ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.14@sha256:c443e20f7cc81154d46bf4b5cba3d3942745b72d4d9a4b1f9936e2e84f3ff329
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
