
ENVIRONMENT_PROFILES = {
    "dev": {
        "storage": {
            "retention_days": 7,
            "transition_days": 0,
            "versioned": False,
            "access_logging": False,
            "cors_enabled": True,
            "use_kms": False,
            "event_bridge": True,
            "object_lock": False
        },
        "compute": {
            "memory": 128,
            "timeout": 10,
            "architecture": "ARM64",
            "tracing": False,
            "log_retention": 1,
            "reserved_concurrency": None
        },
        "nosql": {
            "enable_backup": False,
            "deletion_protection": False,
            "use_kms": False,
            "stream": True
        },
        "network": {
            "cidr": "10.0.0.0/16",
            "max_azs": 2,
            "nat_gateways": 1,
            "s3_endpoint": True,
            "dynamo_endpoint": True
        },
        "rds": {
            "min_acu": 0.5,
            "max_acu": 1.0,
            "backup_days": 1,
            "deletion_protection": False,
            "insights": False,
            "monitoring_interval": 0
        },
        "containers": {

            "scan_on_push": False,
            "max_images": 5,
            "immutable_tags": False,
            

            "instance_type": "t3.medium",
            "min_nodes": 1,
            "max_nodes": 2,
            "logging": False,
            "public_access": True
        },
        "security": {
            "permissions_boundary_arn": None,
            "session_duration": 3600,
            "default_policies": [
                "service-role/AWSLambdaBasicExecutionRole"
            ]
        },
        "messaging": {
            "fifo": False,
            "retention_days": 4,
            "encrypted": False,
            "visibility_timeout": 30
        },
        "analytics": {
            "on_demand": False,
            "shards": 1,
            "retention_hours": 24,
        },
        "identity": {
            "self_signup": True,
            "mfa": "OFF",
            "password_length": 6,
            "retain": False
        },
        "scheduler": {
            "enabled": True,
            "retries": 0,
            "use_dlq": False
        },
        "workflow": {
            "timeout_minutes": 5,
            "express_mode": True,
            "logging": True,
            "tracing": False
        },
        "graphql": {
            "auth_type": "API_KEY",
            "logging": True,
            "xray": False
        },
        "warehouse": {
            "node_type": "dc2.large",
            "nodes": 2,
            "public": False
        },
        "cdn": {
            "price_class": "100",
            "geo_block": [],
            "waf_enabled": False
        },
        "waf_secrets": {
            "waf_scope": "REGIONAL",
            "rate_limit": 500,
            "managed_rules": False,
            "secret_length": 16
        }
    },
    
    
    "prod": {
        "storage": {
            "retention_days": 365,
            "transition_days": 90,
            "versioned": True,
            "access_logging": True,
            "cors_enabled": False,
            "use_kms": True,
            "event_bridge": True,
            "object_lock": True
        },
        "compute": {
            "memory": 1024,
            "timeout": 60,
            "architecture": "X86_64",
            "tracing": True,
            "log_retention": 30,
            "reserved_concurrency": 100
        },
        "nosql": {
            "enable_backup": True,
            "deletion_protection": True,
            "use_kms": True,
            "stream": True
        },
        "network": {
            "cidr": "10.10.0.0/16",
            "max_azs": 3,
            "nat_gateways": 3,
            "s3_endpoint": True,
            "dynamo_endpoint": True
        },
        "rds": {
            "min_acu": 2.0,
            "max_acu": 16.0,
            "backup_days": 30,
            "deletion_protection": True,
            "insights": True,
            "monitoring_interval": 60
        },
        "containers": {
            
            "scan_on_push": True,
            "max_images": 50,
            "immutable_tags": True,
            

            "instance_type": "m5.large",
            "min_nodes": 2,
            "max_nodes": 10,
            "logging": True,
            "public_access": True
        },
        "security": {

            "permissions_boundary_arn": None, 
            
            "session_duration": 43200,
            "default_policies": [
                "service-role/AWSLambdaBasicExecutionRole",
                "AWSXRayDaemonWriteAccess"
            ]
        },
        "messaging": {
            "fifo": True,
            "retention_days": 14,
            "encrypted": True,
            "visibility_timeout": 300
        },
        "analytics": {
            "on_demand": True,
            "shards": 1,
            "retention_hours": 168,
            "encrypt": True
        },
        "identity": {
            "self_signup": False,
            "mfa": "OPTIONAL",
            "password_length": 12,
            "retain": True
        },
        "scheduler": {
            "enabled": True,
            "retries": 2,
            "use_dlq": True
        },
        "workflow": {
            "timeout_minutes": 60,
            "express_mode": False,
            "logging": True,
            "tracing": True
        },
        "graphql": {
            "auth_type": "USER_POOL",
            "logging": True,
            "xray": True
        },
        "warehouse": {
            "node_type": "ra3.xlplus",
            "nodes": 2,
            "public": False
        },
        "cdn": {
            "price_class": "ALL",
            "geo_block": ["KP", "IR"],
            "waf_enabled": True
        },
        "waf_secrets": {
            "waf_scope": "REGIONAL",
            "rate_limit": 2000,
            "managed_rules": True,
            "secret_length": 32
        }
    }
}