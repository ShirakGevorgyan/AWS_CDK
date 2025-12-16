from aws_cdk import (
    RemovalPolicy,
    aws_cognito as cognito
)
from constructs import Construct

class StandardUserPool(Construct):
    def __init__(self, 
                    scope: Construct, 
                    id: str,
                    self_signup: bool,
                    mfa_enforcement: str,
                    password_length: int,
                    retain_on_delete: bool
                    ):
        super().__init__(scope, id)

        removal_policy = RemovalPolicy.RETAIN if retain_on_delete else RemovalPolicy.DESTROY

        mfa_config = cognito.Mfa.OFF
        if mfa_enforcement == "REQUIRED":
            mfa_config = cognito.Mfa.REQUIRED
        elif mfa_enforcement == "OPTIONAL":
            mfa_config = cognito.Mfa.OPTIONAL

        self.user_pool = cognito.UserPool(
            self, "Resource",
            user_pool_name=f"{id}-Pool",
            
            self_sign_up_enabled=self_signup,
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            
            password_policy=cognito.PasswordPolicy(
                min_length=password_length,
                require_digits=True,
                require_symbols=True,
                require_lowercase=True,
                require_uppercase=True
            ),

            mfa=mfa_config,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=False,
                otp=True
            ),

            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            
            removal_policy=removal_policy
        )
        
        self.client = self.user_pool.add_client(
            "AppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )