ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.8@sha256:75048caf626bb81ef6e85bf72c2cde565b61f7095479f633e984107ccf9d595e
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2023-05-09

LABEL Name="senzing/cognito-authorizer" \
      Maintainer="support@senzing.com" \
      Version="0.1.0"

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
