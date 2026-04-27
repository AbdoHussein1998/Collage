# src/DatabaseInfrastructure/Vector/vector_database_interface.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from logging import Logger

from DatabaseInfrastructure.Vector.Schema.vector_document import VectorDocument


class VectorDBInterface(ABC):
    """
    Abstract interface for all Vector Database providers.
    Any new provider (Qdrant, Chroma, Pinecone, etc.) must implement this.

    Logger handling:
        - If a logger is passed to init_class → use it
        - If not → provider falls back to loguru.logger
    """

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    @abstractmethod
    async def init_class(
        cls,
        logger: Optional[Logger] = None,
        *args,
        **kwargs,
    ):
        pass

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        vector_dimension: int,
        distance: str = "cosine",
    ) -> bool:
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    async def list_collections(self) -> List[str]:
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict:
        pass

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        document: VectorDocument,
    ) -> bool:
        pass

    @abstractmethod
    async def insert_many(
        self,
        collection_name: str,
        documents: List[VectorDocument],
        batch_size: int = 100,
    ) -> bool:
        pass

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_document(
        self,
        collection_name: str,
        document_id: str,
        schema: bool = True,
    ) -> VectorDocument | None:
        pass

    @abstractmethod
    async def get_many_documents(
        self,
        collection_name: str,
        document_ids: List[str],
        schema: bool = True,
    ) -> List[VectorDocument] | List:
        pass

    @abstractmethod
    async def get_all_documents(
        self,
        collection_name: str,
        filters: Optional[Dict[str, Any]] = None,
        batch_size: int = 100,
        schema: bool = True,
    ) -> List[VectorDocument] | List:
        pass

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        schema: bool = True,
    ) -> List[VectorDocument] | List:
        pass

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    @abstractmethod
    async def count_documents(
        self,
        collection_name: str,
    ) -> int:
        pass