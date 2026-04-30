from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
import loguru
from .api_setting import get_basic_settings
from LLM.Embedding import EmbeddingFactory


def create_lifespan(logger: Optional[loguru._logger.Logger] = None):
    if logger is None:
        logger = loguru.logger


    @asynccontextmanager
    async def lifespan(app: FastAPI):

        logger.info("FastAPI app is starting up...")        
        app.state.basic_settings=get_basic_settings()



        yield

        logger.info("FastAPI app is shutting down...")

    return lifespan
