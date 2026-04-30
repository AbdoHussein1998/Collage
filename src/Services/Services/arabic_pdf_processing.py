

from typing import Optional, List
import uuid
import loguru

from fastapi import UploadFile
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

from Document import BasePdfInterface
from DatabaseInfrastructure.Vector.Providers.Qdrant.qdrant_provider import (
    QdrantProvider,
    VectorDocument,
)
from DatabaseInfrastructure.Json.Mongodb import MongoProvider
from Services.service_interface import ServiceInterface
from Services.Exceptions.arabic_pdf_processing_excp import ArabicPdfProcessingError

class ArabicPdfProcessingService(ServiceInterface):
    """
    Orchestrator service for Arabic PDF processing.
    Receives all dependencies via init_service.
    """

    def __init__(
        self,
        document_engine: BasePdfInterface,
        embedding_model: Embeddings,
        text_splitter: RecursiveCharacterTextSplitter,
        vector: QdrantProvider,
        json: MongoProvider,
        collection_name: str = "arabic_pdfs",
        logger: Optional[loguru._logger.Logger] = None,
    ):
        # Injected dependencies
        self.document_engine = document_engine
        self.embedding_model = embedding_model
        self.text_splitter = text_splitter
        self.vector = vector
        self.json = json

        # Config
        self.collection_name = collection_name

        # Runtime state
        self.file: Optional[UploadFile] = None
        self.text: Optional[str] = None
        self.chunks: List[str] = []
        self.embedded_chunks: List[List[float]] = []

        # Logger
        self.logger = logger or loguru.logger

    @classmethod
    async def init_service(
        cls,
        document_engine: BasePdfInterface,
        embedding_model: Embeddings,
        text_splitter: RecursiveCharacterTextSplitter,
        vector: QdrantProvider,
        json: MongoProvider,
        collection_name: str = "arabic_pdfs",
        logger: Optional[loguru._logger.Logger] = None,
    ) -> "ArabicPdfProcessingService":
        """
        Factory method — receives pre-built dependencies.
        """

        logger = logger or loguru.logger
        logger.info(
            "Initializing ArabicPdfProcessingService..."
        )

        instance = cls(
            document_engine=document_engine,
            embedding_model=embedding_model,
            text_splitter=text_splitter,
            vector=vector,
            json=json,
            collection_name=collection_name,
            logger=logger,
        )

        logger.success(
            "ArabicPdfProcessingService ready."
        )

        return instance

    # =====================================================
    # STEP 1: READ PDF
    # =====================================================

    async def read_pdf(
        self,
        file: UploadFile,
    ) -> str:
        """
        Extract text from uploaded PDF.
        """

        try:
            self.file = file

            self.logger.info(
                f"Extracting text from: {file.filename}"
            )

            file_bytes = await file.read()

            if not file_bytes:
                self.logger.error(
                    "Uploaded file is empty."
                )

                raise ArabicPdfProcessingError(
                    "Uploaded file is empty."
                )

            extracted = (
                await self.document_engine
                .extract_text_from_bytes(file_bytes)
            )


            if not extracted:
                self.logger.error(
                    "No text extracted from PDF."
                )

                raise ArabicPdfProcessingError(
                    "No text extracted from PDF."
                )

            # Handle list of pages → convert to one string
            if isinstance(extracted, list):
                self.text = "\n".join(
                    str(page)
                    for page in extracted
                    if page
                )
            else:
                self.text = str(extracted)

            if not self.text.strip():
                self.logger.error(
                    "Extracted text is empty."
                )

                raise ArabicPdfProcessingError(
                    "Extracted text is empty."
                )

            self.logger.success(
                f"Text extracted successfully "
                f"(length={len(self.text)})"
            )


            def clean_arabic_text(text: str) -> str:
                """
                Remove:
                - Parentheses and their content
                - Emojis
                - Arabic tashkeel (diacritics)
                - Special symbols / punctuation

                Keep only:
                - Arabic letters
                - English letters
                - Numbers
                - Spaces

                Example:
                "السَّلَامُ عَلَيْكُمْ 😊 (test) 123"
                -> "السلام عليكم 123"
                """
                self.logger.info("Cleaning The Text")
                if not text:
                    return ""

                # 1. Remove parentheses and everything inside them
                text = re.sub(r"\(.*?\)", "", text)

                # 2. Remove Arabic tashkeel (diacritics)
                tashkeel_pattern = r"""
                    ّ    | # Shadda
                    َ    | # Fatha
                    ً    | # Tanwin Fath
                    ُ    | # Damma
                    ٌ    | # Tanwin Damm
                    ِ    | # Kasra
                    ٍ    | # Tanwin Kasr
                    ْ    | # Sukun
                    ـ      # Tatweel / Kashida
                """
                text = re.sub(tashkeel_pattern, "", text, flags=re.VERBOSE)

                # 3. Remove emojis and symbols (keep Arabic, English, digits, spaces)
                text = re.sub(r"[^\u0600-\u06FFa-zA-Z0-9\s]", "", text)

                # 4. Normalize multiple spaces
                text = re.sub(r"\s+", " ", text).strip()

                return text

            return clean_arabic_text(self.text)

        except ArabicPdfProcessingError:
            raise

        except Exception as e:
            self.logger.exception(
                f"PDF read failed: {str(e)}"
            )

            raise ArabicPdfProcessingError(
                "Failed while reading PDF."
            )

    # =====================================================
    # STEP 2: SPLIT TEXT
    # =====================================================

    async def split_text(self) -> List[str]:
        """
        Split extracted text into chunks.
        """

        try:
            if not self.text:
                raise ArabicPdfProcessingError(
                    "No text available. "
                    "Run read_pdf() first."
                )

            self.logger.info(
                "Splitting text into chunks..."
            )

            self.chunks = (
                self.text_splitter.split_text(
                    self.text
                )
            )

            if not self.chunks:
                raise ArabicPdfProcessingError(
                    "No chunks generated."
                )

            self.logger.success(
                f"Split into "
                f"{len(self.chunks)} chunks."
            )

            return self.chunks

        except ArabicPdfProcessingError:
            raise

        except Exception as e:
            self.logger.exception(
                f"Text splitting failed: {str(e)}"
            )

            raise ArabicPdfProcessingError(
                "Failed while splitting text."
            )

    # =====================================================
    # STEP 3: EMBED CHUNKS
    # =====================================================

    async def embed_chunks(self) -> List[List[float]]:
        """
        Generate embeddings for all chunks.
        """

        try:
            if not self.chunks:
                raise ArabicPdfProcessingError(
                    "No chunks available. "
                    "Run split_text() first."
                )

            self.logger.info(
                f"Embedding "
                f"{len(self.chunks)} chunks..."
            )

            self.embedded_chunks = (
                await self.embedding_model
                .aembed_documents(self.chunks)
            )

            if not self.embedded_chunks:
                raise ArabicPdfProcessingError(
                    "Embedding generation failed."
                )

            self.logger.success(
                "Embedding completed successfully."
            )

            return self.embedded_chunks

        except ArabicPdfProcessingError:
            raise

        except Exception as e:
            self.logger.exception(
                f"Embedding failed: {str(e)}"
            )

            raise ArabicPdfProcessingError(
                "Failed while generating embeddings."
            )

    # =====================================================
    # STEP 4: PUSH VECTORS TO QDRANT
    # =====================================================

    async def push_vectors(self) -> None:
        """
        Store embeddings in Qdrant.
        """

        try:
            if not self.embedded_chunks:
                raise ArabicPdfProcessingError(
                    "No embeddings available. "
                    "Run embed_chunks() first."
                )

            if not self.file:
                raise ArabicPdfProcessingError(
                    "File metadata missing."
                )

            documents = [
                VectorDocument(
                    id=str(uuid.uuid4()),
                    content=chunk,
                    vector=embedding,
                    payload={
                        "file_name":
                        self.file.filename
                    },
                )
                for chunk, embedding in zip(
                    self.chunks,
                    self.embedded_chunks
                )
            ]

            self.logger.info(
                f"Inserting "
                f"{len(documents)} vectors "
                f"into Qdrant..."
            )
            try:
                await self.vector.create_collection(
                collection_name=self.collection_name,
                vector_dimension=len(self.embedded_chunks[0]),
                distance="Cosine",
            )
            except Exception as e:
                pass
            await self.vector.insert_many(
                collection_name=self.collection_name,
                documents=documents,
                batch_size=1000,
            )

            self.logger.success(
                "Vectors stored successfully."
            )

        except ArabicPdfProcessingError:
            raise

        except Exception as e:
            self.logger.exception(
                f"Vector insert failed: {str(e)}"
            )

            raise ArabicPdfProcessingError(
                "Failed while storing vectors."
            )

    # =====================================================
    # STEP 5: PUSH TEXT TO MONGODB
    # =====================================================

    async def push_texts_to_json(self) -> None:
        """
        Store text chunks in MongoDB.
        """

        try:
            if not self.chunks:
                raise ArabicPdfProcessingError(
                    "No chunks available. "
                    "Run split_text() first."
                )

            if not self.file:
                raise ArabicPdfProcessingError(
                    "File metadata missing."
                )

            documents = [
                {
                    "file_name":
                    self.file.filename,
                    "content":
                    chunk,
                }
                for chunk in self.chunks
            ]

            self.logger.info(
                f"Inserting "
                f"{len(documents)} documents "
                f"into MongoDB..."
            )

            await self.json.insert_many(
                collection_name=self.collection_name,
                documents=documents,
            )

            self.logger.success(
                "Text chunks stored successfully."
            )

        except ArabicPdfProcessingError:
            raise

        except Exception as e:
            self.logger.exception(
                f"MongoDB insert failed: {str(e)}"
            )

            raise ArabicPdfProcessingError(
                "Failed while storing text."
            )

    # =====================================================
    # CLEANUP
    # =====================================================

    async def close_connections(self) -> None:
        """
        Safely close external connections.
        """

        try:
            if self.vector:
                await self.vector.disconnect()

                self.logger.info(
                    "Qdrant disconnected."
                )

        except Exception as e:
            self.logger.exception(
                f"Connection closing failed: "
                f"{str(e)}"
            )

    # =====================================================
    # FULL PIPELINE
    # =====================================================

    async def process(
        self,
        file: UploadFile,
    ) -> dict:
        """
        Full workflow:
            1. Read PDF
            2. Split text
            3. Embed chunks
            4. Push vectors
            5. Push texts
        """

        try:
            self.logger.info(
                f"Processing PDF: "
                f"{file.filename}"
            )

            await self.read_pdf(file)
            await self.split_text()
            await self.embed_chunks()
            await self.push_vectors()
            await self.push_texts_to_json()

            self.logger.success(
                f"PDF '{file.filename}' "
                f"processed successfully."
            )

            return {
                "status": "success",
                "filename": file.filename,
                "total_chunks":
                len(self.chunks),
                "embedding_dim": (
                    len(
                        self.embedded_chunks[0]
                    )
                    if self.embedded_chunks
                    else 0
                ),
            }

        except ArabicPdfProcessingError:
            raise

        except Exception as e:
            self.logger.exception(
                f"PDF processing failed: "
                f"{str(e)}"
            )

            raise ArabicPdfProcessingError(
                "Unexpected PDF processing failure."
            )

        finally:
            await self.close_connections()