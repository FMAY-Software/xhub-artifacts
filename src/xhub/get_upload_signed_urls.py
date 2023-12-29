import boto3
import json
import os

s3 = boto3.client("s3")


def handler(event, context):
    # Retrieve the bucket name from the environment variable
    # bucket_name = os.environ.get("ARTIFACTS_BUCKET")
    bucket_name = "xtuml-hub-artifacts"

    if not bucket_name:
        print("Environment variable ARTIFACTS_BUCKET not set.")
        return {"statusCode": 500, "body": "Bucket name not configured."}

    try:
        # Retrieve file keys from the request
        file_keys = event.get("multiValueQueryStringParameters", {}).get(
            "file_keys", []
        )

        if not file_keys:
            return {
                "statusCode": 400,
                "body": "Missing 'file_keys' parameter in the request.",
            }

        # Generate signed URLs for each file
        signed_urls = {}
        for file_key in file_keys:
            # Generate a presigned URL for the file
            url = s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": bucket_name, "Key": file_key},
                ExpiresIn=3600,  # URL expiration time in seconds (adjust as needed)
            )
            signed_urls[file_key] = url

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"signed_urls": signed_urls}),
        }
    except Exception as e:
        print(f"Error generating signed URLs: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
