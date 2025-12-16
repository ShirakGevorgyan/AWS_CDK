from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_lambda as _lambda,
    aws_logs as logs,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class StandardWorkflow(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    worker_function: _lambda.Function,
                    timeout_minutes: int,
                    use_express_type: bool,
                    enable_logging: bool,
                    enable_tracing: bool
                    ):
        super().__init__(scope, id)

        log_group = None
        log_config = None
        
        if enable_logging:
            log_group = logs.LogGroup(
                self, "SFNLogs",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY
            )
            log_config = sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            )

        task = tasks.LambdaInvoke(
            self, "InvokeWorker",
            lambda_function=worker_function,
            output_path="$.Payload"
        )
        
        task.add_retry(
            max_attempts=2,
            backoff_rate=2.0,
            interval=Duration.seconds(2),
            errors=["Lambda.TooManyRequestsException", "Lambda.Unknown"]
        )

        definition = sfn.Chain.start(task)

        sfn_type = sfn.StateMachineType.EXPRESS if use_express_type else sfn.StateMachineType.STANDARD

        self.state_machine = sfn.StateMachine(
            self, "Resource",
            definition=definition,
            timeout=Duration.minutes(timeout_minutes),
            state_machine_type=sfn_type,
            logs=log_config,
            tracing_enabled=enable_tracing
        )