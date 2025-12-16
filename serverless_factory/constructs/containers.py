from aws_cdk import (
    aws_ecr as ecr,
    aws_eks as eks,
    aws_ec2 as ec2,
    RemovalPolicy
)
from aws_cdk.lambda_layer_kubectl_v30 import KubectlV30Layer
from constructs import Construct

class ContainerRepo(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    scan_on_push: bool,
                    max_image_count: int,
                    immutable_tags: bool
                    ):
        super().__init__(scope, id)

        mutability = ecr.TagMutability.IMMUTABLE if immutable_tags else ecr.TagMutability.MUTABLE

        self.repo = ecr.Repository(
            self, "Resource",
            image_scan_on_push=scan_on_push,
            image_tag_mutability=mutability,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep only last X images",
                    max_image_count=max_image_count,
                    tag_status=ecr.TagStatus.ANY
                )
            ]
        )

class K8sCluster(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    vpc: ec2.IVpc, 
                    instance_type: str,
                    min_size: int,
                    max_size: int,
                    enable_logging: bool,
                    public_access: bool
                    ):
        super().__init__(scope, id)

        logs = []
        if enable_logging:
            logs = [
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR
            ]

        endpoint = eks.EndpointAccess.PUBLIC_AND_PRIVATE if public_access else eks.EndpointAccess.PRIVATE

        self.cluster = eks.Cluster(
            self, "Resource",
            vpc=vpc,
            version=eks.KubernetesVersion.V1_30,
            cluster_name=id,
            kubectl_layer=KubectlV30Layer(self, "KubectlLayer"),
            endpoint_access=endpoint,
            cluster_logging=logs,
            default_capacity=0,
        )

        self.cluster.add_nodegroup_capacity(
            "MainNodeGroup",
            instance_types=[ec2.InstanceType(instance_type)],
            min_size=min_size,
            max_size=max_size,
            desired_size=min_size
        )