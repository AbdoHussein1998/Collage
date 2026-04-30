import asyncio
from typing import Final, Optional,Union,Any

from langchain.embeddings import init_embeddings
from langchain_core.embeddings import Embeddings
from langchain_core.runnables import Runnable
import loguru



class EmbeddingFactory:
    """Factory class for creating embedding instances from various providers."""

    SUPPORTED_PROVIDERS: Final[frozenset[str]] = frozenset({
        "openai",
        "azure_openai",
        "bedrock",
        "cohere",
        "google_vertexai",
        "huggingface",
        "mistralai",
        "ollama",
    })

    @classmethod
    def _validate_and_sanitize(
        cls,
        embedding_provider: str,
        model_name: str,
        logger: loguru._logger.Logger,
    ) -> tuple[str, str]:
        """Validate and sanitize input parameters."""

        # --- Validate types ---
        if not isinstance(embedding_provider, str):
            raise TypeError(
                f"embedding_provider must be a string, got {type(embedding_provider)}"
            )
        if not isinstance(model_name, str):
            raise TypeError(
                f"model_name must be a string, got {type(model_name)}"
            )

        # --- Sanitize: strip whitespace and lowercase ---
        embedding_provider = embedding_provider.strip().lower()
        model_name = model_name.strip().lower()

        # --- Validate not empty after sanitization ---
        if not embedding_provider:
            raise ValueError("embedding_provider cannot be empty")
        if not model_name:
            raise ValueError("model_name cannot be empty")

        # --- Validate provider is supported ---
        if embedding_provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider: '{embedding_provider}'. "
                f"Supported providers: {', '.join(sorted(cls.SUPPORTED_PROVIDERS))}"
            )

        logger.debug(
            "Sanitized inputs | provider='{}', model='{}'",
            embedding_provider,
            model_name,
        )

        return embedding_provider, model_name

    @classmethod
    async def create_embeddings(
        cls,
        embedding_provider: str,
        model_name: str,
        api_key: str = None,
        url: str = None,
        logger: Optional[loguru._logger.Logger] = None,
        **kwargs)->Embeddings:
        # Union[Embeddings, Runnable[Any, list[float]]]:
        """Create an embeddings instance from a provider and model name.

        Args:
            embedding_provider: The provider name (e.g., "openai", "ollama").
            model_name: The model name (e.g., "text-embedding-3-small").
            api_key: Optional API key for the provider.
            url: Optional base URL for the provider.
            logger: Optional loguru Logger instance. Falls back to default loguru logger.
            **kwargs: Additional provider-specific parameters.

        Returns:
            An Embeddings instance.

        Raises:
            TypeError: If inputs are not strings.
            ValueError: If provider is unsupported or inputs are empty.
        """

        # --- Use provided logger or fall back to default ---
        logger = logger or loguru.logger

        logger.info("Creating embeddings | provider='{}', model='{}'",embedding_provider,model_name,)

        # --- Validate & Sanitize ---
        try:
            embedding_provider, model_name = cls._validate_and_sanitize(embedding_provider, model_name, logger)
        except (TypeError, ValueError) as e:
            logger.error("Validation failed: {}", str(e))
            raise

        # --- Build model string ---
        model_str = f"{embedding_provider}:{model_name}"

        if api_key:
            kwargs["api_key"] = api_key
            logger.debug("API key provided")
        if url:
            kwargs["base_url"] = url
            logger.debug("Custom base URL provided: '{}'", url)

        # --- Create embeddings ---
        try:
            embeddings = await asyncio.to_thread(init_embeddings, model_str, **kwargs)
            logger.success("Embeddings created successfully | model_str='{}'", model_str)
            return embeddings

        except ImportError as e:
            logger.error(
                "Missing provider package for '{}': {}",
                embedding_provider,
                str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to create embeddings | model_str='{}': {}",
                model_str,
                str(e),
            )
            raise









