ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.14@sha256:5ec375e564d79e5d5d18cc8167d9ee9a7a67c931210ed95c508e3be4fcc847ca
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2025-12-22

LABEL Name="senzing/cognito-authorizer" \
  Maintainer="support@senzing.com" \
  Version="0.1.2"

HEALTHCHECK CMD ["/app/healthcheck.sh"]

# Run as "root" for system installation.

USER root

# Install packages via PIP.

COPY requirements.txt ./
RUN pip3 install awslambdaric \
  && pip3 install -r requirements.txt \
  && rm requirements.txt

# Copy files from repository.

COPY ./rootfs /
COPY cognito_authorizer.py ./

# Make non-root container.

USER 1001

# Runtime execution.

ENV SENZING_DOCKER_LAUNCHED=true

ENTRYPOINT ["/var/task/cognito_authorizer.py"]
