import pulumi
import pulumi_aws as aws


def create_api_gateway(cognito):
    http_endpoint = aws.apigatewayv2.Api("api-gateway-http",
        protocol_type="HTTP",
        cors_configuration={
            "allow_origins": ["http://localhost:4200", "https://d3oqhhtuqrkt4g.cloudfront.net"],
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "Content-Disposition",
                "X-Amz-Date",
                "X-Api-Key",
                "X-Amz-Security-Token",
                "Origin",
                "Access-Control-Request-Headers",
                "Access-Control-Request-Method"
            ],
            "allow_credentials": True,
            "max_age": 300
        }
    )

    # Create Authorizer
    api_authorizer = aws.apigatewayv2.Authorizer(
        "api-authorizer",
        api_id=http_endpoint.id,
        authorizer_type="JWT",
        identity_sources=["$request.header.Authorization"],
        name="cognito-api-authorizer",
        jwt_configuration={
            "audience": [cognito['api_user_pool_client'].id],
            "issuer": cognito['user_pool'].endpoint.apply(lambda endpoint: f"https://{endpoint}")
        }
    )

    # Create Authorizer
    user_authorizer = aws.apigatewayv2.Authorizer(
        "user-authorizer",
        api_id=http_endpoint.id,
        authorizer_type="JWT",
        identity_sources=["$request.header.Authorization"],
        name="cognito-user-authorizer",
        jwt_configuration={
            "audience": [cognito['user_auth_pool_client'].id],
            "issuer": cognito['user_pool'].endpoint.apply(lambda endpoint: f"https://{endpoint}")
        }
    )

    http_stage = aws.apigatewayv2.Stage(
        "prod",
        api_id=http_endpoint.id,
        auto_deploy=True,
        access_log_settings=None,
    )

    return {
        'gateway': http_endpoint,
        'stage': http_stage,
        'api_authorizer': api_authorizer,
        'user_authorizer': user_authorizer,
    }


pulumi.export('create_api_gateway', create_api_gateway)
