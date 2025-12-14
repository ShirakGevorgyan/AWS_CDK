import aws_cdk as core
import aws_cdk.assertions as assertions

from serverless_factory.serverless_factory_stack import ServerlessFactoryStack

# example tests. To run these tests, uncomment this file along with the example
# resource in serverless_factory/serverless_factory_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServerlessFactoryStack(app, "serverless-factory")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
