import json
import boto3
import uuid

s3 = boto3.client("s3")

BUCKET_NAME = "source-peter-manara-project-2026"


def lambda_handler(event, context):

    try:
        body = {}

        if event.get("body"):
            body = json.loads(event["body"])

        filename = body.get("filename", "upload.jpg")
        content_type = body.get("content_type", "image/jpeg")

        extension = filename.split(".")[-1].lower()

        object_key = f"uploads/{uuid.uuid4()}.{extension}"

        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key,
                "ContentType": content_type
            },
            ExpiresIn=900
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "upload_url": upload_url,
                "object_key": object_key,
                "expires_in": 900
            })
        }

    except Exception as e:

        print(str(e))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }