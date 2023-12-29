import json
import os
import uuid
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
        # Parse the JSON body from the request
        request_body = json.loads(event.get("body", "{}"))

        # Retrieve the array of artifacts from the parsed body
        artifacts = request_body.get("artifacts", [])

        if not artifacts:
            return {
                "statusCode": 400,
                "body": "Missing 'artifacts' parameter in the request body.",
            }

        # Dictionary to store generated artifact IDs mapped by name
        artifact_ids_by_name = {}

        # Iterate through each artifact and check if it exists in DynamoDB
        for artifact in artifacts:
            artifact_id = artifact.get("artifactId")
            artifact_name = artifact.get("name")
            artifact_owner = artifact.get("owner")
            artifact_description = artifact.get("description")
            artifact_types = artifact.get("types", [])
            artifact_files = artifact.get("files", [])
            artifact_dependencies = artifact.get("dependencies")
            artifact_usage = artifact.get("usage")
            artifact_last_modified = artifact.get("last_modified")

            if not artifact_id or not artifact_files:
                return {
                    "statusCode": 400,
                    "body": "Missing required parameters in the artifact.",
                }

            # Check if the artifact with the given artifactId already exists in DynamoDB
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression="artifactId = :artifactId",
                ExpressionAttributeValues={":artifactId": {"S": artifact_id}},
            )

            # If the artifact exists, update its attributes
            if response.get("Items"):
                # Update the artifact in DynamoDB
                dynamodb.update_item(
                    TableName=table_name,
                    Key={
                        "artifactId": {"S": artifact_id},
                        "name": {"S": artifact_name},
                    },
                    UpdateExpression=(
                        "SET #owner = :owner, #description = :description, "
                        "#types = :types, #files = :files, "
                        "#dependencies = :dependencies, #usage = :usage, "
                        "#last_modified = :last_modified"
                    ),
                    ExpressionAttributeValues={
                        ":owner": {"S": artifact_owner},
                        ":description": {"S": artifact_description},
                        ":types": {"SS": artifact_types},
                        ":files": {
                            "L": [
                                {
                                    "M": {
                                        "name": {"S": file["name"]},
                                        "size": {"N": str(file["size"])},
                                        "type": {"S": file["type"]},
                                        "url": {"S": file["url"]},
                                    }
                                }
                                for file in artifact_files
                            ]
                        },
                        ":dependencies": {"S": artifact_dependencies},
                        ":usage": {"S": artifact_usage},
                        ":last_modified": {"S": artifact_last_modified},
                    },
                    ExpressionAttributeNames={
                        "#owner": "owner",
                        "#description": "description",
                        "#types": "types",
                        "#files": "files",
                        "#dependencies": "dependencies",
                        "#usage": "usage",
                        "#last_modified": "last_modified",
                    },
                )
                artifact_ids_by_name[artifact_id] = artifact_id
            else:
                # If the artifact does not exist, return an error
                return {
                    "statusCode": 404,
                    "body": f"Artifact with artifactId {artifact_id} not found.",
                }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps(artifact_ids_by_name),
        }
    except Exception as e:
        print(f"Error updating artifacts in DynamoDB: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
