import pulumi
import pulumi_aws as aws


def create_api_gateway(cognito):
    http_endpoint = aws.apigatewayv2.Api("api-gateway-http",
        protocol_type="HTTP"
    )

    # Create Authorizer
    authorizer = aws.apigatewayv2.Authorizer(
        "api-authorizer",
        api_id=http_endpoint.id,
        authorizer_type="JWT",
        identity_sources=["$request.header.Authorization"],
        name="cognito-authorizer",
        jwt_configuration={
            "audience": [cognito['api_user_pool_client'].id],
            "issuer": cognito['user_pool'].endpoint.apply(lambda endpoint: f"https://{endpoint}")
        }
    )

    http_stage = aws.apigatewayv2.Stage(
        "prod",
        api_id=http_endpoint.id,
        auto_deploy=True,
        access_log_settings=None
    )

    return {
        'gateway': http_endpoint,
        'stage': http_stage,
        'authorizer': authorizer,
    }


pulumi.export('create_api_gateway', create_api_gateway)
