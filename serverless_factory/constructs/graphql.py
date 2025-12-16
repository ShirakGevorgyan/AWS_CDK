from aws_cdk import (
    aws_appsync as appsync,
    aws_lambda as _lambda,
    aws_cognito as cognito,
    aws_logs as logs,
    Expiration,
    Duration
)
from constructs import Construct

class StandardGraphQLApi(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str,
                    data_source_function: _lambda.Function,
                    auth_mode: str,
                    user_pool: cognito.IUserPool = None,
                    enable_logging: bool = True,
                    enable_xray: bool = True
                    ):
        super().__init__(scope, id)

        auth_config = None
        
        if auth_mode == "USER_POOL":
            if not user_pool:
                raise ValueError("❌ GraphQL Error: Auth mode is 'USER_POOL' but no Cognito Pool provided!")
                
            auth_config = appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.USER_POOL,
                    user_pool_config=appsync.UserPoolConfig(user_pool=user_pool)
                )
            )
        else:
            auth_config = appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY,
                    api_key_config=appsync.ApiKeyConfig(
                        expires=Expiration.after(Duration.days(365))
                    )
                )
            )

        log_config = None
        if enable_logging:
            log_config = appsync.LogConfig(
                field_log_level=appsync.FieldLogLevel.ALL,
                retention=logs.RetentionDays.ONE_WEEK,
                exclude_verbose_content=False
            )

        self.api = appsync.GraphqlApi(
            self, "Resource",
            name=f"{id}-API",
            schema=appsync.SchemaFile.from_asset("graphql/schema.graphql"),
            authorization_config=auth_config,
            log_config=log_config,
            xray_enabled=enable_xray
        )

        ds = self.api.add_lambda_data_source("LambdaDS", data_source_function)

        ds.create_resolver("GetItemResolver", type_name="Query", field_name="getItem")
        ds.create_resolver("ListItemsResolver", type_name="Query", field_name="listItems")