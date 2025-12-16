from aws_cdk import (
    aws_secretsmanager as secretsmanager,
    aws_wafv2 as wafv2,
    RemovalPolicy
)
from constructs import Construct

class SecurePlatformTools(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str, 
                    waf_scope: str,
                    rate_limit: int,
                    enable_managed_rules: bool,
                    secret_length: int = 32
                    ):
        super().__init__(scope, id)

        self.db_secret = secretsmanager.Secret(
            self, "DBPassword",
            secret_name=f"{id}-Secret",
            description="Auto-generated secure password",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                password_length=secret_length,
                exclude_punctuation=True,
                exclude_characters='"@/' 
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        rules = []
        priority_counter = 0

        rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name="RateLimitRule",
                priority=priority_counter,
                action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                statement=wafv2.CfnWebACL.StatementProperty(
                    rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                        limit=rate_limit,
                        aggregate_key_type="IP"
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    cloud_watch_metrics_enabled=True,
                    metric_name=f"{id}-RateLimit",
                    sampled_requests_enabled=True
                )
            )
        )
        priority_counter += 1

        if enable_managed_rules:
            rules.append(
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-CommonRuleSet",
                    priority=priority_counter,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesCommonRuleSet",
                            vendor_name="AWS"
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name=f"{id}-CommonRules",
                        sampled_requests_enabled=True
                    )
                )
            )

        self.web_acl = wafv2.CfnWebACL(
            self, "WebACL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope=waf_scope, 
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name=f"{id}-MainMetrics",
                sampled_requests_enabled=True
            ),
            rules=rules
        )