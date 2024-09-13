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
    user_pool_client = aws.cognito.UserPoolClient("property-valuation-user-pool-client",
        user_pool_id=user_pool.id,
        generate_secret=True,
        allowed_oauth_flows=["client_credentials"],
        allowed_oauth_scopes=["api/read"],
        allowed_oauth_flows_user_pool_client=True,
        supported_identity_providers=["COGNITO"],
        explicit_auth_flows=["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_ADMIN_USER_PASSWORD_AUTH"]
    )

    return {
        "user_pool": user_pool,
        "user_pool_client": user_pool_client
    }


pulumi.export('create_cognito', create_cognito)
