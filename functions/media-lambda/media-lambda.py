import json
import os
import urllib.parse as urllib
from datetime import datetime
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

METADATA_TABLE = os.environ.get("METADATA_TABLE") or "gbatt-automads-metadata-manual"

dynamo = boto3.resource("dynamodb")
mediatailor = boto3.client("mediatailor")
metadata_table = dynamo.Table(METADATA_TABLE)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return o.to_eng_string()

        return json.JSONEncoder.default(self, o)


def lambda_handler(event, context):

    # expected $ORIGINAL_KEY/ads/$TYPE/$UUID.vmap.xml
    KEY = urllib.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    # expected [$ORIGINAL_KEY, $TYPE/$UUID.vmap.xml]
    MEDIA_BUCKET, FILENAME = KEY.split("/ads/")
    TYPE, UUID = FILENAME.split("/")
    UUID = UUID.replace(".vmap.xml", "")

    print("**********DYNAMO REQUEST**********")
    try:
        item = metadata_table.get_item(Key={"MediaId": UUID})["Item"]
    except ClientError as e:
        print(e)
        return {
            "statusCode": 500,
            "body": f"possible problem with UUID {UUID}: {str(e)}",
        }

    print("**********DYNAMO RESPONSE**********")
    print(json.dumps(item, indent=2, cls=DateTimeEncoder))

    print("**********MEDIATAILOR REQUEST**********")
    try:
        mediatailor_response = mediatailor.put_playback_configuration(
            AdDecisionServerUrl=item[f"VMAPUrl-{TYPE}"],
            Name=f"{TYPE}-{UUID}",
            Tags={"OriginTable": METADATA_TABLE, "MediaId": UUID},
            VideoContentSourceUrl=item["PlaylistUrl"].replace("/playlist.m3u8", ""),
        )
    except ClientError as e:
        print(e)
        return {
            "statusCode": 500,
            "body": f"possible problem with UUID {UUID} and ads manifest type {TYPE}: {str(e)}",
        }
    except KeyError as e:
        print(e)
        return {
            "statusCode": 500,
            "body": f"ads manifest type {TYPE} not found for media {UUID}: {str(e)}",
        }

    print("**********MEDIATAILOR RESPONSE**********")
    print(json.dumps(mediatailor_response, indent=2, cls=DateTimeEncoder))

    print("**********DYNAMO UPDATE**********")
    try:
        update_response = metadata_table.update_item(
            Key={"MediaId": UUID},
            AttributeUpdates={
                f"StreamUrl-{TYPE}": {
                    "Value": mediatailor_response["HlsConfiguration"][
                        "ManifestEndpointPrefix"
                    ]
                }
            },
        )
    except ClientError as e:
        print(e)
        exit(255)

    print("**********DYNAMO RESPONSE**********")
    print(json.dumps(update_response, indent=2, cls=DateTimeEncoder))

    return {"statusCode": 200, "body": "OK"}
