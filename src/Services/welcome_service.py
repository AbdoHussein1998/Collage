import loguru
from typing import Optional


class WelcomeService:
    def __init__(self,logger: Optional[loguru._logger.Logger] = None) -> None:
        self.logger = logger or loguru.logger

    @classmethod
    async def init_service(cls,
        logger: Optional[loguru._logger.Logger] = None,) -> "WelcomeService":
        logger = logger or loguru.logger
        logger.info("Initializing WelcomeService...")
        instance=cls(logger=logger) 
        return instance




    async def welcome(self) -> str:
        self.logger.info("Welcome service is running")

        return "Welcome to the Base RAG application"