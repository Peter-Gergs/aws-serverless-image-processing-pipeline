import json
import os
import uuid
import boto3
import urllib.parse
from datetime import datetime, timezone
from PIL import Image, ImageDraw

s3 = boto3.client("s3")
sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

DESTINATION_BUCKET = os.environ["DESTINATION_BUCKET"]
METADATA_TABLE = os.environ["METADATA_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

table = dynamodb.Table(METADATA_TABLE)


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    for record in event["Records"]:
        sqs_body = json.loads(record["body"])

        for s3_record in sqs_body["Records"]:
            source_bucket = s3_record["s3"]["bucket"]["name"]
            object_key = urllib.parse.unquote_plus(
                s3_record["s3"]["object"]["key"]
            )

            input_path = "/tmp/input_image"
            output_path = "/tmp/output_image.jpg"

            s3.download_file(source_bucket, object_key, input_path)

            with Image.open(input_path) as image:
                image = image.convert("RGB")

                original_width = image.width
                original_height = image.height

                image.thumbnail((1200, 1200))

                draw = ImageDraw.Draw(image)
                watermark = "Manara AWS Project"

                x = 20
                y = max(20, image.height - 50)

                bbox = draw.textbbox((x, y), watermark)

                draw.rectangle(
                    (
                        bbox[0] - 10,
                        bbox[1] - 5,
                        bbox[2] + 10,
                        bbox[3] + 5
                    ),
                    fill="black"
                )

                draw.text((x, y), watermark, fill="white")

                image.save(output_path, "JPEG", quality=85)

                processed_width = image.width
                processed_height = image.height

            filename = os.path.basename(object_key)
            filename_without_extension = os.path.splitext(filename)[0]

            destination_key = (
                f"processed/{filename_without_extension}-processed.jpg"
            )

            s3.upload_file(
                output_path,
                DESTINATION_BUCKET,
                destination_key,
                ExtraArgs={"ContentType": "image/jpeg"}
            )

            image_id = str(uuid.uuid4())

            table.put_item(
                Item={
                    "image_id": image_id,
                    "original_key": object_key,
                    "processed_key": destination_key,
                    "source_bucket": source_bucket,
                    "destination_bucket": DESTINATION_BUCKET,
                    "original_width": original_width,
                    "original_height": original_height,
                    "processed_width": processed_width,
                    "processed_height": processed_height,
                    "status": "COMPLETED",
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }
            )

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="Image Processing Completed",
                Message=(
                    f"Image processed successfully.\n\n"
                    f"Original: {object_key}\n"
                    f"Processed: {destination_key}\n"
                    f"Original size: {original_width}x{original_height}\n"
                    f"Processed size: {processed_width}x{processed_height}"
                )
            )

    return {
        "statusCode": 200,
        "body": "Image processed successfully"
    }