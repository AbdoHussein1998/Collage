from typing import List, Optional
from LLM.Embedding import EmbeddingFactory
from service_interface import ServiceInterface
from typing import Optional, Union
from langchain.embeddings.base import Embeddings
from langchain_core.runnables import Runnable
import loguru
from fastapi import Response

class EmbeddingService(ServiceInterface):
    def __init__(self,logger: Optional[loguru._logger.Logger] = None) -> None:
        super().__init__(logger)
        self.embedding_model: Optional[Union[Embeddings, Runnable]] = None

    async def select_embed(self,provider: str,model_name: str,api_key:str,url:str):
        self.logger.info(f"Selecting embedding model: {provider}:{model_name}")
        self.embedding_model = await EmbeddingFactory.create_embeddings(embedding_provider=provider,model_name=model_name,api_key=api_key,url=url,logger=self.logger)
        self.logger.success(f"Embedding model {model_name} selected successfully")
        return self.embedding_model

    async def embed_text(self,text: str) -> List[float]:
        self.logger.info("Embedding...")            
        result=self.embedding_model.embed_query(text)
        self.logger.success("Embedding Finshed.")
        return result
    async def embed_text_list(self,text_list: List[str]) -> List[List[float]]:
        self.logger.info("Embedding list of texts...")
        result=self.embedding_model.embed_documents(text_list)
        self.logger.success("Embedding list of texts finished.")
        return result


