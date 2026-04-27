from contextlib import asynccontextmanager
from fastapi import FastAPI
import loguru
from typing import Optional

from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
import loguru

def create_lifespan(logger: Optional[loguru._logger.Logger] = None):
    if logger is None:
        logger = loguru.logger


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("FastAPI app is starting up...")
        


        yield

        logger.info("FastAPI app is shutting down...")

    return lifespan
