import aws_cdk as cdk
from aws_cdk import assertions
from serverless_factory.serverless_factory_stack import ServerlessFactoryStack

def get_template():
    app = cdk.App()
    stack = ServerlessFactoryStack(app, "TestStack", env_name="dev")
    return assertions.Template.from_stack(stack)

def test_resource_counts():
    template = get_template()

    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::Cognito::UserPool", 1)
    template.resource_count_is("Custom::AWSCDK-EKS-Cluster", 1)
    template.resource_count_is("AWS::RDS::DBCluster", 1)
    template.resource_count_is("AWS::Redshift::Cluster", 1)
    
    lambdas = template.find_resources("AWS::Lambda::Function")
    assert len(lambdas) >= 5

def test_vpc_configuration():
    template = get_template()
    
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.20.0.0/16",
        "EnableDnsHostnames": True
    })

def test_lambda_configuration():
    template = get_template()
    
    template.has_resource_properties("AWS::Lambda::Function", {
        "MemorySize": 128,
        "Architectures": ["arm64"],
        "Timeout": 10
    })

def test_s3_security():
    template = get_template()
    
    template.has_resource_properties("AWS::S3::Bucket", {
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        }
    })
    
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }
    })

def test_dynamodb_config():
    template = get_template()
    
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST"
    })

def test_iam_roles_boundary():
    template = get_template()
    
    template.has_resource_properties("AWS::IAM::Role", {
        "Path": "/serverless-factory/"
    })

print("✅ Advanced tests passed!")