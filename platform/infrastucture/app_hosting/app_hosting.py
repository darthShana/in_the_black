import json

import pulumi
import pulumi_aws as aws
from pulumi_aws.apigatewayv2 import Api, Stage


def create_app_hosting(gateway: Api, stage: Stage):

    bucket = aws.s3.Bucket("client-hosting-bucket",
        bucket="client-hosting-bucket",
        acl="private",

    )

    # Block all public access to the bucket
    bucket_public_access_block = aws.s3.BucketPublicAccessBlock("public-access-block",
        bucket=bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True
    )

    # Create an Origin Access Identity for CloudFront
    cloudfront_oai = aws.cloudfront.OriginAccessIdentity("cloudfront-oai",
        comment="OAI for website distribution"
    )

    # Create bucket policy to allow CloudFront access
    bucket_policy = aws.s3.BucketPolicy("bucket-policy",
        bucket=bucket.id,
        policy=bucket.arn.apply(lambda arn: {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "AllowCloudFrontAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": cloudfront_oai.iam_arn
                },
                "Action": "s3:GetObject",
                "Resource": f"{arn}/*"
            }]
        }
        )
    )

    existing_api_gateway_domain = gateway.api_endpoint.apply(
        lambda endpoint: endpoint.replace('https://', '')
    )

    # Create Route 53 hosted zone
    hosted_zone = aws.route53.Zone("accountingAssistantZone",
        name="accountingassistant.io"
    )

    # Create ACM certificate
    certificate = aws.acm.Certificate("appCertificate",
        domain_name="app.accountingassistant.io",
        validation_method="DNS",
    )

    # Create validation record
    validation_record = aws.route53.Record("validationRecord",
        name=certificate.domain_validation_options[0].resource_record_name,
        zone_id=hosted_zone.id,
        type=certificate.domain_validation_options[0].resource_record_type,
        records=[certificate.domain_validation_options[0].resource_record_value],
        ttl=60
    )

    # Create certificate validation
    certificate_validation = aws.acm.CertificateValidation("certificateValidation",
        certificate_arn=certificate.arn,
        validation_record_fqdns=[validation_record.fqdn],
        opts=pulumi.ResourceOptions(provider=aws.Provider("us-east-1"))
    )

    # First, get the stage name from the Stage resource
    stage_name = stage.name

    # First, create the CloudFront Function
    cf_function = aws.cloudfront.Function("url-rewriter",
        code="""
    function handler(event) {
        var request = event.request;
        var uri = request.uri;
        if (uri.startsWith('/signin-callback')) {
          request.uri = "/"
        }
    
        return request;
    }
    """,
        name="url-rewriter",
        runtime="cloudfront-js-1.0",
        comment="Redirects all signin callback to index.html for SPA support"
    )

    distribution = aws.cloudfront.Distribution("website-distribution",
        enabled=True,
        is_ipv6_enabled=True,
        default_root_object="index.html",

        origins=[
            # S3 bucket origin
            aws.cloudfront.DistributionOriginArgs(
                domain_name=bucket.bucket_regional_domain_name,
                origin_id=bucket.id,
                s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
                    origin_access_identity=cloudfront_oai.cloudfront_access_identity_path
                )
            ),

            # API Gateway origin
            aws.cloudfront.DistributionOriginArgs(
                domain_name=existing_api_gateway_domain,
                origin_id="APIGateway",
                origin_path=pulumi.Output.concat("/", stage_name),
                custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
                    http_port=80,
                    https_port=443,
                    origin_protocol_policy="https-only",
                    origin_ssl_protocols=["TLSv1.2"],
                ),
            ),

        ],

        default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
            allowed_methods=[
                "GET",
                "HEAD",
                "OPTIONS"
            ],
            cached_methods=[
                "GET",
                "HEAD"
            ],
            target_origin_id=bucket.id,
            forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
                query_string=False,
                cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                    forward="none"
                )
            ),
            viewer_protocol_policy="redirect-to-https",
            min_ttl=0,
            default_ttl=3600,
            max_ttl=86400,
            function_associations=[
                aws.cloudfront.DistributionDefaultCacheBehaviorFunctionAssociationArgs(
                    event_type="viewer-request",
                    function_arn=cf_function.arn
                )
            ]

        ),

        # Ordered cache behaviors
        ordered_cache_behaviors=[
            aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
                path_pattern="/settings*",
                allowed_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
                cached_methods=["GET", "HEAD"],
                target_origin_id="APIGateway",
                forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
                    query_string=True,
                    headers=["Authorization", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"],
                    cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(forward="all"),
                ),
                viewer_protocol_policy="redirect-to-https",
                min_ttl=0,
                default_ttl=0,
                max_ttl=0,
                compress=True,
            ),
            aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
                path_pattern="/crud-entity-maintenance*",
                allowed_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
                cached_methods=["GET", "HEAD"],
                target_origin_id="APIGateway",
                forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
                    query_string=True,
                    headers=["Authorization", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"],
                    cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(forward="all"),
                ),
                viewer_protocol_policy="redirect-to-https",
                min_ttl=0,
                default_ttl=0,
                max_ttl=0,
                compress=True,
            ),
            aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
                path_pattern="/document-upload*",
                allowed_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
                cached_methods=["GET", "HEAD"],
                target_origin_id="APIGateway",
                forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
                    query_string=True,
                    headers=["Authorization", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"],
                    cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(forward="all"),
                ),
                viewer_protocol_policy="redirect-to-https",
                min_ttl=0,
                default_ttl=0,
                max_ttl=0,
                compress=True,
            ),
            aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
                path_pattern="/convert-pdf-to-image*",
                allowed_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
                cached_methods=["GET", "HEAD"],
                target_origin_id="APIGateway",
                forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
                    query_string=True,
                    headers=["Authorization", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"],
                    cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(forward="all"),
                ),
                viewer_protocol_policy="redirect-to-https",
                min_ttl=0,
                default_ttl=0,
                max_ttl=0,
                compress=True,
            ),
        ],

        restrictions=aws.cloudfront.DistributionRestrictionsArgs(
            geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                restriction_type="none"
            )
        ),

        viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
            acm_certificate_arn=certificate.arn,
            ssl_support_method="sni-only",
            minimum_protocol_version="TLSv1.2_2021"
        ),

        aliases=["app.accountingassistant.io"],

        price_class="PriceClass_200",

    )

    # Create an A record for app.accountingassistant.io
    app_record = aws.route53.Record("appRecord",
        zone_id=hosted_zone.id,
        name="app.accountingassistant.io",
        type="A",
        aliases=[aws.route53.RecordAliasArgs(
            name=distribution.domain_name,
            zone_id=distribution.hosted_zone_id,
            evaluate_target_health=False
        )]
    )

    # Export the CloudFront domain name
    pulumi.export('cloudfront', distribution)
    pulumi.export('bucket_name', bucket)
    pulumi.export("nameservers", hosted_zone.name_servers)


pulumi.export('create_api_gateway', create_app_hosting)
