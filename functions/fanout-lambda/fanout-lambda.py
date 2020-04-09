import json
import os
import time
import urllib.parse as urllib
import uuid
from datetime import datetime

import boto3

s3 = boto3.client("s3")
ecs = boto3.client("ecs")
dynamo = boto3.resource("dynamodb")

with open("./jobTemplate.json", "r") as fp:
    job_template = json.load(fp)

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
METADATA_TABLE = os.environ["METADATA_TABLE"]
BLACK_FRAMES_TASK = os.environ["BLACK_FRAMES_TASK"]
SUBNETS = os.environ["SUBNETS"]
MC_JOB_ROLE_ARN = os.environ["MC_JOB_ROLE_ARN"]
MC_QUEUE_JOB_ARN = os.environ["MC_QUEUE_JOB_ARN"]
MC_CUSTOMER_ENDPOINT = os.environ["MC_CUSTOMER_ENDPOINT"]
ECS_FARGATE_CLUSTER = os.environ["ECS_FARGATE_CLUSTER"]
ADS_OUTPUT_BUCKET = os.environ["ADS_OUTPUT_BUCKET"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]

mediaconvert = boto3.client("mediaconvert", endpoint_url=MC_CUSTOMER_ENDPOINT)
metadata_table = dynamo.Table(METADATA_TABLE)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def job_overrides(
    JobTemplate,
    CustomName="",
    Name="",
    OutputsNameModifier="",
    FileInput="",
    Destination="",
    Queue="",
    Role="",
):
    JobTemplate["Queue"] = Queue
    JobTemplate["Settings"]["OutputGroups"][0]["CustomName"] = CustomName
    JobTemplate["Settings"]["OutputGroups"][0]["Name"] = Name
    JobTemplate["Settings"]["OutputGroups"][0]["Outputs"][0][
        "NameModifier"
    ] = OutputsNameModifier
    JobTemplate["Settings"]["OutputGroups"][0]["OutputGroupSettings"][
        "HlsGroupSettings"
    ]["Destination"] = Destination
    JobTemplate["Settings"]["Inputs"][0]["FileInput"] = FileInput
    JobTemplate["Role"] = Role
    JobTemplate["Queue"] = Queue
    return JobTemplate


def loop_breaker(input_bucket, output_bucket):
    if input_bucket == output_bucket:
        raise Exception(
            "Infinite Loop Exception! Input Bucket cannot be the same as Output Bucket"
        )


def lambda_handler(event, context):

    UUID = str(uuid.uuid4())

    print("************UUID************")
    print(UUID)

    # Get the object from the event
    INPUT_BUCKET = event["Records"][0]["s3"]["bucket"]["name"]
    KEY = urllib.unquote_plus(event["Records"][0]["s3"]["object"]["key"])

    # kills the lambda if the input bucket and the output bucket are the same
    loop_breaker(INPUT_BUCKET, OUTPUT_BUCKET)

    job_body = job_overrides(
        job_template,
        CustomName="outputs",
        Name=f"AUTOMADS HLS - {INPUT_BUCKET}/{KEY}",
        OutputsNameModifier="automads-output",
        FileInput=f"s3://{INPUT_BUCKET}/{KEY}",
        Destination=f"s3://{OUTPUT_BUCKET}/{KEY}/playlist",
        Queue=MC_QUEUE_JOB_ARN,
        Role=MC_JOB_ROLE_ARN,
    )

    print("**********MEDIA CONVERT REQUEST**********")
    print(json.dumps(job_body, indent=2))

    response = mediaconvert.create_job(
        Queue=job_body["Queue"],
        AccelerationSettings=job_body["AccelerationSettings"],
        Role=job_body["Role"],
        Settings=job_body["Settings"],
        StatusUpdateInterval=job_body["StatusUpdateInterval"],
        Priority=job_body["Priority"],
    )
    json_mc_response = json.dumps(response, indent=2, cls=DateTimeEncoder)

    print("**********MEDIA CONVERT RESPONSE**********")
    print(json_mc_response)

    print("**********DYNAMO REQUEST**********")
    dynamo_response = metadata_table.put_item(
        Item={
            "MediaId": UUID,
            "IngestionDate": int(time.time()),
            "SourceUrl": f"s3://{INPUT_BUCKET}/{KEY}",
            "PlaylistUrl": f"https://{OUTPUT_BUCKET}.s3-{AWS_DEFAULT_REGION}.amazonaws.com/{KEY}/playlist.m3u8",
        }
    )
    print("**********DYNAMO RESPONSE**********")
    print(json.dumps(dynamo_response, indent=2))

    print("**********ECS REQUEST**********")
    ecs_response = ecs.run_task(
        cluster=ECS_FARGATE_CLUSTER,
        count=1,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS.split(","),
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": "black-frames-detection-container",
                    "environment": [
                        {"name": "INPUT_MEDIA_BUCKET", "value": INPUT_BUCKET},
                        {"name": "INPUT_MEDIA_KEY", "value": KEY},
                        {"name": "INPUT_MEDIA_ID", "value": UUID},
                        {"name": "OUTPUT_MEDIA_BUCKET", "value": ADS_OUTPUT_BUCKET},
                        {"name": "METADATA_TABLE", "value": METADATA_TABLE},
                    ],
                }
            ]
        },
        taskDefinition=BLACK_FRAMES_TASK,
    )

    print("**********ECS RESPONSE**********")
    print(ecs_response)

    return {"statusCode": 200, "body": "OK"}
