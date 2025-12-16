from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class AuroraDB(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    vpc: ec2.IVpc,
                    min_capacity: float,
                    max_capacity: float,
                    backup_retention_days: int,
                    deletion_protection: bool,
                    enable_insights: bool,
                    monitoring_interval: int
                    ):
        super().__init__(scope, id)

        removal_policy = RemovalPolicy.RETAIN if deletion_protection else RemovalPolicy.DESTROY

        self.cluster = rds.DatabaseCluster(
            self, "Resource",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_2
            ),
            writer=rds.ClusterInstance.serverless_v2(
                "Writer",
                publicly_accessible=False,
                enable_performance_insights=enable_insights,
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            serverless_v2_min_capacity=min_capacity,
            serverless_v2_max_capacity=max_capacity,
            storage_encrypted=True,
            backup=rds.BackupProps(retention=Duration.days(backup_retention_days)),
            deletion_protection=deletion_protection,
            removal_policy=removal_policy,
            cloudwatch_logs_exports=["postgresql"]
        )