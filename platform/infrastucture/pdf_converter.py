import pulumi
import pulumi_aws as aws
import json
from pulumi import AssetArchive, FileAsset


def create_pdf_converter(api):

    # IAM role for Lambda
    lambda_role = aws.iam.Role("in-the-black-pdf-converter-lambda-role",
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

    # Define the Lambda layer
    poppler_layer = aws.lambda_.LayerVersion("popplerLayer",
        compatible_runtimes=["python3.8"],
        code=pulumi.FileArchive("pdf_to_image_lambda/layer/poppler.zip"),
        layer_name="poppler-layer",
        description="Poppler library for PDF processing"
    )

    def create_lambda_asset():
        return AssetArchive({
            '.': pulumi.FileArchive('./pdf_to_image_lambda')
        })

    # Define the Lambda function
    pdf_to_image_lambda = aws.lambda_.Function(
        "pdfToImageLambda",
        runtime="python3.8",
        handler="crud_entity_maintenance.handler",
        role=lambda_role.arn,
        code=create_lambda_asset(),
        layers=[poppler_layer.arn, "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-Pillow:10"],
        timeout=30,
        memory_size=1024
    )

    http_lambda_backend = aws.apigatewayv2.Integration("pdf-converter-integration",
        api_id=api['gateway'].id,
        integration_type="AWS_PROXY",
        connection_type="INTERNET",
        description="Lambda example",
        integration_method="POST",
        integration_uri=pdf_to_image_lambda.arn,
        passthrough_behavior="WHEN_NO_MATCH"
    )

    http_route = aws.apigatewayv2.Route(
        "convert_pdf_to_image",
        api_id=api['gateway'].id,
        route_key="ANY /convert-pdf-to-image",
        target=http_lambda_backend.id.apply(lambda target_url: "integrations/" + target_url),
        authorization_type="JWT",
        authorizer_id=api['api_authorizer'].id
    )

    # Give permissions from API Gateway to invoke the Lambda
    http_invoke_permission = aws.lambda_.Permission("api-http-lambda-permission",
        action="lambda:invokeFunction",
        function=pdf_to_image_lambda.name,
        principal="apigateway.amazonaws.com",
        source_arn=api['gateway'].execution_arn.apply(lambda arn: arn + "*/*"),
    )

    # Output the CloudFront distribution URL and API Gateway URL
    return {
        "apigatewayv2-http-endpoint": pulumi.Output.all(api['gateway'].api_endpoint, api['stage'].name).apply(lambda values: values[0] + '/' + values[1] + '/')
    }
