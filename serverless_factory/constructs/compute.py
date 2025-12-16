from aws_cdk import (
    RemovalPolicy,
    Duration,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_ec2 as ec2,
)
from constructs import Construct

class StandardFunction(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str,
                    handler: str, 
                    memory: int, 
                    timeout_sec: int,
                    tracing: bool,
                    use_arm: bool,
                    log_retention: int,
                    env: dict = None,
                    vpc: ec2.IVpc = None,
                    layers: list = None,
                    reserved_concurrency: int = None,
                    code_path: str = "lambda_src"
                    ):
        super().__init__(scope, id)

        retention_map = {
            1: logs.RetentionDays.ONE_DAY,
            7: logs.RetentionDays.ONE_WEEK,
            30: logs.RetentionDays.ONE_MONTH,
            90: logs.RetentionDays.THREE_MONTHS,
            365: logs.RetentionDays.ONE_YEAR
        }
        
        log_retention_obj = retention_map.get(log_retention, logs.RetentionDays.ONE_WEEK)

        log_group = logs.LogGroup(
            self, "LogGroup",
            retention=log_retention_obj,
            removal_policy=RemovalPolicy.DESTROY
        )

        vpc_subnets = None
        if vpc:
            vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)

        arch = _lambda.Architecture.ARM_64 if use_arm else _lambda.Architecture.X86_64

        trace_mode = _lambda.Tracing.ACTIVE if tracing else _lambda.Tracing.DISABLED

        self.function = _lambda.Function(
            self, "Resource",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler=handler,
            code=_lambda.Code.from_asset(code_path),
            memory_size=memory,
            timeout=Duration.seconds(timeout_sec),
            environment=env or {},
            architecture=arch,
            tracing=trace_mode,
            log_group=log_group,
            vpc=vpc,
            vpc_subnets=vpc_subnets,
            reserved_concurrent_executions=reserved_concurrency,
            layers=layers or [],
            insights_version=_lambda.LambdaInsightsVersion.VERSION_1_0_229_0
        )