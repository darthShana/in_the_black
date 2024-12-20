import base64
import time

import pulumi
import pulumi_aws as aws
import json
from pulumi import AssetArchive, FileAsset
from pulumi_aws.s3 import Bucket
import pulumi_docker as docker


def create_pdf_converter(api, bucket: Bucket):

    conversion_queue = aws.sqs.Queue("conversion_queue",
        name="conversion_queue",
        max_message_size=2048,
        message_retention_seconds=86400,
        visibility_timeout_seconds=150,
        tags={
            "Environment": "production",
        }
    )

    # IAM role for Lambda
    lambda_role = aws.iam.Role("pdf-converter-lambda-role",
       assume_role_policy=json.dumps({
           "Version": "2012-10-17",
           "Statement": [{
               "Action": "sts:AssumeRole",
               "Principal": {
                   "Service": "lambda.amazonaws.com"
               },
               "Effect": "Allow",
               "Sid": ""
           }]
       })
    )
    
    lambda_policy = aws.iam.RolePolicy("lambdaPolicy",
        role=lambda_role.id,
        policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }]
        })
    )

    # Define the ECR repository
    repo = aws.ecr.Repository("pdf-conversion-repo",
        name="pdf-conversion-repo",
        image_tag_mutability="MUTABLE",
        force_delete=True  # Enable force delete if needed
    )

    # Define the lifecycle policy
    lifecycle_policy = {
        "rules": [
            {
                "rulePriority": 1,
                "description": "Keep last 3 images",
                "selection": {
                    "tagStatus": "any",
                    "countType": "imageCountMoreThan",
                    "countNumber": 3
                },
                "action": {
                    "type": "expire"
                }
            }
        ]
    }

    # Attach the lifecycle policy to the repository
    repo_policy = aws.ecr.LifecyclePolicy("pdf-conversion-lifecycle-policy",
        repository=repo.name,
        policy=json.dumps(lifecycle_policy)
    )

    # Create a function to get ECR credentials
    def get_ecr_credentials(registry_id):
        creds = aws.ecr.get_credentials(registry_id=registry_id)
        decoded = base64.b64decode(creds.authorization_token).decode('utf-8')
        username, password = decoded.split(':')
        return {
            "username": username,
            "password": password
        }

    # Use apply to handle the Output
    ecr_credentials = repo.registry_id.apply(get_ecr_credentials)

    unique_tag = f"build-{int(time.time())}"

    # Build and push the Docker image
    image = docker.Image("pdf-conversion-image",
        build=docker.DockerBuildArgs(
            context="./pdf_to_image_lambda",  # Directory containing Dockerfile
            dockerfile="pdf_to_image_lambda/Dockerfile"
        ),
        image_name=pulumi.Output.concat(repo.repository_url, ":", unique_tag),
        registry=docker.RegistryArgs(
            server=repo.repository_url,
            username=ecr_credentials.apply(lambda creds: creds["username"]),
            password=ecr_credentials.apply(lambda creds: creds["password"])
        )
    )

    def create_lambda_asset(function_file):
        return pulumi.AssetArchive({
            '__main__.py': pulumi.FileAsset(f"pdf_to_image_lambda/{function_file}")
        }
        )

    # Define the Lambda functions
    start_conversion_lambda = aws.lambda_.Function(
        "pdfToImageStartJob",
        runtime="python3.8",
        handler="__main__.handler",
        role=lambda_role.arn,
        code=create_lambda_asset("start_conversion.py"),
        timeout=30,
        environment={
            "variables": {
                "ENVIRONMENT": "production",
                "SQS_QUEUE_URL": conversion_queue.url,
                "BUCKET": bucket.id,
            }
        }
    )

    pdf_to_image_lambda = aws.lambda_.Function(
        "pdfToImageProcessJob",
        image_uri=image.image_name,
        package_type="Image",
        role=lambda_role.arn,
        publish=True,
        timeout=120,
        memory_size=2048,
        environment={
            "variables": {
                "PYTHONPATH": "/var/task"
            }
        },
        opts=pulumi.ResourceOptions(depends_on=[image])
    )

    # First, create an SQS event source mapping for the Lambda
    aws.lambda_.EventSourceMapping("pdfToImageEventMapping",
        event_source_arn=conversion_queue.arn,
        function_name=pdf_to_image_lambda.arn,
        batch_size=1,
        enabled=True
    )

    # Then, add SQS permissions to the Lambda role
    aws.iam.RolePolicy("sqsPolicy",
        role=lambda_role.id,
        policy=pulumi.Output.all(conversion_queue.arn).apply(
            lambda args: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:SendMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:ChangeMessageVisibility"
                    ],
                    "Resource": args[0]
                }]
            }
            )
        )
    )

    aws.iam.RolePolicy("s3PutPolicy",
        role=lambda_role.id,
        policy=pulumi.Output.all(bucket.arn).apply(
            lambda args: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"{args[0]}/*",  # This allows access to all objects in the bucket
                        args[0]  # This allows access to the bucket itself
                    ]
                }]
            }
            )
        )
    )

    http_lambda_backend = aws.apigatewayv2.Integration("pdf-converter-integration",
        api_id=api['gateway'].id,
        integration_type="AWS_PROXY",
        connection_type="INTERNET",
        description="Lambda example",
        integration_method="POST",
        timeout_milliseconds=30000,
        integration_uri=start_conversion_lambda.arn,
        passthrough_behavior="WHEN_NO_MATCH",
    )

    http_route = aws.apigatewayv2.Route("convert_pdf_to_image",
        api_id=api['gateway'].id,
        route_key="ANY /convert-pdf-to-image",
        target=http_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
        authorization_type="JWT",
        authorizer_id=api['api_authorizer'].id
    )

    # Give permissions from API Gateway to invoke the Lambda
    http_invoke_permission = aws.lambda_.Permission("api-http-lambda-permission",
        action="lambda:invokeFunction",
        function=start_conversion_lambda.name,
        principal="apigateway.amazonaws.com",
        source_arn=api['gateway'].execution_arn.apply(lambda arn: arn + "*/*"),
    )

    # Output the CloudFront distribution URL and API Gateway URL
    return {
        "apigatewayv2-http-endpoint": pulumi.Output.all(api['gateway'].api_endpoint, api['stage'].name).apply(lambda values: values[0] + '/' + values[1] + '/')
    }
