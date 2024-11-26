import pulumi
import pulumi_aws as aws

from pulumi_aws.apigatewayv2 import Api
from pulumi_aws.cognito import UserPool, UserPoolClient

lambda_code_path = "settings_resource/lambda/lambda_function.py"


def create_settings_resource(user_pool: UserPool, user_pool_client: UserPoolClient, gateway: Api):

    # Create an IAM role for the Lambda function
    lambda_role = aws.iam.Role("settingsLambdaRole",
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
    role_policy_attachment = aws.iam.RolePolicyAttachment("settingsLambdaRolePolicy",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    )

    # Create the Lambda function
    lambda_function = aws.lambda_.Function("settings",
        code=pulumi.asset.AssetArchive({
            "crud_entity_maintenance.py": pulumi.asset.FileAsset(lambda_code_path),
        }
        ),
        handler="crud_entity_maintenance.handler",
        role=lambda_role.arn,
        runtime="python3.12",
        environment={
            "variables": {
                "ENVIRONMENT": "production",
                "ENDPOINT": user_pool.endpoint,
                "CLIENT_ID": user_pool_client.id,
                "USER_POOL_ID": user_pool.domain
            }
        }
    )

    settings_lambda_backend = aws.apigatewayv2.Integration("settings",
        api_id=gateway.id,
        integration_type="AWS_PROXY",
        description="crud entity maintenance integration",
        integration_method="GET",
        integration_uri=lambda_function.arn
    )

    aws.apigatewayv2.Route(
        "settings",
        api_id=gateway.id,
        route_key="GET /settings",
        target=settings_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
    )

    # Give permissions from API Gateway to invoke the Lambda
    aws.lambda_.Permission("settings-http-lambda-permission",
        action="lambda:invokeFunction",
        function=lambda_function.name,
        principal="apigateway.amazonaws.com",
        source_arn=gateway.execution_arn.apply(lambda arn: arn + "*/*"),
    )

