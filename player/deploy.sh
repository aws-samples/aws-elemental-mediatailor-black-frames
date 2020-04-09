#!/usr/bin/env bash

# Import configuration
. ./.env

rm index.html
cp index.template.html index.html

STREAM_URL=${STREAM_URL//\//\\\/}

sed -i "s/{PAGE_TITLE}/$PAGE_TITLE/g" index.html
sed -i "s/{STREAM_URL}/$STREAM_URL/g" index.html
sed -i "s/{ADS_TS}/$ADS_TS/g" index.html

aws s3 mb s3://$DEPLOY_BUCKET
aws s3 website s3://$DEPLOY_BUCKET --index-document index.html --error-document index.html
aws s3 cp index.html s3://$DEPLOY_BUCKET --acl public-read

echo "website endpoint:  http://$DEPLOY_BUCKET.s3-website-$AWS_DEFAULT_REGION.amazonaws.com"

rm index.html