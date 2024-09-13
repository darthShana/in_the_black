import base64

import pulumi
import pulumi_aws as aws
import json
from pulumi import AssetArchive
import pulumi_docker as docker


def create_property_valuation(cognito):

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
    repo = aws.ecr.Repository("my-ecr-repo",
      name="my-lambda-container-repo",
      force_delete=True
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

    # Build and push the Docker image
    image = docker.Image("my-lambda-image",
         build=docker.DockerBuildArgs(
             context="./property_valuation_lambda",
             dockerfile="property_valuation_lambda/Dockerfile"
         ),
         image_name=repo.repository_url,
         registry=docker.RegistryArgs(
             server=repo.repository_url,
             username=ecr_credentials.apply(lambda creds: creds["username"]),
             password=ecr_credentials.apply(lambda creds: creds["password"])
         )
     )

    # Define the Lambda function
    property_valuation_lambda = aws.lambda_.Function(
        "property-valuation-lambda",
        image_uri=image.image_name.apply(lambda name: f"{name}:latest"),
        package_type="Image",
        role=lambda_role.arn,
        publish=True,
        timeout=90,
        memory_size=1024,
        opts=pulumi.ResourceOptions(depends_on=[image])
    )

    http_endpoint = aws.apigatewayv2.Api("property-valuation-http",
        protocol_type="HTTP"
    )

    property_valuation_lambda_backend = aws.apigatewayv2.Integration("property-valuation",
        api_id=http_endpoint.id,
        integration_type="AWS_PROXY",
        description="property-valuation lambda integration",
        integration_method="POST",
        integration_uri=property_valuation_lambda.arn
    )

    # Create Authorizer
    authorizer = aws.apigatewayv2.Authorizer("property-valuation-authorizer",
        api_id=http_endpoint.id,
        authorizer_type="JWT",
        identity_sources=["$request.header.Authorization"],
        name="cognito-authorizer",
        jwt_configuration={
            "audience": [cognito['user_pool_client'].id],
            "issuer": cognito['user_pool'].endpoint.apply(lambda endpoint: f"https://{endpoint}")
        }
    )

    http_route = aws.apigatewayv2.Route("example-route",
        api_id=http_endpoint.id,
        route_key="ANY /{proxy+}",
        target=property_valuation_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
        authorization_type="JWT",
        authorizer_id=authorizer.id,
    )

    http_stage = aws.apigatewayv2.Stage("stage",
        api_id=http_endpoint.id,
        route_settings= [
            {
                "route_key": http_route.route_key,
                "throttling_burst_limit": 1,
                "throttling_rate_limit": 0.5,
            }
        ],
        auto_deploy=True,
    )

    # Give permissions from API Gateway to invoke the Lambda
    http_invoke_permission = aws.lambda_.Permission("property-valuation-http-lambda-permission",
        action="lambda:invokeFunction",
        function=property_valuation_lambda.name,
        principal="apigateway.amazonaws.com",
        source_arn=http_endpoint.execution_arn.apply(lambda arn: arn + "*/*"),
    )

    # Output the CloudFront distribution URL and API Gateway URL
    return {
        "apigatewayv2-http-endpoint": pulumi.Output.all(http_endpoint.api_endpoint, http_stage.name).apply(lambda values: values[0] + '/' + values[1] + '/')
    }
