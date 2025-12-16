import json
import os
import re
from dataclasses import dataclass
from typing import List, Any, Dict

@dataclass
class ResourceConfig:
    type: str
    id: str
    config: Dict[str, Any]

@dataclass
class ProjectConfig:
    project_name: str
    version: str 
    resources: List[ResourceConfig]

class ConfigLoader:
    @staticmethod
    def load(filename: str) -> ProjectConfig:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"❌ Config Error: Configuration file '{filename}' was not found in {os.getcwd()}")

        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Config Error: The file '{filename}' contains invalid JSON.\nError: {e}")

        required_keys = ["project_name", "resources"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"❌ Config Error: Missing required field '{key}' in {filename}")
        resources = []
        for idx, r in enumerate(data.get("resources", [])):
            
            if "type" not in r or "id" not in r:
                raise ValueError(f"❌ Config Error: Resource at index {idx} is missing 'type' or 'id'.")

            if not re.match(r'^[a-zA-Z0-9]+$', r["id"]):
                raise ValueError(f"❌ Config Error: Resource ID '{r['id']}' must contain ONLY letters and numbers (Alphanumeric). No spaces or symbols allowed.")

            # Default config, եթե դատարկ է
            r_config = r.get("config", {})

            resources.append(ResourceConfig(
                type=r["type"],
                id=r["id"],
                config=r_config
            ))
        
        # Վերադարձնում ենք մաքուր օբյեկտը
        return ProjectConfig(
            project_name=data["project_name"],
            version=data.get("version", "1.0.0"),
            resources=resources
        )