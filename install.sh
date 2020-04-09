#!/usr/bin/env bash

# Import configuration
. ./.env

# Build the fanout lambda
cd functions/fanout-lambda
make build
cd ..

# Build the media-lambda
cd media-lambda
make build
cd ../..

cd cloudformation

aws cloudformation package \
    --template-file ./fanout-lambda.yml \
    --s3-bucket $CFN_BUCKET \
    --output-template-file ./fanout-lambda.pkg.yml
aws cloudformation package \
    --template-file ./media-lambda.yml \
    --s3-bucket $CFN_BUCKET \
    --output-template-file ./media-lambda.pkg.yml
aws cloudformation package \
    --template-file ./main.yml \
    --s3-bucket $CFN_BUCKET \
    --output-template-file ./main.pkg.yml

aws cloudformation deploy \
    --template-file ./main.pkg.yml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM

cd ..

aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query Stacks[0].Outputs > stack-outputs.ignore.json

python <<HEREDOC
import json
import os

with open('stack-outputs.ignore.json') as fp:
    outputs = json.load(fp)

def get_output(OutputKey, outputs):
    return list(filter(lambda x: x['OutputKey'] == OutputKey, outputs))[0]

ecr_info = get_output('FargateTasksBlackFramesDockerRepository', outputs)
repo, app = ecr_info['OutputValue'].split("/")
app, version = app.split(":")
environment_info = get_output('StackEnvironment', outputs)['OutputValue']
region = os.environ.get("AWS_DEFAULT_REGION")

print("ecr repository: ", repo)
print("application name: ", app)
print("application version: ", version)
print("deployment region: ", region)
print("deployment environment: ", environment_info)

with open('deploy.auto.env', 'w') as fp:
    fp.write('APP_NAME=' + app + '\n')
    fp.write('DOCKER_REPO=' + repo + '\n')
    fp.write('DEPLOY_ENVIRONMENT=' + environment_info + '\n')
    fp.write('AWS_CLI_REGION=' + region + '\n')

HEREDOC

mv deploy.auto.env tasks/black-frames/deploy.auto.env

cd tasks/black-frames
make dpl="deploy.auto.env" release
cd ../..
