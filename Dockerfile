ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.8
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2021-03-09

LABEL Name="senzing/cognito-authorizer" \
      Maintainer="support@senzing.com" \
      Version="1.0.0"

HEALTHCHECK CMD ["/app/healthcheck.sh"]

# Run as "root" for system installation.

USER root

# Install packages via PIP.

RUN pip3 install \
      awslambdaric \
      cffi \
      cfnresponse \
      pyOpenSSL

# Copy files from repository.

COPY ./rootfs /
COPY cognito_authorizer.py ./

# Make non-root container.

USER 1001

# Runtime execution.

ENV SENZING_DOCKER_LAUNCHED=true

ENTRYPOINT ["/var/task/cognito_authorizer.py"]
