import os
import toml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv


@dataclass
class AppConfig:
    workspace: str = field(default_factory=lambda: os.getcwd())


@dataclass 
class ModelConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    api_key: Optional[str] = None


@dataclass
class AgentConfig:
    system_prompt: str = "You are a helpful coding and ops agent."
    authorized_tools: List[str] = field(default_factory=lambda: ["shell_run", "fs_read", "fs_write"])


@dataclass
class ToolConfig:
    allow: List[str] = field(default_factory=list)
    deny: List[str] = field(default_factory=list)


@dataclass
class Config:
    app: AppConfig = field(default_factory=AppConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    tools: Dict[str, ToolConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        config = cls()
        
        if "app" in data:
            app_data = data["app"]
            config.app = AppConfig(
                workspace=app_data.get("workspace", config.app.workspace)
            )
        
        if "models" in data and "default" in data["models"]:
            model_data = data["models"]["default"]
            config.model = ModelConfig(
                provider=model_data.get("provider", config.model.provider),
                model=model_data.get("model", config.model.model),
                max_tokens=model_data.get("max_tokens", config.model.max_tokens),
                api_key=model_data.get("api_key", config.model.api_key)
            )
        
        if "agents" in data and "default" in data["agents"]:
            agent_data = data["agents"]["default"]
            config.agent = AgentConfig(
                system_prompt=agent_data.get("system_prompt", config.agent.system_prompt),
                authorized_tools=agent_data.get("authorized_tools", config.agent.authorized_tools)
            )
        
        if "tools" in data:
            tools_data = data["tools"]
            for tool_name, tool_config in tools_data.items():
                config.tools[tool_name] = ToolConfig(
                    allow=tool_config.get("allow", []),
                    deny=tool_config.get("deny", [])
                )
        
        return config

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        # Load environment variables from .env file
        load_dotenv()
        
        if config_path is None:
            config_path = cls._find_config_file()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = toml.load(f)
                config = cls.from_dict(data)
                
                if not config.model.api_key:
                    config.model.api_key = os.getenv("OPENAI_API_KEY")
                
                return config
            except Exception as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")
                return cls._default_config()
        else:
            return cls._default_config()

    @classmethod
    def _find_config_file(cls) -> Optional[str]:
        search_paths = [
            "config.toml",
            "ryagent.toml",
            os.path.expanduser("~/.config/ryagent/config.toml"),
            os.path.expanduser("~/.ryagent.toml")
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None

    @classmethod
    def _default_config(cls) -> "Config":
        # Load environment variables from .env file
        load_dotenv()
        
        config = cls()
        config.model.api_key = os.getenv("OPENAI_API_KEY")
        
        config.tools["shell_run"] = ToolConfig(
            allow=["python", "uv", "ls", "cat", "rg", "git", "pytest"],
            deny=["rm", "shutdown", "reboot", "mkfs"]
        )
        
        return config

    def save(self, config_path: str):
        config_dict = {
            "app": {
                "workspace": self.app.workspace
            },
            "models": {
                "default": {
                    "provider": self.model.provider,
                    "model": self.model.model,
                    "max_tokens": self.model.max_tokens
                }
            },
            "agents": {
                "default": {
                    "system_prompt": self.agent.system_prompt,
                    "authorized_tools": self.agent.authorized_tools
                }
            },
            "tools": {}
        }
        
        for tool_name, tool_config in self.tools.items():
            config_dict["tools"][tool_name] = {
                "allow": tool_config.allow,
                "deny": tool_config.deny
            }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            toml.dump(config_dict, f)


def load_config(config_path: Optional[str] = None) -> Config:
    return Config.load(config_path)