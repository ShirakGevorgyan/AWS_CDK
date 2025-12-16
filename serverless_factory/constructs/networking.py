from aws_cdk import (
    aws_ec2 as ec2,
    aws_logs as logs,
    RemovalPolicy
)
from constructs import Construct

class StandardVpc(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    cidr: str,
                    max_azs: int,
                    nat_gateways: int,
                    use_s3_endpoint: bool,
                    use_dynamo_endpoint: bool
                    ):
        super().__init__(scope, id)

        self.vpc = ec2.Vpc(
            self, "Resource",
            ip_addresses=ec2.IpAddresses.cidr(cidr),
            max_azs=max_azs,
            nat_gateways=nat_gateways,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="Public", subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ]
        )

        log_group = logs.LogGroup(
            self, "FlowLogsGroup", 
            removal_policy=RemovalPolicy.DESTROY
        )
        
        ec2.FlowLog(
            self, "FlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group)
        )

        if use_s3_endpoint:
            self.vpc.add_gateway_endpoint(
                "S3Endpoint",
                service=ec2.GatewayVpcEndpointAwsService.S3
            )
            
        if use_dynamo_endpoint:
            self.vpc.add_gateway_endpoint(
                "DynamoEndpoint",
                service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
            )