from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_kinesis as kinesis,
    aws_kms as kms
)
from constructs import Construct

class DataStream(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    shard_count: int,
                    retention_hours: int,
                    is_on_demand: bool,
                    encrypt: bool
                    ):
        super().__init__(scope, id)

        stream_mode = kinesis.StreamMode.ON_DEMAND if is_on_demand else kinesis.StreamMode.PROVISIONED
    
        encryption = kinesis.StreamEncryption.UNENCRYPTED
        encryption_key = None
        
        if encrypt:
            encryption = kinesis.StreamEncryption.KMS
            encryption_key = kms.Key(self, "Key", 
                enable_key_rotation=True, 
                removal_policy=RemovalPolicy.DESTROY
            )

        policy = RemovalPolicy.RETAIN if encrypt else RemovalPolicy.DESTROY

        self.stream = kinesis.Stream(
            self, "Resource",
            stream_name=id,
            
            stream_mode=stream_mode,
            shard_count=shard_count if not is_on_demand else None,
            retention_period=Duration.hours(retention_hours),
            
            encryption=encryption,
            encryption_key=encryption_key,
            
            removal_policy=policy
        )