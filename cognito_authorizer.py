#! /usr/bin/env python3

# -----------------------------------------------------------------------------------------------
# cognito_authorizer.py, a custom lambda authorizer for authorizing network traffic with cognito.
# -----------------------------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Authorizer Variables
# -----------------------------------------------------------------------------

region = os.environ['AWS_REGION']
userpool_id = os.environ['USERPOOL_ID']
app_client_id = os.environ['APP_CLIENT_ID']
keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpool_id)
# instead of re-downloading the public keys every time
# we download them only on cold start
# https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
with urllib.request.urlopen(keys_url) as f:
    response = f.read()
keys = json.loads(response.decode('utf-8'))['keys']

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

def verify_token(token):
    # get the kid from the headers prior to verification
    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']
    # search for the kid in the downloaded public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        print('Public key not found in jwks.json')
        return False
    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        print('Signature verification failed')
        return False
    print('Signature successfully verified')
    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(token)
    # additionally we can verify the token expiration
    if time.time() > claims['exp']:
        print('Token is expired')
        return False
    # and the Audience  (use claims['client_id'] if verifying an access token)
    if claims['client_id'] != app_client_id:
        print('Token was not issued for this audience')
        return False
    # now we can use the claims
    print(claims)
    return claims

def generateAuthPolicy(principalId, resource, effect):
    authResponse = {}
    authResponse["principalId"] = principalId
    if effect and resource:
        policyDocument = {}
        policyDocument["Version"] = '2012-10-17'
        policyDocument["Statement"] = []
        statementOne = {}
        statementOne["Action"] = 'execute-api:Invoke'
        statementOne["Effect"] = effect
        statementOne["Resource"] = resource
        policyDocument["Statement"].append(statementOne)
        authResponse["policyDocument"] = policyDocument
    return authResponse

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
        lprint("Method ARN: " + event['methodArn'])
        headers = event['headers']
        principalId = "user"
        if verify_token(headers["token"]):
            print("policy is allowed")
            return generateAuthPolicy(principalId, event['methodArn'], "Allow")
        else:
            print("policy is not allowed")
            return "Unauthorized"

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
