#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from serverless_factory.serverless_factory_stack import ServerlessFactoryStack

app = cdk.App()

target_env = app.node.try_get_context("env") or "dev"
valid_envs = ["dev", "prod"]

if target_env not in valid_envs:
    raise ValueError(f"❌ Invalid environment: '{target_env}'. Must be one of {valid_envs}")

account_id = os.getenv('CDK_DEFAULT_ACCOUNT')
region = os.getenv('CDK_DEFAULT_REGION')

print(f" Initializing App for: {target_env.upper()} | Account: {account_id} | Region: {region}")

aws_env = cdk.Environment(account=account_id, region=region)

stack_name = f"EnterprisePlatform-{target_env.capitalize()}"

stack = ServerlessFactoryStack(
    app, 
    stack_name,
    env=aws_env,
    env_name=target_env,
    description=f"Enterprise Platform Infrastructure [{target_env}]"
)

cdk.Tags.of(app).add("Environment", target_env)
cdk.Tags.of(app).add("ManagedBy", "CDK-Factory")
cdk.Tags.of(app).add("Project", "ServerlessFactory")
cdk.Tags.of(app).add("Owner", "DevOps-Team")

if target_env == "prod":
    cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
    
"""ERROR IN CDK NAG WITH VERBOSE=False"""
# else:
#     cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=False))



app.synth()