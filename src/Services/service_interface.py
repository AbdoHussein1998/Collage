from abc import ABC
from typing import Optional
import loguru


class ServiceInterface(ABC):
    def __init__(
        self,
        logger: Optional[loguru._logger.Logger] = None
    ):
        self.logger = logger or loguru.logger

    @classmethod
    async def init_service(
        cls,
        logger: Optional[loguru._logger.Logger] = None,
        *args,
        **kwargs
    ):
        logger = logger or loguru.logger

        logger.info(f"Initializing service: {cls.__name__}")

        instance = cls(
            logger=logger,
            *args,
            **kwargs
        )

        logger.success(
            f"Service {cls.__name__} initialized successfully"
        )

        return instance