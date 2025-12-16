from aws_cdk import (
    aws_iam as iam,
    Duration
)
from constructs import Construct

class CustomRole(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    service_principal: str,
                    boundary_arn: str,
                    managed_policy_names: list,
                    max_session_duration: int
                    ):
        super().__init__(scope, id)
        
        permissions_boundary = None
        if boundary_arn:
            permissions_boundary = iam.ManagedPolicy.from_managed_policy_arn(
                self, "Boundary", boundary_arn
            )

        policies = []
        if managed_policy_names:
            for policy_name in managed_policy_names:
                policies.append(
                    iam.ManagedPolicy.from_aws_managed_policy_name(policy_name)
                )


        self.role = iam.Role(
            self, "Resource",
            assumed_by=iam.ServicePrincipal(service_principal),
            description=f"Managed Custom role for {id}",
            permissions_boundary=permissions_boundary,
            managed_policies=policies,
            max_session_duration=Duration.seconds(max_session_duration),
            path="/serverless-factory/"
        )