from aws_cdk import (
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_kms as kms
)
from constructs import Construct

class SecureBucket(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str,
                    retention_days: int,
                    transition_days: int,
                    versioned: bool,
                    access_logging: bool,
                    cors_enabled: bool,
                    use_kms: bool,
                    event_bridge: bool,
                    object_lock: bool
                    ):
        super().__init__(scope, id)

        encryption_key = None
        encryption_type = s3.BucketEncryption.S3_MANAGED
        
        if use_kms:
            encryption_key = kms.Key(self, "Key", 
                enable_key_rotation=True, 
                removal_policy=RemovalPolicy.DESTROY)
            encryption_type = s3.BucketEncryption.KMS

        rules = []
        if transition_days > 0:
            rules.append(s3.LifecycleRule(
                transitions=[
                    s3.Transition(
                        storage_class=s3.StorageClass.GLACIER,
                        transition_after=Duration.days(transition_days)
                    )
                ]
            ))
        rules.append(s3.LifecycleRule(expiration=Duration.days(retention_days)))

        cors_rules = []
        if cors_enabled:
            cors_rules.append(s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
                allowed_origins=["*"],
                allowed_headers=["*"]
            ))

        log_bucket = None
        if access_logging:
            log_bucket = s3.Bucket(
                self, "AccessLogs",
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True,
                encryption=s3.BucketEncryption.S3_MANAGED,
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL
            )

        self.bucket = s3.Bucket(
            self, "Resource",
            encryption=encryption_type,
            encryption_key=encryption_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=versioned,
            object_lock_enabled=object_lock,
            event_bridge_enabled=event_bridge,
            cors=cors_rules,
            lifecycle_rules=rules,
            server_access_logs_bucket=log_bucket,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )