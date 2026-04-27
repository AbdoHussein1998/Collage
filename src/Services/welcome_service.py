import loguru
from typing import Optional
from Services.service_interface import ServiceInterface


class WelcomeService(ServiceInterface):
    def __init__(self,logger: Optional[loguru._logger.Logger] = None) -> None:
        self.logger = logger or loguru.logger


    async def welcome(self) -> str:
        self.logger.info("Welcome service is running")

        return "Welcome to the Base RAG application"