from aws_cdk import (
    Duration,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_kms as kms,
)
from constructs import Construct

class StandardQueue(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str,
                    fifo: bool,
                    retention_days: int,
                    encrypted: bool,
                    visibility_timeout: int
                    ):
        super().__init__(scope, id)

        encryption = sqs.QueueEncryption.UNENCRYPTED
        
        if encrypted:
            encryption = sqs.QueueEncryption.KMS_MANAGED

        queue_name = f"{id}.fifo" if fifo else None

        self.dlq = sqs.Queue(
            self, "DeadLetterBox",
            fifo=fifo,
            encryption=encryption,
            retention_period=Duration.days(14),
            enforce_ssl=True
        )

        self.queue = sqs.Queue(
            self, "Resource",
            queue_name=queue_name,
            fifo=fifo,
            content_based_deduplication=fifo,
            
            encryption=encryption,
            enforce_ssl=True,
            
            visibility_timeout=Duration.seconds(visibility_timeout),
            retention_period=Duration.days(retention_days),
            
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3, 
                queue=self.dlq
            )
        )

class StandardTopic(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    fifo: bool,
                    encrypted: bool
                    ):
        super().__init__(scope, id)
        
        topic_name = f"{id}.fifo" if fifo else None
        master_key = kms.Alias.from_alias_name(self, "SnsKey", "alias/aws/sns") if encrypted else None

        self.topic = sns.Topic(
            self, "Resource",
            topic_name=topic_name,
            fifo=fifo,
            content_based_deduplication=fifo,
            master_key=master_key,
            display_name=id
        )

    def subscribe_queue(self, standard_queue: StandardQueue):
        self.topic.add_subscription(subs.SqsSubscription(standard_queue.queue))