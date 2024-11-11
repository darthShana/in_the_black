import pulumi_aws as aws
import pulumi


def create_cognito():
    # Create Cognito User Pool
    user_pool = aws.cognito.UserPool("in-the-black-user-pool",
        auto_verified_attributes=["email"],
        password_policy={
            "minimumLength": 8,
            "requireLowercase": True,
            "requireNumbers": True,
            "requireSymbols": True,
            "requireUppercase": True,
        }
    )

    # Create Cognito User Pool Domain
    user_pool_domain = aws.cognito.UserPoolDomain("in-the-black",
        domain="in-the-black-auth",
        user_pool_id=user_pool.id
  )
    
    # Add this after creating the User Pool
    resource_server = aws.cognito.ResourceServer(
        "api-resource-server",
        identifier="api",
        name="Property Valuation Resource Server",
        scopes=[{
            "scope_name": "read",
            "scope_description": "Read access for property valuation",
        }],
        user_pool_id=user_pool.id
    )

    # Create Cognito User Pool Client
    user_pool_client = aws.cognito.UserPoolClient("property-valuation-api-client",
        user_pool_id=user_pool.id,
        generate_secret=True,
        allowed_oauth_flows=["client_credentials"],
        allowed_oauth_scopes=["api/read"],
        allowed_oauth_flows_user_pool_client=True,
        supported_identity_providers=["COGNITO"],
        explicit_auth_flows=["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_ADMIN_USER_PASSWORD_AUTH"]
    )

    # Create Cognito User Pool Client for user authentication
    user_auth_pool_client = aws.cognito.UserPoolClient("user-auth-client",
        user_pool_id=user_pool.id,
        generate_secret=False,  # Set to True if you need a client secret
        allowed_oauth_flows=["implicit", "code"],
        allowed_oauth_scopes=["email", "openid", "profile"],
        allowed_oauth_flows_user_pool_client=True,
        supported_identity_providers=["COGNITO"],
        callback_urls=["http://localhost:4200/signin-callback"],  # Replace with your actual callback URL
        logout_urls=["http://localhost:4200/logout"],  # Replace with your actual logout URL
        explicit_auth_flows=[
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH",
            "ALLOW_USER_PASSWORD_AUTH"
        ]
    )

    return {
        "user_pool": user_pool,
        "api_user_pool_client": user_pool_client,
        "user_auth_pool_client": user_auth_pool_client
    }


pulumi.export('create_cognito', create_cognito)
