from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_kms as kms
)
from constructs import Construct

class StandardTable(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    partition_key: str,
                    sort_key: str,
                    enable_backup: bool,
                    deletion_protection: bool,
                    use_kms: bool,
                    ttl_attribute: str = None,
                    stream: bool = False
                    ):
        super().__init__(scope, id)

        encryption = dynamodb.TableEncryption.AWS_MANAGED
        encryption_key = None
        
        if use_kms:
            encryption = dynamodb.TableEncryption.CUSTOMER_MANAGED
            encryption_key = kms.Key(self, "Key",
                enable_key_rotation=True, 
                removal_policy=RemovalPolicy.DESTROY
            )

        policy = RemovalPolicy.RETAIN if deletion_protection else RemovalPolicy.DESTROY

        stream_spec = dynamodb.StreamViewType.NEW_AND_OLD_IMAGES if stream else None

        self.table = dynamodb.Table(
            self, "Resource",
            partition_key=dynamodb.Attribute(name=partition_key, type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name=sort_key, type=dynamodb.AttributeType.STRING) if sort_key else None,
            
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            
            encryption=encryption,
            encryption_key=encryption_key,
            point_in_time_recovery=enable_backup,
            deletion_protection=deletion_protection,
            
            time_to_live_attribute=ttl_attribute,
            stream=stream_spec,
            
            removal_policy=policy
        )