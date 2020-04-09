import os
import subprocess

import boto3
from botocore.exceptions import ClientError
from utils import build_manifest

# 1. get input from environment

try:
    INPUT_MEDIA_BUCKET = os.environ["INPUT_MEDIA_BUCKET"]
    INPUT_MEDIA_KEY = os.environ["INPUT_MEDIA_KEY"]
    INPUT_MEDIA_ID = os.environ["INPUT_MEDIA_ID"]
    OUTPUT_MEDIA_BUCKET = os.environ["OUTPUT_MEDIA_BUCKET"]
    METADATA_TABLE = os.environ["METADATA_TABLE"]
    REGION = os.environ["AWS_DEFAULT_REGION"]
except KeyError as e:
    print(f"Missing env variable: {e}")
    exit(1)

FFMPEG_BLACK_DURATION = os.environ.get("FFMPEG_BLACK_DURATION", 0.5)
FFMPEG_BLACK_THRESHOLD = os.environ.get("FFMPEG_BLACK_THRESHOLD", 0.0)
ENVIRONMENT_SUFFIX = os.environ.get("ENVIRONMENT_SUFFIX", "dev")

TASK_FILE_NAME = "input.mp4"
TASK_OUTPUT_NAME = "output.xml"


s3 = boto3.client("s3")
dynamo = boto3.resource("dynamodb")
metadata_table = dynamo.Table(METADATA_TABLE)

# 2. download the media file to the local filesystem

with open(TASK_FILE_NAME, "wb") as fp:
    s3.download_fileobj(INPUT_MEDIA_BUCKET, INPUT_MEDIA_KEY, fp)

FFMPEG_COMMAND = [
    "ffmpeg",
    "-i",
    TASK_FILE_NAME,
    "-vf",
    f"blackdetect=d={FFMPEG_BLACK_DURATION}:pix_th={FFMPEG_BLACK_THRESHOLD}",
    "-an",
    "-f",
    "null",
    "-",
]

# 3. runs ffmpeg

p = subprocess.Popen(FFMPEG_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

out, err = p.communicate()

# 4. builds the VMAP file from the output of FFMPEG
# using err instead of out because ffmpeg spits output on err instead of std
manifest = build_manifest(err.split("\n"))
print(manifest)

with open(TASK_OUTPUT_NAME, "w") as fp:
    fp.write(manifest)

output_key = f"{INPUT_MEDIA_KEY}/ads/black/{INPUT_MEDIA_ID}.vmap.xml"

# 5. uploads the VMAP file to S3, sets its ACL to public

try:
    response = s3.upload_file(
        TASK_OUTPUT_NAME,
        OUTPUT_MEDIA_BUCKET,
        output_key,
        ExtraArgs={"ACL": "public-read"},
    )
except ClientError as e:
    print(e)
    exit(1)

VMAPUrl = f"https://{OUTPUT_MEDIA_BUCKET}.s3-{REGION}.amazonaws.com/{output_key}"

print("**********VMAPUrl**********")
print(VMAPUrl)

# 6. updates the metadata table

try:
    dynamo_response = metadata_table.update_item(
        Key={"MediaId": INPUT_MEDIA_ID},
        AttributeUpdates={"VMAPUrl-black": {"Value": VMAPUrl}},
    )
except ClientError as e:
    print(e)
    exit(1)
