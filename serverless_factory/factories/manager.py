from constructs import Construct
from aws_cdk import aws_lambda_event_sources as events

from ..config.presets import ENVIRONMENT_PROFILES
from ..constructs.storage import SecureBucket
from ..constructs.compute import StandardFunction
from ..constructs.messaging import StandardQueue, StandardTopic
from ..constructs.database import StandardTable
from ..constructs.identity import StandardUserPool
from ..constructs.analytics import DataStream
from ..constructs.scheduler import CronJob
from ..constructs.networking import StandardVpc
from ..constructs.containers import ContainerRepo, K8sCluster
from ..constructs.relational_db import AuroraDB
from ..constructs.security import CustomRole
from ..constructs.workflow import StandardWorkflow
from ..constructs.graphql import StandardGraphQLApi
from ..constructs.data_warehouse import DataLakeAnalytics
from ..constructs.security_mgmt import SecurePlatformTools
from ..constructs.cdn import CdnDistribution


class ResourceManager(Construct):
    def __init__(self, scope: Construct, id: str, resource_conf, env_name="dev", dashboard=None, global_vpc=None):
        super().__init__(scope, id)

        self.env_name = env_name
        self.dashboard = dashboard
        self.defaults = ENVIRONMENT_PROFILES.get(env_name, ENVIRONMENT_PROFILES["dev"])
        self.json_config = resource_conf.config

        resource_map = {
            "data_ingestion": self.create_ingestion,
            "backend_api":    self.create_backend,
            "archive_store":  self.create_archive,
            "async_job":      self.create_async_job,
            "auth_provider":  self.create_auth,
            "data_stream":    self.create_stream,
            "scheduled_task": self.create_cron,
            "virtual_network": self.create_vpc,
            "container_repo":  self.create_ecr,
            "k8s_cluster":     self.create_eks,
            "sql_database":    self.create_rds,
            "iam_role":        self.create_role,
            "workflow_engine": self.create_workflow,
            "graphql_api":     self.create_graphql,
            "data_analytics":  self.create_analytics,
            "secret_storage":  self.create_secrets,
            "web_firewall":    self.create_waf,
            "content_delivery": self.create_cdn
        }

        t = resource_conf.type
        if t in resource_map:
            resource_map[t](resource_conf)
        else:
            raise ValueError(f"⚠️ Unknown Resource Type: '{t}'")
        
    def _get_val(self, category, key):
        if key in self.json_config:
            return self.json_config[key]
        return self.defaults[category].get(key)

    def create_ingestion(self, conf):
        self._create_bucket_resource(conf, "Store")

    def create_archive(self, conf):
        self._create_bucket_resource(conf, "Archive")


    def _create_bucket_resource(self, conf, resource_id, force_cors=None):
        
        retention = self._get_val("storage", "retention_days")
        transition = self._get_val("storage", "transition_days")
        versioning = self._get_val("storage", "versioned")
        logging = self._get_val("storage", "access_logging")
        kms = self._get_val("storage", "use_kms")
        events = self._get_val("storage", "event_bridge")
        obj_lock = self._get_val("storage", "object_lock")
        
        cors = force_cors if force_cors is not None else self._get_val("storage", "cors_enabled")

        bucket_construct = SecureBucket(
            self, resource_id,
            retention_days=retention,
            transition_days=transition,
            versioned=versioning,
            access_logging=logging,
            cors_enabled=cors,
            use_kms=kms,
            event_bridge=events,
            object_lock=obj_lock
        )
        
        return bucket_construct
    
    def create_backend(self, conf):
        mem = self._get_val("compute", "memory")
        time = self._get_val("compute", "timeout")
        trace = self._get_val("compute", "tracing")
        arch_str = self._get_val("compute", "architecture")
        log_days = self._get_val("compute", "log_retention")
        concurrency = self._get_val("compute", "reserved_concurrency")
        
        is_arm = True if arch_str == "ARM64" else False

        use_vpc = conf.config.get("use_vpc", False)
        target_vpc = None
        if use_vpc:
            target_vpc = getattr(self.node.scope, "global_vpc", None)
            if not target_vpc:
                print(f"⚠️ Warning: {conf.id} requested VPC, but no VPC was created.")

        fn = StandardFunction(
            self, "ApiHandler", 
            handler="handler.main",
            memory=mem,
            timeout_sec=time,
            tracing=trace,
            use_arm=is_arm,
            log_retention=log_days,
            vpc=target_vpc,
            reserved_concurrency=concurrency
        )

        need_db = conf.config.get("database", False)

        if need_db:
            backup = self._get_val("nosql", "enable_backup")
            protect = self._get_val("nosql", "deletion_protection")
            kms = self._get_val("nosql", "use_kms")
            stream = self._get_val("nosql", "stream")

            table = StandardTable(
                self, 
                f"{conf.id}Table",
                partition_key="id",
                sort_key=conf.config.get("sort_key"),
                
                enable_backup=backup,
                deletion_protection=protect,
                use_kms=kms,
                stream=stream
            )
            
            table.table.grant_read_write_data(fn.function)
            
            fn.function.add_environment("TABLE_NAME", table.table.table_name)
            
            print(f"      + Added DynamoDB Table for {conf.id}")
        
    def create_async_job(self, conf):
        mem = self._get_val("compute", "memory")
        time = self._get_val("compute", "timeout")
        trace = self._get_val("compute", "tracing")
        arch_str = self._get_val("compute", "architecture")
        log_days = self._get_val("compute", "log_retention")
        
        is_arm = True if arch_str == "ARM64" else False

        use_vpc = conf.config.get("use_vpc", False)
        target_vpc = getattr(self.node.scope, "global_vpc", None) if use_vpc else None

        is_fifo = self._get_val("messaging", "fifo")
        ret_days = self._get_val("messaging", "retention_days")
        is_enc = self._get_val("messaging", "encrypted")
        vis_timeout = self._get_val("messaging", "visibility_timeout")

        if vis_timeout < time:
            print(f"⚠️ Fixing config: Increasing SQS visibility to match Lambda timeout ({time}s)")
            vis_timeout = time

        topic = StandardTopic(self, "Notifier", fifo=is_fifo, encrypted=is_enc)
        
        queue = StandardQueue(
            self, "JobQueue", 
            fifo=is_fifo, 
            retention_days=ret_days, 
            encrypted=is_enc, 
            visibility_timeout=vis_timeout
        )
        
        topic.subscribe_queue(queue)
        
        worker = StandardFunction(
            self, 
            "Worker", 
            handler="handler.main",
            memory=mem,
            timeout_sec=time,
            tracing=trace,
            use_arm=is_arm,
            log_retention=log_days,
            vpc=target_vpc,
            env={"QUEUE_URL": queue.queue.queue_url}
        )
        
        worker.function.add_event_source(
            events.SqsEventSource(queue.queue, batch_size=1)
        )
        
        print(f"      + Added Async Job (FIFO={is_fifo}, Encrypted={is_enc}, VPC={bool(target_vpc)}) for {conf.id}")
        
        
        
        
    def create_workflow(self, conf):
        mem = self._get_val("compute", "memory")
        time = self._get_val("compute", "timeout")
        trace_lambda = self._get_val("compute", "tracing")
        arch_str = self._get_val("compute", "architecture")
        log_days = self._get_val("compute", "log_retention")
        is_arm = True if arch_str == "ARM64" else False

        use_vpc = conf.config.get("use_vpc", False)
        target_vpc = getattr(self.node.scope, "global_vpc", None) if use_vpc else None

        worker_fn = StandardFunction(
            self, 
            "WorkflowWorker", 
            handler="handler.main",
            memory=mem, timeout_sec=time, tracing=trace_lambda,
            use_arm=is_arm, log_retention=log_days, vpc=target_vpc
        )

        sf_timeout = self._get_val("workflow", "timeout_minutes")
        is_express = self._get_val("workflow", "express_mode")
        sf_logging = self._get_val("workflow", "logging")
        sf_tracing = self._get_val("workflow", "tracing")

        StandardWorkflow(
            self, "Workflow", 
            worker_function=worker_fn.function,
            timeout_minutes=sf_timeout,
            use_express_type=is_express,
            enable_logging=sf_logging,
            enable_tracing=sf_tracing
        )
        
        type_str = "EXPRESS" if is_express else "STANDARD"
        print(f"      + Added Step Functions ({type_str}) for {conf.id}")
        
    
    def create_vpc(self, conf):
        cidr = self._get_val("network", "cidr")
        azs = self._get_val("network", "max_azs")
        nats = self._get_val("network", "nat_gateways")
        s3_end = self._get_val("network", "s3_endpoint")
        dynamo_end = self._get_val("network", "dynamo_endpoint")

        net = StandardVpc(
            self, "Network", 
            cidr=cidr,
            max_azs=azs,
            nat_gateways=nats,
            use_s3_endpoint=s3_end,
            use_dynamo_endpoint=dynamo_end
        )
        
        self.node.scope.global_vpc = net.vpc 
        
        print(f"      + Added VPC ({cidr}, AZs={azs}, NATs={nats})")
        
        
    def create_rds(self, conf):
        vpc = getattr(self.node.scope, "global_vpc", None)
        if not vpc:
            raise Exception("❌ RDS Error: No VPC found! Make sure 'virtual_network' is listed BEFORE database in JSON.")

        min_cap = self._get_val("rds", "min_acu")
        max_cap = self._get_val("rds", "max_acu")
        bkp_days = self._get_val("rds", "backup_days")
        protect = self._get_val("rds", "deletion_protection")
        insights = self._get_val("rds", "insights")
        mon_interval = self._get_val("rds", "monitoring_interval")

        AuroraDB(
            self, "Database", 
            vpc=vpc, 
            min_capacity=min_cap, 
            max_capacity=max_cap,
            backup_retention_days=bkp_days,
            deletion_protection=protect,
            enable_insights=insights,
            monitoring_interval=mon_interval
        )
        
        print(f"      + Added Aurora Serverless DB for {conf.id}")
        
    
    def create_ecr(self, conf):
        scan = self._get_val("containers", "scan_on_push")
        count = self._get_val("containers", "max_images")
        immutable = self._get_val("containers", "immutable_tags")

        ContainerRepo(
            self, "Registry", 
            scan_on_push=scan,
            max_image_count=count,
            immutable_tags=immutable
        )
        print(f"      + Added ECR (Max {count} images)")

    def create_eks(self, conf):
        vpc = getattr(self.node.scope, "global_vpc", None)
        if not vpc:
            raise Exception("❌ EKS Error: No VPC found! Please add 'virtual_network' to JSON first.")
            
        inst_type = self._get_val("containers", "instance_type")
        min_n = self._get_val("containers", "min_nodes")
        max_n = self._get_val("containers", "max_nodes")
        logs = self._get_val("containers", "logging")
        pub_access = self._get_val("containers", "public_access")

        K8sCluster(
            self, "Cluster", 
            vpc=vpc,
            instance_type=inst_type,
            min_size=min_n,
            max_size=max_n,
            enable_logging=logs,
            public_access=pub_access
        )
        print(f"      + Added EKS Cluster ({inst_type}, Nodes: {min_n}-{max_n})")
        
        
    def create_role(self, conf):
        service = conf.config.get("service", "lambda.amazonaws.com")
        
        boundary = self._get_val("security", "permissions_boundary_arn")
        duration = self._get_val("security", "session_duration")
        
        defaults = self._get_val("security", "default_policies") or []
        extras = conf.config.get("managed_policies", [])
        combined_policies = list(set(defaults + extras))

        CustomRole(
            self, "Role",
            service_principal=service,
            boundary_arn=boundary,
            max_session_duration=duration,
            managed_policy_names=combined_policies
        )
        
        print(f"      + Added IAM Role for {conf.id} (Service: {service})")
        
        
        
    def create_stream(self, conf):
        shards = self._get_val("analytics", "shards")
        on_demand = self._get_val("analytics", "on_demand")
        hours = self._get_val("analytics", "retention_hours")
        is_enc = self._get_val("analytics", "encrypt")

        DataStream(
            self, "Stream", 
            shard_count=shards,
            is_on_demand=on_demand,
            retention_hours=hours,
            encrypt=is_enc
        )
        
        mode_str = "On-Demand" if on_demand else f"Provisioned ({shards} shards)"
        print(f"      + Added Kinesis Stream ({mode_str}, {hours}h retention)")
        
        
        
    def create_cron(self, conf):
        mem = self._get_val("compute", "memory")
        time = self._get_val("compute", "timeout")
        trace = self._get_val("compute", "tracing")
        arch_str = self._get_val("compute", "architecture")
        log_days = self._get_val("compute", "log_retention")
        is_arm = True if arch_str == "ARM64" else False

        fn = StandardFunction(
            self, "TaskRunner", 
            handler="handler.main",
            memory=mem, timeout_sec=time, tracing=trace,
            use_arm=is_arm, log_retention=log_days
        )
        
        rate = conf.config.get("rate_minutes", 60)
        
        is_enabled = self._get_val("scheduler", "enabled")
        retries = self._get_val("scheduler", "retries")
        use_dlq = self._get_val("scheduler", "use_dlq")

        CronJob(
            self, "Scheduler", 
            rate_minutes=rate, 
            target_fn=fn.function,
            enabled=is_enabled,
            retry_attempts=retries,
            create_dlq=use_dlq
        )
        
        status = "ENABLED" if is_enabled else "DISABLED"
        print(f"      + Added Cron Job ({status}, Every {rate} mins) for {conf.id}")
        
        
        
    def create_auth(self, conf):
        signup = self._get_val("identity", "self_signup")
        mfa = self._get_val("identity", "mfa")
        pass_len = self._get_val("identity", "password_length")
        retain = self._get_val("identity", "retain")

        auth_construct = StandardUserPool(
            self, 
            "Users",
            self_signup=signup,
            mfa_enforcement=mfa,
            password_length=pass_len,
            retain_on_delete=retain
        )
        
        self.node.scope.global_user_pool = auth_construct.user_pool
        
        print(f"      + Added Auth (Cognito) [MFA: {mfa}] - Registered Globally")

    def create_graphql(self, conf):
        mem = self._get_val("compute", "memory")
        time = self._get_val("compute", "timeout")
        trace = self._get_val("compute", "tracing")
        arch_str = self._get_val("compute", "architecture")
        log_days = self._get_val("compute", "log_retention")
        
        is_arm = True if arch_str == "ARM64" else False

        use_vpc = conf.config.get("use_vpc", False)
        target_vpc = getattr(self.node.scope, "global_vpc", None) if use_vpc else None

        auth_mode = self._get_val("graphql", "auth_type")
        do_log = self._get_val("graphql", "logging")
        do_xray = self._get_val("graphql", "xray")

        target_pool = None
        if auth_mode == "USER_POOL":
            target_pool = getattr(self.node.scope, "global_user_pool", None)
            
            if not target_pool:
                raise Exception(
                    "❌ GraphQL Error: Auth mode is 'USER_POOL', but no Auth Provider found! "
                    "Make sure 'auth_provider' is listed BEFORE 'graphql_api' in pipelines.json."
                )

        handler_fn = StandardFunction(
            self, 
            "GraphQLDataSource", 
            handler="handler.main",
            memory=mem,
            timeout_sec=time,
            tracing=trace,
            use_arm=is_arm,
            log_retention=log_days,
            vpc=target_vpc
        )

        StandardGraphQLApi(
            self, 
            "GraphQLApi",
            data_source_function=handler_fn.function,
            auth_mode=auth_mode,
            user_pool=target_pool,
            enable_logging=do_log,
            enable_xray=do_xray
        )
        
        print(f"      + Added GraphQL API (Auth: {auth_mode}, X-Ray: {do_xray})")
        
        
    def create_analytics(self, conf):
        vpc = getattr(self.node.scope, "global_vpc", None)
        if not vpc:
            raise Exception("❌ Analytics Error: Redshift requires a VPC! Add 'virtual_network' to JSON first.")

        r_node_type = self._get_val("warehouse", "node_type")
        r_nodes = self._get_val("warehouse", "nodes")
        r_public = self._get_val("warehouse", "public")

        data_bucket_construct = self._create_bucket_resource(conf, "AnalyticsDataStore")
        
        DataLakeAnalytics(
            self, "Analytics",
            data_bucket=data_bucket_construct.bucket,
            vpc=vpc,
            node_type_id=r_node_type,
            number_of_nodes=r_nodes,
            publicly_accessible=r_public
        )
        
        print(f"      + Added Data Lake (Athena + Redshift {r_nodes}x{r_node_type}) for {conf.id}")
        
        
    def create_cdn(self, conf):
        price = self._get_val("cdn", "price_class")
        blocked_countries = self._get_val("cdn", "geo_block")
        
        content_bucket_construct = self._create_bucket_resource(
            conf, "CDNContent", force_cors=True
        )

        log_bucket_construct = self._create_bucket_resource(
            conf, "CDNLogs", force_cors=False
        )

        CdnDistribution(
            self, "CDN",
            content_bucket=content_bucket_construct.bucket,
            log_bucket=log_bucket_construct.bucket,
            price_class_str=price,
            geo_locations=blocked_countries,
            web_acl_id=None 
        )
        
        print(f"      + Added CloudFront CDN (PriceClass: {price}) for {conf.id}")
        
        
    def create_secrets(self, conf):
        length = self._get_val("waf_secrets", "secret_length")

        SecurePlatformTools(
            self, "Secrets",
            waf_scope="REGIONAL", rate_limit=100, enable_managed_rules=False,
            secret_length=length
        )
        print(f"      + Added Secrets Manager ({length} chars) for {conf.id}")

    def create_waf(self, conf):
        scope = self._get_val("waf_secrets", "waf_scope")
        limit = self._get_val("waf_secrets", "rate_limit")
        managed = self._get_val("waf_secrets", "managed_rules")
        
        SecurePlatformTools(
            self, "Firewall",
            waf_scope=scope,
            rate_limit=limit,
            enable_managed_rules=managed,
            secret_length=20
        )
        
        print(f"      + Added WAF ({scope}, RateLimit={limit}, Managed={managed}) for {conf.id}")