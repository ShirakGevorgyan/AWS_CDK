from aws_cdk import (
    aws_s3 as s3,
    aws_athena as athena,
    aws_ec2 as ec2,
    RemovalPolicy,
    Duration
)
import aws_cdk.aws_redshift_alpha as redshift 

from constructs import Construct

class DataLakeAnalytics(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    data_bucket: s3.Bucket,
                    vpc: ec2.IVpc,
                    node_type_id: str,
                    number_of_nodes: int,
                    publicly_accessible: bool
                    ):
        super().__init__(scope, id)


        node_types = {
            "dc2.large": redshift.NodeType.DC2_LARGE,
            "ds2.xlarge": redshift.NodeType.DS2_XLARGE,
            "ra3.xlplus": redshift.NodeType.RA3_XLPLUS,
            "ra3.4xlarge": redshift.NodeType.RA3_4XLARGE,
            "ra3.16xlarge": redshift.NodeType.RA3_16XLARGE
        }

        selected_node_type = node_types.get(node_type_id)
        if not selected_node_type:
            raise ValueError(f"Invalid Redshift Node Type: '{node_type_id}'. Available: {list(node_types.keys())}")
        
        subnet_type = ec2.SubnetType.PUBLIC if publicly_accessible else ec2.SubnetType.PRIVATE_WITH_EGRESS

        self.redshift_cluster = redshift.Cluster(
            self, "RedshiftCluster",
            cluster_name=f"{id}-Cluster",
            master_user=redshift.Login(
                master_username="adminuser"
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=subnet_type),
            node_type=selected_node_type, 
            number_of_nodes=number_of_nodes,
            publicly_accessible=publicly_accessible,
            encrypted=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        
        athena_results_bucket = s3.Bucket(
            self, "AthenaResults",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(expiration=Duration.days(7))
            ]
        )

        self.athena_workgroup = athena.CfnWorkGroup(
            self, "AthenaWorkGroup",
            name=f"{id}-AnalyticsGroup",
            state="ENABLED",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=athena_results_bucket.s3_url_for_object(),
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3"
                    )
                ),
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True
            )
        )
