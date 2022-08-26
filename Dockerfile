ARG BASE_IMAGE=public.ecr.aws/lambda/python:3.8@sha256:20f33cfb14df6d6af0564ba53335d1048682aaf410c881ddc6fb13ceb2e74a8e
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2022-08-25

LABEL Name="senzing/cognito-authorizer" \
      Maintainer="support@senzing.com" \
      Version="1.0.0"

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
