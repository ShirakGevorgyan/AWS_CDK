from aws_cdk import (
    Stack,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct

class CdnDistribution(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    content_bucket: s3.Bucket,
                    log_bucket: s3.Bucket,
                    price_class_str: str,
                    geo_locations: list,
                    web_acl_id: str = None
                    ):
        super().__init__(scope, id)

        price_map = {
            "100": cloudfront.PriceClass.PRICE_CLASS_100,
            "200": cloudfront.PriceClass.PRICE_CLASS_200,
            "ALL": cloudfront.PriceClass.PRICE_CLASS_ALL
        }
        selected_price = price_map.get(price_class_str, cloudfront.PriceClass.PRICE_CLASS_100)

        geo_restrict = None
        if geo_locations:
            geo_restrict = cloudfront.GeoRestriction.denylist(geo_locations)

        oac = cloudfront.CfnOriginAccessControl(
            self, "OAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=f"{id}-OAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4"
            )
        )

        self.distribution = cloudfront.Distribution(
            self, "Resource",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(content_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress=True,
            ),
            comment=f"Enterprise CDN for {id}",

            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            
            default_root_object="index.html",
            
            price_class=selected_price,
            geo_restriction=geo_restrict,
            web_acl_id=web_acl_id,
            enable_logging=True,
            log_bucket=log_bucket,
            log_file_prefix="cdn-logs/"
        )

        cfn_dist = self.distribution.node.default_child
        cfn_dist.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId", 
            oac.attr_id
        )
        
        content_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowCloudFrontServicePrincipal",
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                resources=[content_bucket.arn_for_objects("*")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{Stack.of(self).account}:distribution/{self.distribution.distribution_id}"
                    }
                }
            )
        )