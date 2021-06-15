#! /usr/bin/env python3

# -----------------------------------------------------------------------------
# cognito_authorizer.py for authorizing network traffic.
# -----------------------------------------------------------------------------

from OpenSSL import crypto
import datetime
from json import JSONEncoder
import json
import logging
import os
import random
import sys
import time
import traceback

import cfnresponse

__all__ = []
__version__ = "1.0.0"  # See https://www.python.org/dev/peps/pep-0396/
__date__ = '2021-06-15'
__updated__ = '2021-06-15'

SENZING_PRODUCT_ID = "5022"  # See https://github.com/Senzing/knowledge-base/blob/master/lists/senzing-product-ids.md

ONE_YEAR_IN_SECONDS = 365 * 24 * 60 * 60
NINE_YEARS_IN_SECONDS = 9 * ONE_YEAR_IN_SECONDS
TEN_YEARS_IN_SECONDS = 10 * ONE_YEAR_IN_SECONDS

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

# Configure logging. See https://docs.python.org/2/library/logging.html#levels

log_level_map = {
    "notset": logging.NOTSET,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "fatal": logging.FATAL,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

log_format = '%(asctime)s %(message)s'
log_level_parameter = os.getenv("SENZING_LOG_LEVEL", "info").lower()
log_level = log_level_map.get(log_level_parameter, logging.INFO)
logging.basicConfig(format=log_format, level=log_level)

# -----------------------------------------------------------------------------
# Message handling
# -----------------------------------------------------------------------------

# 1xx Informational (i.e. logging.info())
# 3xx Warning (i.e. logging.warning())
# 5xx User configuration issues (either logging.warning() or logging.err() for Client errors)
# 7xx Internal error (i.e. logging.error for Server errors)
# 9xx Debugging (i.e. logging.debug())

MESSAGE_INFO = 100
MESSAGE_WARN = 300
MESSAGE_ERROR = 700
MESSAGE_DEBUG = 900

message_dictionary = {
    "100": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}I",
    "101": "Event: {0}",
    "102": "Context: {0}",
    "103": "Response: {0}",
    "300": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}W",
    "700": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}E",
    "900": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}D",
    "997": "Exception: {0}",
    "998": "Debugging enabled.",
    "999": "{0}",
}


def message(index, *args):
    index_string = str(index)
    template = message_dictionary.get(index_string, "No message for index {0}.".format(index_string))
    return template.format(*args)


def message_generic(generic_index, index, *args):
    index_string = str(index)
    return "{0} {1}".format(message(generic_index, index), message(index, *args))


def message_info(index, *args):
    return message_generic(MESSAGE_INFO, index, *args)


def message_warning(index, *args):
    return message_generic(MESSAGE_WARN, index, *args)


def message_error(index, *args):
    return message_generic(MESSAGE_ERROR, index, *args)


def message_debug(index, *args):
    return message_generic(MESSAGE_DEBUG, index, *args)


def get_exception():
    ''' Get details about an exception. '''
    exception_type, exception_object, traceback = sys.exc_info()
    frame = traceback.tb_frame
    line_number = traceback.tb_lineno
    filename = frame.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, line_number, frame.f_globals)
    return {
        "filename": filename,
        "line_number": line_number,
        "line": line.strip(),
        "exception": exception_object,
        "type": exception_type,
        "traceback": traceback,
    }

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def get_new_key(key_size=1024):
    """ Create an "empty" key of requested length. """

    result = crypto.PKey()
    result.generate_key(crypto.TYPE_RSA, key_size)
    return result


def get_certificate_authority_certificate(public_key, subject_dict):
    """ Create a self-signed Certificate Authority (CA) certificate. """

    # Create certificate.

    result = crypto.X509()
    result.set_version(2)
    result.set_serial_number(random.randrange(100000))

    # Set subject.

    subject = result.get_subject()
    subject.C = subject_dict.get('C')
    subject.CN = subject_dict.get('CNca')
    subject.L = subject_dict.get('L')
    subject.O = subject_dict.get('O')
    subject.OU = subject_dict.get('OU')
    subject.ST = subject_dict.get('ST')

    # Add extensions.

    result.add_extensions([
        crypto.X509Extension(
            b"subjectKeyIdentifier",
            False,
            b"hash",
            subject=result),
    ])
    result.add_extensions([
        crypto.X509Extension(
            b"authorityKeyIdentifier",
            False,
            b"keyid:always",
            issuer=result),
    ])
    result.add_extensions([
        crypto.X509Extension(
            b"basicConstraints",
            False,
            b"CA:TRUE"),
        crypto.X509Extension(
            b"keyUsage",
            False,
            b"keyCertSign, cRLSign"),
    ])

    # Set expiry.

    result.gmtime_adj_notBefore(0)
    result.gmtime_adj_notAfter(TEN_YEARS_IN_SECONDS)

    # Sign and seal.

    result.set_pubkey(public_key)
    result.set_issuer(subject)
    result.sign(public_key, 'sha256')

    return result


def get_certificate(public_key, ca_key, certificate_authority_certificate, subject_dict):
    """ Create a self-signed X.509 certificate. """

    # Create certificate.

    result = crypto.X509()
    result.set_version(2)
    result.set_serial_number(random.randrange(100000))

    # Set subject.

    subject = result.get_subject()
    subject.C = subject_dict.get('C')
    subject.CN = subject_dict.get('CN')
    subject.L = subject_dict.get('L')
    subject.O = subject_dict.get('O')
    subject.OU = subject_dict.get('OU')
    subject.ST = subject_dict.get('ST')

    # Add extensions.

    result.add_extensions([
        crypto.X509Extension(
            b"basicConstraints",
            False,
            b"CA:FALSE"),
        crypto.X509Extension(
            b"subjectKeyIdentifier",
            False,
            b"hash",
            subject=result),
    ])
    result.add_extensions([
        crypto.X509Extension(
            b"authorityKeyIdentifier",
            False,
            b"keyid:always",
            issuer=certificate_authority_certificate),
        crypto.X509Extension(
            b"extendedKeyUsage",
            False,
            b"serverAuth"),
        crypto.X509Extension(
            b"keyUsage",
            False,
            b"digitalSignature"),
    ])
    result.add_extensions([
        crypto.X509Extension(
            b'subjectAltName',
            False,
            ','.join([
                'DNS:*.example.com'
                ]).encode())
    ])

    # Set expiry.

    result.gmtime_adj_notBefore(0)
    result.gmtime_adj_notAfter(NINE_YEARS_IN_SECONDS)

    # Sign and seal.

    result.set_pubkey(public_key)
    result.set_issuer(certificate_authority_certificate.get_subject())
    result.sign(ca_key, 'sha256')

    return result

# -----------------------------------------------------------------------------
# Lambda handler
# -----------------------------------------------------------------------------


def handler(event, context):
    """ Function to be called by AWS lambda. """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    result = cfnresponse.SUCCESS
    response = {}

    try:
        logger.info(message_info(101, json.dumps(event)))

        if event.get('RequestType') in ['Create', 'Update']:

            # Get input parameters.

            properties = event.get('ResourceProperties', {})
            certificate_authority_key_size = int(properties.get('CertificateAuthorityKeySize', 1024))
            certificate_key_size = int(properties.get('CertificateKeySize', 1024))

            # Mock up a subject, using input parameters if supplied.

            subject = {
                "C": properties.get('SubjectCountryName', 'US'),
                "CN": properties.get('SubjectCommonName', 'CommonName'),
                "CNca": properties.get('SubjectCommonNameCA', 'Self CA'),
                "L": properties.get('SubjectLocality', 'City'),
                "O": properties.get('SubjectOrganization', 'Organization'),
                "OU": properties.get('SubjectOrganizationalUnit', 'OrganizationalUnit'),
                "ST": properties.get('SubjectState', 'State'),
            }

            # Create mock Certificate Authority certificate.

            certificate_authority_certificate_key = get_new_key(certificate_authority_key_size)
            certificate_authority_certificate = get_certificate_authority_certificate(certificate_authority_certificate_key, subject)

            # Create mock X.509 certificate.

            certificate_key = get_new_key(certificate_key_size)
            certificate = get_certificate(certificate_key, certificate_authority_certificate_key, certificate_authority_certificate, subject)

            # Craft the response.

            response['CertificateBody'] = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate).decode('utf-8')
            response['PrivateKey'] = crypto.dump_privatekey(crypto.FILETYPE_PEM, certificate_key).decode('utf-8')

        logger.info(message_info(103, json.dumps(response)))

    except Exception as e:
        logger.error(message_error(997, e))
        traceback.print_exc()
        result = cfnresponse.FAILED
    finally:
        cfnresponse.send(event, context, result, response)

    return response

# -----------------------------------------------------------------------------
# Main
#  - Used only in testing.
# -----------------------------------------------------------------------------


if __name__ == "__main__":

    event = {
        "RequestType": "Create",
        "ResponseURL": ""
    }
    context = {}

    # Note: This will error because of cfnresponse.send() not having a context "log_stream_name".

    handler(event, context)
