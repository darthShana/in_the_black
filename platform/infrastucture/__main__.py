"""An AWS Python Pulumi program"""
import json

import pulumi
import pulumi_aws as aws
from pulumi_aws import s3

from app_hosting.app_hosting import create_app_hosting
from api_gateway import create_api_gateway
from cognito_user_pool import create_cognito
from crud_entities.crud_entities import create_crud_entity_maintenance
from document_upload import create_document_upload
from pdf_converter import create_pdf_converter
from persistance import create_dbs
from property_valuation import create_property_valuation
from settings_resource.settings_resource import create_settings_resource

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket('black-transactions')

langgraph_user = aws.iam.User("langgraph_user",
    name="langgraph_user",
)

# Create access key for the user
langgraph_user_access_key = aws.iam.AccessKey("langgraph_user_key",
    user=langgraph_user.name
)

langgraph_user_secret = aws.secretsmanager.Secret("langgraph-credentials",
    description="Access key and secret for S3 and DynamoDB user",
    name="langgraph-credentials"
)

secret_version = aws.secretsmanager.SecretVersion("langgraph-user-credentials-version",
    secret_id=langgraph_user_secret.id,
    secret_string=pulumi.Output.all(langgraph_user_access_key.id, langgraph_user_access_key.secret).apply(
        lambda args: json.dumps({
            "access_key_id": args[0],
            "secret_access_key": args[1]
        })
    )
)

dbs = create_dbs()

# First, create the assume role policy that allows the user to assume the role
assume_role_policy = pulumi.Output.all(langgraph_user.arn).apply(
    lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": args[0]
            },
            "Action": "sts:AssumeRole",
            "Condition": {}
        }]
    })
)

# Create the role
langgraph_role = aws.iam.Role("langgraph-role",
    assume_role_policy=assume_role_policy,
    description="Role for LangGraph operations"
)

# Define the policy document
langgraph_user_policy_document = pulumi.Output.all(bucket.arn, dbs['transactions'].arn, dbs['customer_assets'].arn, dbs['users'].arn).apply(
    lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                f"{args[0]}/*",
                args[0],
            ]
        }, {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem"
            ],
            "Resource": [
                args[1],
                f"{args[1]}/index/*",
                args[2],
                f"{args[2]}/index/*",
                args[3],
                f"{args[3]}/index/*"
            ]
        }]
    })
)

# Create the IAM policy
langgraph_policy = aws.iam.Policy("langgraph-policy",
    description="Policy for LangGraph operations",
    policy=langgraph_user_policy_document
)

# Attach the policy to the role
role_policy_attachment = aws.iam.RolePolicyAttachment("langgraph-policy-attachment",
    role=langgraph_role.name,
    policy_arn=langgraph_policy.arn
)

# Allow the user to assume the role by attaching the appropriate policy
user_assume_role_policy = aws.iam.UserPolicy("langgraph-assume-role-policy",
    user=langgraph_user.name,
    policy=pulumi.Output.all(langgraph_role.arn).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "sts:AssumeRole",
                "Resource": args[0]
            }]
        })
    )
)

# Export the name of the bucket
pulumi.export('bucket_id', bucket.id)
pulumi.export('db_transactions', dbs['transactions'].id)
pulumi.export('db_customer_assets', dbs['customer_assets'].id)

# Export the bucket name and user credentials
pulumi.export("bucket_name", bucket.id)
pulumi.export("user_name", langgraph_user.name)
pulumi.export("access_key_id", langgraph_user_access_key.id)
pulumi.export("secret_access_key", langgraph_user_access_key.secret)

cognito_outputs = create_cognito()
gateway_outputs = create_api_gateway(cognito_outputs)
app_hosting = create_app_hosting(gateway_outputs['gateway'], gateway_outputs['stage'])
settings = create_settings_resource(cognito_outputs['user_pool'], cognito_outputs['user_auth_pool_client'], gateway_outputs['gateway'])

pdf_converter_outputs = create_pdf_converter(gateway_outputs)
property_valuation_outputs = create_property_valuation(gateway_outputs)
document_upload_outputs = create_document_upload(gateway_outputs, bucket, dbs['users'], cognito_outputs['user_auth_pool_client'])
crud_maintenance_outputs = create_crud_entity_maintenance(gateway_outputs['gateway'], gateway_outputs['user_authorizer'], dbs['users'], cognito_outputs['user_auth_pool_client'], langgraph_role)

# Export values if needed
pulumi.export("pdf-converter-http-endpoint", pdf_converter_outputs["apigatewayv2-http-endpoint"])
pulumi.export("property-valuation-http-endpoint", pdf_converter_outputs["apigatewayv2-http-endpoint"])
pulumi.export("langgraph-role", langgraph_role.arn)
