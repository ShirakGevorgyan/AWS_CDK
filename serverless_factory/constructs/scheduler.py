from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class CronJob(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    rate_minutes: int,
                    target_fn: _lambda.Function,
                    enabled: bool,
                    retry_attempts: int,
                    create_dlq: bool
                    ):
        super().__init__(scope, id)

        dlq = None
        if create_dlq:
            dlq = sqs.Queue(
                self, "DLQ",
                retention_period=Duration.days(14),
                removal_policy=RemovalPolicy.DESTROY
            )

        lambda_target = targets.LambdaFunction(
            target_fn,
            retry_attempts=retry_attempts,
            dead_letter_queue=dlq
        )

        self.rule = events.Rule(
            self, "Resource",
            description=f"Scheduled task for {id}",
            schedule=events.Schedule.rate(Duration.minutes(rate_minutes)),
            enabled=enabled,
            targets=[lambda_target]
        )