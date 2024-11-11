import json
import os
import subprocess

import pulumi
import pulumi_aws as aws
from pulumi_aws.apigatewayv2 import Api, Authorizer
from pulumi_aws.cognito import UserPoolClient

from pulumi_aws.dynamodb import Table
from pulumi_aws.iam import Role

# Define the path to the Lambda function code and requirements
lambda_code_path = "crud_entities/crud_entity_maintenance/lambda_function.py"
requirements_path = "crud_entities/crud_entity_maintenance/requirements.txt"

# Get the current region
current_region = aws.get_region()


def create_crud_entity_maintenance(api: Api, authorizer: Authorizer, user_db: Table, user_pool_client: UserPoolClient, langgraph_role: Role):

    accepted_anomalies_db = aws.dynamodb.Table("accepted_anomalies",
        name="AcceptedAnomalies",
        billing_mode="PAY_PER_REQUEST",
        hash_key="Id",
        attributes=[
            {
                "name": "Id",
                "type": "S",
            },
            {
                "name": "UserId",
                "type": "S",
            }
        ],
        global_secondary_indexes=[{
            "name": "CustomerIndex",
            "hash_key": "UserId",
            "projection_type": "ALL"
        }],
        tags={
            "Name": "accepted_anomalies",
            "Environment": "production",
        }
    )

    os.makedirs('crud_entities/crud_entity_maintenance/layer', exist_ok=True)
    # Install the dependencies into the layer directory
    subprocess.run([
        "pip", "install",
        "-r", requirements_path,
        "-t", "crud_entities/crud_entity_maintenance/layer/python",
        "--platform", "manylinux2014_x86_64",
        "--upgrade",
        "--only-binary=:all:",
    ]
    )

    # Create a ZIP archive of the layer
    layer_zip = pulumi.asset.AssetArchive({
        ".": pulumi.asset.FileArchive('crud_entities/crud_entity_maintenance/layer')
    })

    # Create an IAM role for the Lambda function
    lambda_role = aws.iam.Role("crudEntityMaintenanceLambdaRole",
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
    role_policy_attachment = aws.iam.RolePolicyAttachment("crudEntityMaintenanceLambdaRolePolicy",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    )

    # Create policy for DynamoDB read access
    read_user_dynamo_policy = aws.iam.Policy(f"read-user-dynamo-policy",
        policy=user_db.arn.apply(lambda table_arn: json.dumps({
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
    # Create policy for DynamoDB write access
    write_accepted_anomalies_policy = aws.iam.Policy(f"write-accepted-anomalies-policy",
        policy=accepted_anomalies_db.arn.apply(lambda table_arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                ],
                "Resource": [
                    f"{table_arn}"
                ]
            }]
        }))
    )
    read_accepted_anomalies_policy = aws.iam.Policy(f"read-accepted-anomalies-policy",
        policy=accepted_anomalies_db.arn.apply(lambda table_arn: json.dumps({
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
        }
        )
        )
    )

    # Attach DynamoDB policy to the role
    aws.iam.RolePolicyAttachment("crud-maintenance-user-dynamo-policy-attachment",
        role=lambda_role.name,
        policy_arn=read_user_dynamo_policy.arn
    )
    aws.iam.RolePolicyAttachment("crud-langgraph-dynamo-policy-attachment",
        role=langgraph_role.name,
        policy_arn=read_accepted_anomalies_policy.arn
    )
    aws.iam.RolePolicyAttachment("crud-maintenance-accepted-anomalies-dynamo-policy-attachment",
        role=lambda_role.name,
        policy_arn=write_accepted_anomalies_policy.arn
    )

    # Create a Lambda layer for the requirements
    lambda_layer = aws.lambda_.LayerVersion("crud-maintenance-upload-layer",
        compatible_runtimes=["python3.12"],
        code=layer_zip,
        layer_name="crud-maintenance-upload-layer"
    )

    # Create the Lambda function
    lambda_function = aws.lambda_.Function("crud_entity_maintenance",
        code=pulumi.asset.AssetArchive({
            "crud_entity_maintenance.py": pulumi.asset.FileAsset(lambda_code_path),
        }
        ),
        handler="crud_entity_maintenance.handler",
        role=lambda_role.arn,
        runtime="python3.12",
        layers=[lambda_layer.arn],
        environment={
            "variables": {
                "ENVIRONMENT": "production",
                "CLIENT_ID": user_pool_client.id,
                "USER_POOL_ID": user_pool_client.user_pool_id
            }
        }
    )

    document_upload_lambda_backend = aws.apigatewayv2.Integration("crud-entity-maintenance",
        api_id=api.id,
        integration_type="AWS_PROXY",
        description="crud entity maintenance integration",
        integration_method="POST",
        integration_uri=lambda_function.arn
    )

    aws.apigatewayv2.Route(
        "crud-entity-maintenance",
        api_id=api.id,
        route_key="POST /crud-entity-maintenance",
        target=document_upload_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
        authorization_type="JWT",
        authorizer_id=authorizer.id,
    )

    # Give permissions from API Gateway to invoke the Lambda
    aws.lambda_.Permission("crud-maintenance-http-lambda-permission",
        action="lambda:invokeFunction",
        function=lambda_function.name,
        principal="apigateway.amazonaws.com",
        source_arn=api.execution_arn.apply(lambda arn: arn + "*/*"),
    )

    return {
        "lambda_function_name": lambda_function.name,
        "lambda_function_arn": lambda_function.arn
    }
