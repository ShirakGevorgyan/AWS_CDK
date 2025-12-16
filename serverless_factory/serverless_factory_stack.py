from aws_cdk import (
    Stack,
    Tags,
    aws_cloudwatch as cw
)
from constructs import Construct

from .config.loader import ConfigLoader
from .factories.manager import ResourceManager

class ServerlessFactoryStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        print(f"🌍 Deploying Environment: {env_name.upper()}")

        project_config = ConfigLoader.load("pipelines.json")
        print(f"  Initializing Project: {project_config.project_name}")

        Tags.of(self).add("Project", project_config.project_name)
        Tags.of(self).add("ManagedBy", "CDK-Factory")
        
        Tags.of(self).add("Environment", env_name)

        dashboard = cw.Dashboard(
            self, 
            "MainDashboard",
            dashboard_name=f"{project_config.project_name}-{env_name}-Overview"
        )
        
        self.global_vpc = None

        for res in project_config.resources:
            
            print(f"   Generating Module: {res.id} ({res.type})...")

            ResourceManager(
                self, 
                res.id, 
                res, 
                env_name=env_name, 
                dashboard=dashboard, 
                global_vpc=self.global_vpc
            )