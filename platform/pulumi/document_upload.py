import json
import os
import subprocess

import pulumi
import pulumi_aws as aws
from pulumi_aws.cognito import UserPool, UserPoolClient

from pulumi_aws.dynamodb import Table
from pulumi_aws.s3 import Bucket

# Define the path to the Lambda function code and requirements
lambda_code_path = "./document_upload/lambda_function.py"
requirements_path = "./document_upload/requirements.txt"

# Get the current region
current_region = aws.get_region()


def create_document_upload(api, bucket: Bucket, dynamo_db: Table, user_pool_client: UserPoolClient):

    os.makedirs('document_upload/layer', exist_ok=True)
    # Install the dependencies into the layer directory
    subprocess.run([
        "pip", "install",
        "-r", requirements_path,
        "-t", "document_upload/layer/python",
        "--platform", "manylinux2014_x86_64",
        "--upgrade",
        "--only-binary=:all:",
    ]
    )

    # Create a ZIP archive of the layer
    layer_zip = pulumi.asset.AssetArchive({
        ".": pulumi.asset.FileArchive('document_upload/layer')
    }
    )

    # Create an IAM role for the Lambda function
    lambda_role = aws.iam.Role("documentUploadLambdaRole",
        assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
        }"""
    )

    # Attach basic execution role policy to the IAM role
    role_policy_attachment = aws.iam.RolePolicyAttachment("documentUploadLambdaRolePolicy",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    )

    # Create policy for DynamoDB read access
    dynamo_policy = aws.iam.Policy(f"document-upload-dynamo-policy",
        policy=dynamo_db.arn.apply(lambda table_arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:Scan",
                    "dynamodb:Query"
                ],
                "Resource": [
                    f"{table_arn}",
                    f"{table_arn}/index/*",
                ]
            }]
        }))
    )

    # Attach DynamoDB policy to the role
    aws.iam.RolePolicyAttachment("document-upload-dynamo-policy-attachment",
        role=lambda_role.name,
        policy_arn=dynamo_policy.arn
    )

    # Create policy for S3 put object access
    s3_policy = aws.iam.Policy("document-upload-s3-policy",
        policy=bucket.arn.apply(lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject"
                ],
                "Resource": f"{arn}/*"
            }]
        }))
    )

    # Attach S3 policy to the role
    aws.iam.RolePolicyAttachment("document-upload-s3-policy-attachment",
        role=lambda_role.name,
        policy_arn=s3_policy.arn
    )

    # Create a Lambda layer for the requirements
    lambda_layer = aws.lambda_.LayerVersion("document-upload-layer",
        compatible_runtimes=["python3.12"],
        code=layer_zip,
        layer_name="document-upload-layer"
    )

    # Create the Lambda function
    lambda_function = aws.lambda_.Function("document_upload",
        code=pulumi.asset.AssetArchive({
            "lambda_function.py": pulumi.asset.FileAsset(lambda_code_path),
        }
        ),
        handler="lambda_function.handler",
        role=lambda_role.arn,
        runtime="python3.12",
        layers=[lambda_layer.arn],
        environment={
            "variables": {
                "ENVIRONMENT": "production",
                "CLIENT_ID": user_pool_client.id,
                "USER_POOL_ID": user_pool_client.user_pool_id,
                "BUCKET_NAME": bucket.id,
            }
        }
    )

    document_upload_lambda_backend = aws.apigatewayv2.Integration("document-upload",
        api_id=api['gateway'].id,
        integration_type="AWS_PROXY",
        description="document upload lambda integration",
        integration_method="POST",
        integration_uri=lambda_function.arn
    )

    http_route = aws.apigatewayv2.Route(
        "document-upload",
        api_id=api['gateway'].id,
        route_key="POST /document-upload",
        target=document_upload_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
        authorization_type="JWT",
        authorizer_id=api['user_authorizer'].id,
    )

    # Give permissions from API Gateway to invoke the Lambda
    http_invoke_permission = aws.lambda_.Permission("document-upload-http-lambda-permission",
        action="lambda:invokeFunction",
        function=lambda_function.name,
        principal="apigateway.amazonaws.com",
        source_arn=api['gateway'].execution_arn.apply(lambda arn: arn + "*/*"),
    )

    return {
        "lambda_function_name": lambda_function.name,
        "lambda_function_arn": lambda_function.arn
    }
