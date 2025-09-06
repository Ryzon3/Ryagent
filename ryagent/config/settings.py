"""Configuration settings for RyAgent."""

from pathlib import Path

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for an LLM model."""

    name: str
    display_name: str
    provider: str = "openai"
    max_tokens: int = 4000
    temperature: float = 0.7
    enabled: bool = True


class UIConfig(BaseModel):
    """UI configuration settings."""

    theme: str = "light"
    sidebar_collapsed: bool = False
    show_model_in_tabs: bool = True
    max_tabs: int = 20


class Settings(BaseModel):
    """Application settings."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000

    # Authentication
    auth_token: str | None = None

    # Templates and static files
    templates_dir: Path = Path(__file__).parent.parent / "templates"
    static_dir: Path = Path(__file__).parent.parent / "app" / "static"

    # Security
    allowed_hosts: list[str] = ["127.0.0.1", "localhost"]

    # Development
    debug: bool = False

    # Models configuration
    models: list[ModelConfig] = Field(
        default_factory=lambda: [
            ModelConfig(
                name="gpt-4o-mini",
                display_name="GPT-4o Mini",
                provider="openai",
                max_tokens=4000,
                temperature=0.7,
            ),
            ModelConfig(
                name="gpt-4o",
                display_name="GPT-4o",
                provider="openai",
                max_tokens=4000,
                temperature=0.7,
            ),
            ModelConfig(
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                provider="openai",
                max_tokens=4000,
                temperature=0.7,
            ),
        ]
    )

    # UI configuration
    ui: UIConfig = Field(default_factory=UIConfig)

    # Default system prompts
    default_system_prompt: str = "You are a helpful assistant."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Generate auth token if not provided
        if not self.auth_token:
            self.auth_token = self._get_or_create_token()

    def _get_or_create_token(self) -> str:
        """Get existing token or create a new one."""
        token_file = Path.home() / ".ryagent" / "token"

        if token_file.exists():
            return token_file.read_text().strip()

        # Create new token
        import secrets

        token = secrets.token_urlsafe(32)

        # Ensure directory exists
        token_file.parent.mkdir(exist_ok=True)
        token_file.write_text(token)
        token_file.chmod(0o600)  # Readable only by owner

        return token

    def get_enabled_models(self) -> list[ModelConfig]:
        """Get list of enabled models."""
        return [model for model in self.models if model.enabled]

    def get_model_by_name(self, name: str) -> ModelConfig | None:
        """Get model configuration by name."""
        for model in self.models:
            if model.name == name:
                return model
        return None


# Global settings instance
settings = Settings()
