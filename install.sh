#!/usr/bin/env bash

# Import configuration
. ./.env

MEDIA_CONVERT_ENDPOINT=$(aws mediaconvert describe-endpoints --query Endpoints[0].Url | xargs)

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
    --parameter-overrides \
    MediaConvertEndpoint=$MEDIA_CONVERT_ENDPOINT \
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
region = get_output('DeploymentRegion', outputs)['OutputValue']

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
source tasks/black-frames/deploy.auto.env

# activating ECR scan on push
aws ecr put-image-scanning-configuration \
    --repository-name $APP_NAME \
    --image-scanning-configuration scanOnPush=true \
    --region $AWS_CLI_REGION

cd tasks/black-frames

stat config.env
IS_CONFIG=$?

[[ $IS_CONFIG == "1" ]] && touch config.env

echo "building the contianer"
echo "this will take around 10 mins"
make dpl="deploy.auto.env" build-nc

echo "testing black frames detection works ok"
make dpl="deploy.auto.env" test-ffmpeg-black-frames

echo "The container built at the previous step makes use of FFmpeg with the following License"
make dpl="deploy.auto.env" test-ffmpeg-license

echo "By deploying and using this container, you agree to the terms and conditions stated in the license agreement above."
echo "More information about FFmpeg in README.md"
read -p "Do you wish to continue? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1

echo "Ok, deploying to ECR $DOCKER_REPO"
make dpl="deploy.auto.env" publish
cd ../..
