from typing import Optional, Union
from LLM.Generation import GenerationFactory, ModelConfig
from service_interface import ServiceInterface
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
import loguru


class GenerationService(ServiceInterface):
    """Thin service — only responsible for model selection and access."""

    def __init__(
        self,
        logger: Optional[loguru._logger.Logger] = None,
    ) -> None:
        super().__init__(logger)
        self.llm: Optional[Union[BaseChatModel, Runnable]] = None
        self.model_config: Optional[ModelConfig] = None

    async def select_model(
        self,
        model_config: Optional[ModelConfig] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Union[BaseChatModel, Runnable]:
        """Select and initialize an LLM model.

        Args:
            model_config: ModelConfig dataclass. Uses defaults if not provided.
            api_key: Optional API key for the provider.
            base_url: Optional base URL for the provider.

        Returns:
            The configured LLM instance.
        """
        self.model_config = model_config or ModelConfig()

        self.logger.info(
            "Selecting LLM model: {}:{}",
            self.model_config.model_provider,
            self.model_config.model,
        )

        self.llm = await GenerationFactory.create_llm(
            model_config=self.model_config,
            api_key=api_key,
            base_url=base_url,
            logger=self.logger,
        )

        self.logger.success(
            "LLM model {}:{} selected successfully",
            self.model_config.model_provider,
            self.model_config.model,
        )
        return self.llm

    @property
    def model(self) -> Union[BaseChatModel, Runnable]:
        """Get the current LLM model."""
        if self.llm is None:
            self.logger.error("No LLM model selected. Call select_model() first.")
            raise RuntimeError("No LLM model selected. Call select_model() first.")
        return self.llm