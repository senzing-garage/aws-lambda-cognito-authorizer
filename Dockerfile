ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.8@sha256:209f374bb976d9d340937785ebae761a2446d19c342246fcf4522316060dec9a
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2023-06-29

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
