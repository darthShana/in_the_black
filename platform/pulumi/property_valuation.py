import base64
import time

import pulumi
import pulumi_aws as aws
import json
from pulumi import AssetArchive
import pulumi_docker as docker


def create_property_valuation(api):

    lambda_cache = aws.dynamodb.Table("property-valuation-lambda-cache",
        name="PropertyValuesCache",
        billing_mode="PAY_PER_REQUEST",
        hash_key="cache_key",
        attributes=[
            {
                "name": "cache_key",
                "type": "S",
            }
        ],
        tags={
            "Name": "dynamodb-table-1",
            "Environment": "production",
        }
    )

    # IAM role for Lambda
    lambda_role = aws.iam.Role("property-valuation-lambda-role",
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

    lambda_policy = aws.iam.RolePolicy("property-valuation-lambda-policy",
        role=lambda_role.id,
        policy=pulumi.Output.all(lambda_cache.arn).apply(
            lambda args: json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "arn:aws:logs:*:*:*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan"
                        ],
                        "Resource": args[0]
                    }
                ]
            }
            )
        )
    )

    # Define the ECR repository
    repo = aws.ecr.Repository("property-valuation-repo",
      name="property-valuation-repo",
      image_tag_mutability="MUTABLE",
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
    repo_policy = aws.ecr.LifecyclePolicy("property-valuation-lifecycle-policy",
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
    image = docker.Image("my-lambda-image",
         build=docker.DockerBuildArgs(
             context="./property_valuation_lambda",
             dockerfile="property_valuation_lambda/Dockerfile"
         ),
         image_name=pulumi.Output.concat(repo.repository_url, ":", unique_tag),
         registry=docker.RegistryArgs(
             server=repo.repository_url,
             username=ecr_credentials.apply(lambda creds: creds["username"]),
             password=ecr_credentials.apply(lambda creds: creds["password"])
         )
     )

    # Define the Lambda function
    property_valuation_lambda = aws.lambda_.Function(
        "property-valuation-lambda",
        image_uri=image.image_name,
        package_type="Image",
        role=lambda_role.arn,
        publish=True,
        timeout=90,
        memory_size=1024,
        opts=pulumi.ResourceOptions(depends_on=[image])
    )

    property_valuation_lambda_backend = aws.apigatewayv2.Integration("property-valuation",
        api_id=api['gateway'].id,
        integration_type="AWS_PROXY",
        description="property-valuation lambda integration",
        integration_method="POST",
        integration_uri=property_valuation_lambda.arn
    )

    http_route = aws.apigatewayv2.Route(
        "valuation",
        api_id=api['gateway'].id,
        route_key="ANY /valuation",
        target=property_valuation_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
        authorization_type="JWT",
        authorizer_id=api['authorizer'].id,
    )

    # Give permissions from API Gateway to invoke the Lambda
    http_invoke_permission = aws.lambda_.Permission("property-valuation-http-lambda-permission",
        action="lambda:invokeFunction",
        function=property_valuation_lambda.name,
        principal="apigateway.amazonaws.com",
        source_arn=api['gateway'].execution_arn.apply(lambda arn: arn + "*/*"),
    )

    # Output the CloudFront distribution URL and API Gateway URL
    return {
        "apigatewayv2-http-endpoint": pulumi.Output.all(api['gateway'].api_endpoint, api['stage'].name).apply(lambda values: values[0] + '/' + values[1] + '/')
    }
