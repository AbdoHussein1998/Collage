from dataclasses import dataclass, asdict
from typing import Optional, Final, Dict, Any
from langchain.chat_models import init_chat_model
import loguru

import asyncio


# =========================================================
# 1. Config Dataclass
# =========================================================

@dataclass
class ModelConfig:
    """Holds LLM model behavior parameters."""

    model: str = "llama3"
    model_provider: str = "ollama"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    max_retries: int = 2

    def __post_init__(self):
        """Sanitize and validate inputs."""
        if not isinstance(self.model, str):
            raise TypeError(f"model must be a string, got {type(self.model)}")
        if not isinstance(self.model_provider, str):
            raise TypeError(
                f"model_provider must be a string, got {type(self.model_provider)}"
            )

        self.model = self.model.strip().lower()
        self.model_provider = self.model_provider.strip().lower()

        if not self.model:
            raise ValueError("model cannot be empty")
        if not self.model_provider:
            raise ValueError("model_provider cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, removing None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


# =========================================================
# 2. Generation Factory
# =========================================================

class GenerationFactory:
    """Factory class for creating LLM instances."""

    SUPPORTED_PROVIDERS: Final[frozenset[str]] = frozenset({
        "openai",
        "azure_openai",
        "anthropic",
        "google_vertexai",
        "google_genai",
        "bedrock",
        "cohere",
        "fireworks",
        "together",
        "mistralai",
        "huggingface",
        "groq",
        "ollama",
    })

    @classmethod
    def _validate_config(
        cls,
        model_config: ModelConfig,
        logger: Logger,
    ) -> None:
        """Validate ModelConfig instance."""

        if not isinstance(model_config, ModelConfig):
            raise TypeError(
                f"model_config must be a ModelConfig instance, got {type(model_config)}"
            )

        if model_config.model_provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider: '{model_config.model_provider}'. "
                f"Supported providers: {', '.join(sorted(cls.SUPPORTED_PROVIDERS))}"
            )

        logger.debug(
            "Config validated | provider='{}', model='{}'",
            model_config.model_provider,
            model_config.model,
        )

    @classmethod
    async def create_llm(
        cls,
        model_config: Optional[ModelConfig] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        logger: Optional[loguru._logger.Logger] = None,
    ):
        """Create an LLM instance with provided configuration."""

        logger = logger or loguru.logger
        model_config = model_config or ModelConfig()

        logger.info(
            "Creating LLM | provider='{}', model='{}'",
            model_config.model_provider,
            model_config.model,
        )

        # --- Validate ---
        try:
            cls._validate_config(model_config, logger)
        except (TypeError, ValueError) as e:
            logger.error("Validation failed: {}", str(e))
            raise

        # --- Build kwargs (clean one-liner!) ---
        kwargs = model_config.to_dict()

        if api_key:
            kwargs["api_key"] = api_key
            logger.debug("API key provided")
        if base_url:
            kwargs["base_url"] = base_url
            logger.debug("Custom base URL provided: '{}'", base_url)

        # --- Create model ---
        try:
            llm = await asyncio.to_thread(init_chat_model, **kwargs)
            logger.success(
                "LLM created successfully | provider='{}', model='{}'",
                model_config.model_provider,
                model_config.model,
            )
            return llm

        except ImportError as e:
            logger.error(
                "Missing provider package for '{}': {}",
                model_config.model_provider,
                str(e),
            )
            raise
        except Exception as e:
            logger.error("Failed to create LLM: {}", str(e))
            raise