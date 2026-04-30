# Dependcecny/arabic_pdf_deps.py

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
import loguru

from Document import DocumentFactoryEngine
from LLM.Embedding import EmbeddingFactory
from DatabaseInfrastructure.Vector.Providers.Qdrant.qdrant_provider import (
    QdrantProvider,
)
from DatabaseInfrastructure.Json.Mongodb import MongoProvider
from Services.Services.arabic_pdf_processing import ArabicPdfProcessingService
from Api.ApiConfiguration.api_setting import get_basic_settings,BasicSettings


async def get_arabic_pdf_service() -> ArabicPdfProcessingService:
    """
    Factory function — builds all dependencies,
    hands them to the service.
    """
    logger = loguru.logger  #later need to be changed to a custom logger 
    settings = get_basic_settings()

    # ─── Build dependencies ───────────────────────────

    # 1. PDF Engine
    document_engine = await DocumentFactoryEngine.select_engine(engine_name="pymupdf",logger_instance=logger,)

    # 2. Embedding Model
    embedding_model = await EmbeddingFactory.create_embeddings(
        embedding_provider=settings.DEFAULT_EMBEDDING_PROVIDER,
        model_name=settings.DEFAULT_EMBEDDING_MODEL,
        api_key=settings.DEFAULT_EMBEDDING_MODEL_API_KEY,
        url=settings.DEFAULT_EMBEDDING_MODEL_CONNECTION_URL
        )

    # 3. Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=300,)

    # 4. Vector DB (Qdrant)
    vector = await QdrantProvider.init_class(url=settings.VECTOR_DB_URL, logger=logger,api_key=settings.VECTOR_DB_API_KEY)

    # 5. MongoDB
    mongo = await MongoProvider.init_class(url=settings.MONGODB_URL,db_name=settings.MONGODB_DB_NAME,logger=logger)

    # ─── Compose service ──────────────────────────────

    service = await ArabicPdfProcessingService.init_service(
        document_engine=document_engine,
        embedding_model=embedding_model,
        text_splitter=text_splitter,
        vector=vector,
        json=mongo,
        logger=logger,
    )

    return service