# aws-lambda-cognito-authorizer

## Synopsis

An AWS Lambda Python program for checking a token for authentication.

## Overview

The instructions show how to generate a package that is loaded onto AWS S3 and used by
[https://github.com/Senzing/aws-cloudformation-ecs-poc-simple](https://github.com/Senzing/aws-cloudformation-ecs-poc-simple)
AWS Cloudformation.

### Contents

1. [Preamble](#preamble)
    1. [Legend](#legend)
1. [Related artifacts](#related-artifacts)
1. [Demonstrate using Command Line Interface](#demonstrate-using-command-line-interface)
    1. [Prerequisites for CLI](#prerequisites-for-cli)
    1. [Download](#download)
    1. [Run command](#run-command)
1. [Demonstrate using Docker](#demonstrate-using-docker)
    1. [Prerequisites for Docker](#prerequisites-for-docker)
    1. [Run Docker container](#run-docker-container)
1. [Develop](#develop)
    1. [Prerequisites for development](#prerequisites-for-development)
    1. [Clone repository](#clone-repository)
    1. [Build Docker image](#build-docker-image)
    1. [Test Docker image](#test-docker-image)
    1. [Make package for S3](#make-package-for-s3)
1. [Advanced](#advanced)
1. [Errors](#errors)
1. [References](#references)

## Preamble

At [Senzing](http://senzing.com),
we strive to create GitHub documentation in a
"[don't make me think](https://github.com/Senzing/knowledge-base/blob/master/WHATIS/dont-make-me-think.md)" style.
For the most part, instructions are copy and paste.
Whenever thinking is needed, it's marked with a "thinking" icon :thinking:.
Whenever customization is needed, it's marked with a "pencil" icon :pencil2:.
If the instructions are not clear, please let us know by opening a new
[Documentation issue](https://github.com/Senzing/template-python/issues/new?template=documentation_request.md)
describing where we can improve.   Now on with the show...

### Legend

1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps there are some choices to be made.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

## Related artifacts

1. [https://github.com/Senzing/aws-cloudformation-ecs-poc-simple](https://github.com/Senzing/aws-cloudformation-ecs-poc-simple) AWS Cloudformation

## Demonstrate using Command Line Interface

### Prerequisites for CLI

:thinking: The following tasks need to be complete before proceeding.
These are "one-time tasks" which may already have been completed.

1. Install Python dependencies:
    1. See [requirements.txt](requirements.txt) for list
        1. [Installation hints](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-python-dependencies.md)

### Download

1. Get a local copy of
   [cognito_authorizer.py](cognito_authorizer.py).
   Example:

    1. :pencil2: Specify where to download file.
       Example:

        ```console
        export SENZING_DOWNLOAD_FILE=~/cognito_authorizer.py
        ```

    1. Download file.
       Example:

        ```console
        curl -X GET \
          --output ${SENZING_DOWNLOAD_FILE} \
          https://raw.githubusercontent.com/Senzing/aws-lambda-cognito-authorizer/master/cognito_authorizer.py
        ```

    1. Make file executable.
       Example:

        ```console
        chmod +x ${SENZING_DOWNLOAD_FILE}
        ```

1. :thinking: **Alternative:** The entire git repository can be downloaded by following instructions at
   [Clone repository](#clone-repository)

### Run command

1. Run the command.
   Example:

   ```console
   ${SENZING_DOWNLOAD_FILE}
   ```

## Demonstrate using Docker

### Prerequisites for Docker

:thinking: The following tasks need to be complete before proceeding.
These are "one-time tasks" which may already have been completed.

1. The following software programs need to be installed:
    1. [docker](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-docker.md)

### Run Docker container

1. Run Docker container.
   Example:

    ```console
    docker run \
      --interactive \
      --rm \
      --tty \
      senzing/cognito-authorizer
    ```

    Note:  Because this is built to run in an AWS Lambda environment,
    errors will be seen when running outside of that environment.

## Develop

The following instructions are used when modifying and building the Docker image.

### Prerequisites for development

:thinking: The following tasks need to be complete before proceeding.
These are "one-time tasks" which may already have been completed.

1. The following software programs need to be installed:
    1. [git](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-git.md)
    1. [make](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-make.md)
    1. [docker](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-docker.md)

### Clone repository

For more information on environment variables,
see [Environment Variables](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md).

1. Set these environment variable values:

    ```console
    export GIT_ACCOUNT=senzing
    export GIT_REPOSITORY=aws-lambda-cognito-authorizer
    export GIT_ACCOUNT_DIR=~/${GIT_ACCOUNT}.git
    export GIT_REPOSITORY_DIR="${GIT_ACCOUNT_DIR}/${GIT_REPOSITORY}"
    ```

1. Using the environment variables values just set, follow steps in [clone-repository](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/clone-repository.md) to install the Git repository.

### Build Docker image

Since the Docker image is based on `public.ecr.aws/lambda/python:3.8`,
logging into AWS Elastic Container Registry (ECR) is required.

1. Set AWS environment variables.
   Example:

    ```console
    export AWS_ACCESS_KEY_ID=$(jq --raw-output ".Credentials.AccessKeyId" ~/aws-sts-get-session-token.json)
    export AWS_SECRET_ACCESS_KEY=$(jq --raw-output ".Credentials.SecretAccessKey" ~/aws-sts-get-session-token.json)
    export AWS_SESSION_TOKEN=$(jq --raw-output ".Credentials.SessionToken" ~/aws-sts-get-session-token.json)
    export AWS_DEFAULT_REGION=$(aws configure get default.region)
    ```

1. Login
   Example:

    ```console
    aws ecr-public get-login-password \
      --region us-east-1 \
    | docker login \
      --username AWS \
      --password-stdin public.ecr.aws/senzing
    ```

1. **Option #1:** Using `docker` command and GitHub.

    ```console
    sudo docker build \
      --tag senzing/template \
      https://github.com/senzing/aws-lambda-cognito-authorizer.git
    ```

1. **Option #2:** Using `docker` command and local repository.

    ```console
    cd ${GIT_REPOSITORY_DIR}
    sudo docker build --tag senzing/cognito-authorizer .
    ```

1. **Option #3:** Using `make` command.

    ```console
    cd ${GIT_REPOSITORY_DIR}
    sudo make docker-build
    ```

    Note: `sudo make docker-build-development-cache` can be used to create cached Docker layers.

### Test Docker image

1. Download the
   [AWS Lambda Runtime Interface Emulator](https://github.com/aws/aws-lambda-runtime-interface-emulator)
   and make executable.
   Example:

    ```console
    mkdir -p ~/aws-lambda-rie
    curl -Lo ~/aws-lambda-rie/aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie
    chmod +x ~/aws-lambda-rie/aws-lambda-rie
    ```

1. Set the required environment variables

    ```console
    export USERPOOL_ID=<insert user pool id>
    export APP_CLIENT_ID=<insert app client id>
    export AWS_REGION=<insert aws region e.g. us-east-1>
    ```

1. Run docker container to start a service.
   Example:

    ```console
    docker run \
      --entrypoint /aws-lambda/aws-lambda-rie \
      --interactive \
      --publish 9001:8080 \
      --rm \
      --tty \
      --env USERPOOL_ID=${USERPOOL_ID} \
      --env APP_CLIENT_ID=${APP_CLIENT_ID} \
      --env AWS_REGION=${AWS_REGION} \
      --volume ~/aws-lambda-rie:/aws-lambda \
      senzing/cognito-authorizer \
        /var/lang/bin/python -m awslambdaric cognito_authorizer.handler
    ```

1. In a separate terminal window, call the lambda.
   Example:

    ```console
    curl -v -X POST \
      http://localhost:9001/2015-03-31/functions/function/invocations \
      --data-binary @- << EOF
        {
          "RequestType": "Create",
          "ResponseURL": "",
          "StackId": "",
          "RequestId": "",
          "LogicalResourceId": ""
        }
    EOF
    ```

### Make package for S3

Make sure that the `python3 --version` used to run the `pip3 install` command is the same
as the python version seen in the AWS Lambda definition (i.e. the `Runtime:` parameter).
If not the python packages may not be the correct version.

1. Install dependencies.
   Example:

    ```console
    cd ${GIT_REPOSITORY_DIR}
    pip3 install \
        --requirement requirements.txt \
        --target ./package
    ```

1. Compress dependencies.
   Example:

    ```console
    cd ${GIT_REPOSITORY_DIR}/package
    zip -r ../cognito-authorizer.zip .
    ```

1. Add `cognito_authorizer.py` to compressed file.
   Example:

    ```console
    cd ${GIT_REPOSITORY_DIR}
    zip -g cognito-authorizer.zip cognito_authorizer.py
    ```

1. Upload `cognito-authorizer.zip` to AWS S3 in multiple AWS regions.

## Advanced

## Errors

1. See [docs/errors.md](docs/errors.md).

## References

1. [PyPi - awslambdaric](https://pypi.org/project/awslambdaric/)
1. [Creating a function with runtime dependencies](https://docs.aws.amazon.com/lambda/latest/dg/python-package-create.html#python-package-create-with-dependency)

