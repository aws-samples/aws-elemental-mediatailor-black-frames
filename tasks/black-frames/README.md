# AWS Elemental MediaTailor - Black Frames - ECS Task

This task makes use of FFmpeg to detect black segments of a media file hosted on S3 and writes info to a DynamoDB table.

## Input

| Env Var     | Description                 | Example                    |
| ----------- | --------------------------- | -------------------------- |
| INPUT_MEDIA_ID | (string, UUID) unique id of the media file to be analysed  | `ba79f3c4-15da-11ea-8d71-362b9e155667` |
| INPUT_MEDIA_BUCKET | (string) input media file bucket | `my-input-bucket` |
| INPUT_MEDIA_KEY | (string) input media file key | `path/to/file.mp4` |
| OUTPUT_MEDIA_BUCKET | (string) output media file bucket | `my-output-bucket` |
| METADATA_TABLE| (string) DynamoDB table that stores metadata|  `MyTableName`|
| FFMPEG_BLACK_DURATION | (float, defaults to 0.5) the minimum duration in seconds for a clip to be considered a break | `2.5` |
| FFMPEG_BLACK_THRESHOLD| (float, [0, 1], defaults to 0.00) the level of brightnes below which a pixel is considered black | `0.05` |

## Process

Once fired up, the task will

1. gather input from environment
2. download the media asset from S3 to the local filesystem
3. execute `ffmpeg` to find long segments of black frames via `blackdetect`
4. build the VMAP file from the output of `ffmpeg`
5. upload the VMAP file to S3, set its ACL to public
6. update the metadata table

## Output

This task causes the following side-effects
1. upload of a VMAP file to `OUTPUT_MEDIA_BUCKET`
2. update of the `METADATA_TABLE`

## Build

The container can be built locally by providing the following configuration file
`deploy.env`
```
APP_NAME=<application-name-here>
DOCKER_REPO=<aws-account-number>.dkr.ecr.<aws-region>.amazonaws.com
DEPLOY_ENVIRONMENT=dev
AWS_CLI_REGION=<aws-region>
```
To build the container run
```bash
make build
```

More build options can be found by running
```
make help
```

## Run

The container can be run locally by providing the following configuration file
`config.env`
```
INPUT_MEDIA_BUCKET=<s3-input-bucket-name>
INPUT_MEDIA_KEY=<mp4-file-name>
INPUT_MEDIA_ID=<uuid>
OUTPUT_MEDIA_BUCKET=<s3-output-bucket-name>
METADATA_TABLE=<dynamodb-table-name>
FFMPEG_BLACK_DURATION=0.5
FFMPEG_BLACK_THRESHOLD=0.0
AWS_DEFAULT_REGION=<aws-region>
```

There are various options to run the container.

- `make run` to run the container with the default configuration file
- `make cnf="config_special.env" run` to use a special configuration file
- `make run-i` to run the container interactively
- `make run-c9` to run the container on a Cloud9 environment
- `make run-c9-i` to run the container on a Cloud9 environment interactively

## Release

The container can be released to an ECR repository by providing the following configuration file
`deploy.env`
```
APP_NAME=<application-name-here>
DOCKER_REPO=<aws-account-number>.dkr.ecr.<aws-region>.amazonaws.com # don't use the full url
DEPLOY_ENVIRONMENT=dev
AWS_CLI_REGION=<aws-region>
```
and run
```bash
make release
```
