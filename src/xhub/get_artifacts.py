import json
import os
import boto3

dynamodb = boto3.client("dynamodb")


def handler(event, context):
    # Retrieve the table name from the environment variable
    # table_name = os.environ.get("ARTIFACTS_TABLE")
    table_name = "xhub-artifacts"

    if not table_name:
        print("Environment variable ARTIFACTS_TABLE not set.")
        return {"statusCode": 500, "body": "Table name not configured."}

    try:
        # Query all artifacts from DynamoDB
        response = dynamodb.scan(
            TableName=table_name,
        )

        # Extract the items from the DynamoDB response
        artifacts = response.get("Items", [])

        # Convert DynamoDB items to a more readable format
        formatted_artifacts = [
            {
                "artifactId": artifact["artifactId"]["S"],
                "owner": artifact.get("owner", {}).get("S", ""),
                "name": artifact.get("name", {}).get("S", ""),
                "description": artifact.get("description", {}).get("S", ""),
                "types": artifact.get("types", {}).get("SS", []),
                "files": [
                    {
                        "name": file["M"].get("name", {}).get("S", ""),
                        "size": int(file["M"].get("size", {}).get("N", 0)),
                        "type": file["M"].get("type", {}).get("S", ""),
                        "url": file["M"].get("url", {}).get("S", ""),
                    }
                    for file in artifact.get("files", {}).get("L", [])
                ],
                "dependencies": artifact.get("dependencies", {}).get("S", ""),
                "usage": artifact.get("usage", {}).get("S", ""),
                "last_modified": artifact.get("last_modified", {}).get("S", ""),
                # Add other attributes as needed
            }
            for artifact in artifacts
        ]

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"artifacts": formatted_artifacts}),
        }

    except Exception as e:
        print(f"Error retrieving artifacts from DynamoDB: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
