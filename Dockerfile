ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.13@sha256:2b00c9883624cadf45e7daf1953a7c4ef8bcd56238847c670d0c2aedd9926f5b
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2024-06-24

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
