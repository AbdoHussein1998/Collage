"""
Async MongoDB Controller using Motor - for WebScraping Project

A robust async MongoDB client wrapper with connection management, batch operations,
error handling, and flexible schema support.

Author: Abdulrhman-Alhkim
Version: 2.0.0 (Motor Async)
"""

from enum import Enum
from typing import Optional, Dict, List, Any, AsyncGenerator,Callable
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, BulkWriteError, ConnectionFailure as PyMongoConnectionError
from pymongo import UpdateOne
import loguru 

from .constants import UpdateOperation

class MongoProvider:
    """
    Production-grade async MongoDB controller using Motor for async operations.
    
    Features:
        - Async/await pattern support
        - Environment-based configuration (no hardcoded credentials)
        - Automatic connection validation and reconnection
        - Batch insertion/updating with error recovery
        - Async streaming with memory efficiency
        - Flexible schema updates via operation enums
        - Comprehensive error handling and logging
        - Async context manager support
    
    Attributes:
        url (str): MongoDB connection string from environment
        db_name (str): Database name from environment
        client (Optional[AsyncClient]): Motor async MongoDB client instance
        db (Optional[AsyncDatabase]): Async database instance
        logger: Loguru logger instance
    """
    
    def __init__(self,mongo_url:str ,db_name: str,logger:Optional[Any]=None) -> None:
        """
        Initialize async MongoDB controller with environment variables or provided parameters.
        Args:
            url (Optional[str]): MongoDB connection URL. Defaults to MONGODB_URL env var.
                Format: mongodb://username:password@host:port/database?authSource=admin
            db_name (Optional[str]): Database name. Defaults to MONGODB_DB_NAME env var or "test".
        
        Raises:
            ValueError: If MONGODB_URL is not provided as argument or environment variable.
        
        """
        self.url:str= mongo_url
        self.db_name: str = db_name 
        
        if not self.url:
            raise ValueError(
                "Connection_String not provided. Pass as argument "
            )
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.logger = logger if logger is not None else loguru.logger
        self.logger.info(f"AsyncMongodbController initialized with db_name: {self.db_name}")
    
    @classmethod
    async def init_class(cls,url,db_name,logger=None):
        """
        Class method to initialize and return an instance of AsyncMongodbController.

        Args:
            url (str): MongoDB connection URL.
            db_name (str): Database name.

        Returns:
            AsyncMongodbController: Initialized instance of AsyncMongodbController.

        """
        try:
            instance = cls(url, db_name,logger)
            instance.logger.success("AsyncMongodbController instance intizled")

            return instance
        except Exception as e:
            loguru.logger.error(f"Failed to initialize AsyncMongodbController: {str(e)}")
            raise

    


    async def __aenter__(self):
        """
        Async context manager entry point - establishes database connection.
        
        Returns:
            AsyncMongodbController: Self for use in async with statement.
        
        Raises:
            ConnectionError: If connection to MongoDB fails.
        """
        if not await self.connect():
            raise ConnectionError("Failed to establish MongoDB connection")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point - closes database connection.
        
        Args:
            exc_type: Exception type if error occurred in async with block
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
        
        Returns:
            bool: False to propagate exceptions from with block
        """
        await self.disconnect()
        return False
    
    async def _ensure_connected(self) -> bool:
        """
        Internal method to validate and maintain database connection.
        
        Checks if client exists and connection is alive. Attempts automatic
        reconnection if connection is lost.
        
        Returns:
            bool: True if connected and healthy, False if connection cannot be established.
        
        Raises:
            Logs critical errors but doesn't raise to allow graceful degradation.
        
        Internal Notes:
            - Uses ping command to verify active connection
            - Automatically reconnects if connection is lost
            - Should be called before all database operations
        """
        if self.client is None:
            self.logger.warning(
                "Database connection not established, attempting initial connection..."
            )
            return await self.connect()
        
        try:
            # Ping to verify connection is alive
            await self.client.admin.command("ping")
            return True
        except (PyMongoConnectionError, Exception) as e:
            self.logger.warning(
                f"Connection health check failed: {type(e).__name__}. "
                f"Attempting to reconnect..."
            )
            await self.disconnect()
            return await self.connect()
    
    async def connect(self) -> bool:
        """
        Establish async connection to MongoDB server.
        
        Configures connection pool, timeout settings, and retry policies
        for production reliability.
        
        Returns:
            bool: True if connection successful, False otherwise.
        
        Connection Parameters:
            - serverSelectionTimeoutMS: 5s (find MongoDB server)
            - connectTimeoutMS: 10s (establish connection)
            - socketTimeoutMS: 30s (individual operation timeout)
            - maxPoolSize: 50 (max concurrent connections)
            - minPoolSize: 10 (maintain minimum connections)
            - retryWrites: True (automatic retry for transient errors)
        """
        try:
            self.logger.info(
                f"Attempting async connection to MongoDB (db={self.db_name})..."
            )
            
            self.client = AsyncIOMotorClient(
                self.url,
                serverSelectionTimeoutMS=5000,      # 5 seconds to find server
                connectTimeoutMS=10000,             # 10 seconds to connect
                socketTimeoutMS=30000,              # 30 seconds per operation
                maxPoolSize=50,                     # Max connections in pool
                minPoolSize=10,                     # Min connections in pool
                retryWrites=True,                   # Automatic retry on transient failures
            )
            
            # Verify connection by pinging server
            await self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            
            self.logger.info(
                f"Successfully connected to MongoDB server. Database: {self.db_name}"
            )
            return True
            
        except PyMongoConnectionError as e:
            self.logger.error(
                f"MongoDB connection failed - network error: {e.details if hasattr(e, 'details') else str(e)}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error during MongoDB connection: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def disconnect(self) -> bool:
        """
        Close async connection to MongoDB server and cleanup resources.
        
        Returns:
            bool: True if disconnection successful or already disconnected, False on error.
    
        """
        try:
            self.logger.info("Attempting to disconnect from MongoDB...")
            
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
                self.logger.success("Successfully disconnected from MongoDB")
                return True
            
            self.logger.debug("Client was already None, no disconnection needed")
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error during MongoDB disconnection: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        """
        Check if collection exists in current database.
        
        Args:
            collection_name (str): Name of collection to check.
        
        Returns:
            bool: True if collection exists, False otherwise.
        
        Raises:
            Returns False on any error instead of raising exception.
        
        """
        try:
            if not await self._ensure_connected():
                self.logger.error("Cannot check collection - database not connected")
                return False
            
            collections = await self.db.list_collection_names()
            exists: bool = collection_name in collections
            self.logger.debug(
                f"Collection '{collection_name}' existence check: {exists}"
            )
            return exists
            
        except Exception as e:
            self.logger.error(
                f"Error checking collection existence for '{collection_name}': "
                f"{type(e).__name__}: {str(e)}"
            )
            return False
    
    async def insert_one(
        self,
        collection_name: str,
        document: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Insert single document into collection (async).
        
        Handles duplicate key errors gracefully and logs appropriately.
        
        Args:
            collection_name (str): Target collection name.
            document (Dict[str, Any]): Document to insert.
        
        Returns:
            Optional[Any]: Inserted document ID (ObjectId) on success, None on error.
        
        Raises:
            Catches exceptions and returns None instead of raising.
        """
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot insert into '{collection_name}' - database not connected"
                )
                return None
            
            self.logger.debug(
                f"Inserting one document into '{collection_name}'..."
            )
            
            result = await self.db[collection_name].insert_one(document)
            
            self.logger.info(
                f"Successfully inserted document with ID: {result.inserted_id} "
                f"into '{collection_name}'"
            )
            return result.inserted_id
            
        except DuplicateKeyError as e:
            # Expected error - duplicate unique key
            self.logger.info(
                f"Duplicate key error in '{collection_name}' - document skipped. "
                f"Details: {e.details.get('errmsg', 'Unknown') if hasattr(e, 'details') else str(e)}"
            )
            return None
        except Exception as e:
            # Programming error or unexpected database issue
            self.logger.error(
                f"Unexpected error inserting into '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return None
    
    async def insert_many(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> Optional[List[Any]]:
        """
        Insert multiple documents in batches with duplicate tolerance (async).

        """

        if not documents:
            self.logger.warning(
                f"insert_many skipped | collection='{collection_name}' | "
                f"reason='no documents provided'"
            )
            return []

        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"insert_many aborted | collection='{collection_name}' | "
                    f"reason='database not connected'"
                )
                return None

            total_docs = len(documents)
            total_batches = (total_docs + batch_size - 1) // batch_size

            inserted_count = 0

            inserted_ids: List[Any] = []

            failed_batches = 0

            self.logger.info(
                f"insert_many started | collection='{collection_name}' | "
                f"provided={total_docs}, batches={total_batches}, "
                f"batch_size={batch_size}"
            )

            for batch_num, start in enumerate(range(0, total_docs, batch_size), 1):
                batch = documents[start:start + batch_size]

                try:
                    result = await self.db[collection_name].insert_many(batch,ordered=False  # Continue inserting despite duplicates
            )


                    batch_inserted = len(result.inserted_ids)
                    inserted_count += batch_inserted
                    inserted_ids.extend(result.inserted_ids)

                    self.logger.info(
                        f"Batch {batch_num}/{total_batches} | "
                        f"size={len(batch)} | inserted={batch_inserted}"
                    )


                except BulkWriteError as e:
                    batch_inserted = e.details.get("nInserted", 0)
                    inserted_count += batch_inserted
                    write_errors = e.details.get("writeErrors", [])

                    self.logger.info(
                        f"Batch {batch_num}/{total_batches} | "
                        f"partial insert | inserted={batch_inserted} | "
                        f"duplicate_or_errors={len(write_errors)}"
                    )

                except Exception as e:
                    failed_batches += 1
                    self.logger.error(
                        f"Batch {batch_num}/{total_batches} failed | "
                        f"{type(e).__name__}: {str(e)}",
                        exc_info=True
                    )

            # 🔹 CHANGE #6:
            # Summary now uses authoritative inserted_count
            duplicate_count = total_docs - inserted_count

            # 🔹 CHANGE #7:
            # Dynamic log level reflects BUSINESS outcome
            if inserted_count == total_docs:
                level = "success"
            elif inserted_count > 0:
                level = "warning"
            else:
                level = "info"

            log_message = (
                f"insert_many summary | collection='{collection_name}' | "
                f"provided={total_docs}, inserted={inserted_count}, "
                f"duplicates={duplicate_count}, failed_batches={failed_batches}"
            )

            getattr(self.logger, level)(log_message)

            return inserted_ids

        except Exception as e:
            self.logger.critical(
                f"insert_many critical failure | collection='{collection_name}' | "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return None

    
    
    
    async def get_one(
        self,
        collection_name: str,
        query: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve single document from collection (async).
        
        Args:
            collection_name (str): Source collection name.
            query (Optional[Dict[str, Any]]): Query filter. Defaults to first document.
        
        Returns:
            Optional[Dict[str, Any]]: Document matching query, or None if not found/error.
        

        """
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot query '{collection_name}' - database not connected"
                )
                return None
            
            if query is None:
                query = {}
            
            self.logger.debug(
                f"Retrieving one document from '{collection_name}' with query: {query}"
            )
            
            result = await self.db[collection_name].find_one(query)
            
            if result:
                self.logger.info(
                    f"Successfully retrieved document from '{collection_name}'"
                )
            else:
                self.logger.debug(
                    f"No document found in '{collection_name}' matching query"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error retrieving document from '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return None
    
    async def stream_many_docs(
        self,
        collection_name: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Stream documents from collection in batches (async, memory-efficient).
        
        Yields documents in configurable batch sizes instead of loading all
        into memory. Ideal for processing large datasets.
        
        Args:
            collection_name (str): Source collection name.
            query (Optional[Dict[str, Any]]): Query filter. Defaults to all documents.
            projection (Optional[Dict[str, Any]]): Fields to include/exclude.
            batch_size (int): Batch size for yielding. Defaults to 1000.
        
        Yields:
            List[Dict[str, Any]]: Batch of documents.
        
        Raises:
            ConnectionError: If database connection is lost during streaming.
        """
        if query is None:
            query = {}
        
        try:
            if not await self._ensure_connected():
                raise ConnectionError("Database not connected")
            
            self.logger.info(
                f"Starting document stream from '{collection_name}' "
                f"(batch_size={batch_size}, query={query})"
            )
            
            cursor = self.db[collection_name].find(query, projection).batch_size(batch_size)
            
            batch: List[Dict[str, Any]] = []
            doc_count = 0
            
            async for doc in cursor:
                batch.append(doc)
                doc_count += 1
                
                if len(batch) >= batch_size:
                    self.logger.debug(
                        f"Yielding batch of {len(batch)} documents "
                        f"(total streamed: {doc_count})"
                    )
                    yield batch
                    batch = []
            
            # Yield remaining documents
            if batch:
                self.logger.debug(
                    f"Yielding final batch of {len(batch)} documents "
                    f"(total streamed: {doc_count})"
                )
                yield batch
            
            self.logger.info(
                f"Document streaming complete for '{collection_name}': "
                f"Total documents streamed: {doc_count}"
            )
            
        except ConnectionError as e:
            self.logger.error(
                f"Connection lost during streaming from '{collection_name}': {str(e)}"
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Error streaming documents from '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_many( self,
        collection_name: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        batch_size: int = 3000,)->List[Dict[str, Any]]:
        self.logger.info(f"Get all called for '{collection_name}' with query: {query} and projection: {projection}, using Batchses of {batch_size}")
        all_docs=[]
        async for batch in self.stream_many_docs(collection_name, query, projection, batch_size):
            all_docs.extend(batch)
        return all_docs
    
    async def create_collection(self, collection_name: str) -> bool:
        """
        Create new collection in database (async).
        
        Idempotent - succeeds if collection already exists.
        
        Args:
            collection_name (str): Name of collection to create.
        
        Returns:
            bool: True if collection created or already exists, False on error.
        
        """
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot create collection '{collection_name}' - "
                    f"database not connected"
                )
                return False
            
            collections = await self.db.list_collection_names()
            if collection_name in collections:
                self.logger.info(
                    f"Collection '{collection_name}' already exists"
                )
                return True
            
            await self.db.create_collection(collection_name)
            self.logger.info(
                f"Successfully created collection '{collection_name}'"
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error creating collection '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Drop collection from database (async).
        
        Args:
            collection_name (str): Name of collection to delete.
        
        Returns:
            bool: True if deleted, False if not found or error.
        
        """
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot delete collection '{collection_name}' - "
                    f"database not connected"
                )
                return False
            
            if not await self.is_collection_existed(collection_name):
                self.logger.warning(
                    f"Collection '{collection_name}' does not exist"
                )
                return False
            
            await self.db.drop_collection(collection_name)
            self.logger.info(
                f"Successfully deleted collection '{collection_name}'"
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error deleting collection '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """
        Update single document in collection (async, with upsert).
        
        Args:
            collection_name (str): Target collection name.
            query (Dict[str, Any]): Query to match document.
            update (Dict[str, Any]): Update operations (e.g., {"$set": {...}}).
        
        Returns:
            bool: True if document matched and updated, False otherwise.
        
        """
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot update in '{collection_name}' - database not connected"
                )
                return False
            
            self.logger.debug(
                f"Updating one document in '{collection_name}' "
                f"(query={query}, upsert=True)"
            )
            
            result = await self.db[collection_name].update_one(
                query,
                update,
                upsert=True
            )
            
            self.logger.info(
                f"Update result for '{collection_name}': "
                f"Matched={result.matched_count}, "
                f"Modified={result.modified_count}, "
                f"Upserted={result.upserted_id if result.upserted_id else 'None'}"
            )
            
            return result.matched_count > 0
            
        except Exception as e:
            self.logger.error(
                f"Error updating document in '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def create_index(
        self,
        collection_name: str,
        fields: List[tuple],
        index_name: str = None,
        unique: bool = False,
        sparse: bool = False
    ) -> bool:
        """
        Create index on collection (async).
        
        Supports single and composite indexes with various options.
        
        Args:
            collection_name (str): Target collection name.
            fields (List[tuple]): List of (field_name, direction) tuples.
                Direction: 1 for ascending, -1 for descending.
            index_name (str): Custom index name. Auto-generated if None.
            unique (bool): Enforce uniqueness constraint. Defaults to False.
            sparse (bool): Index only documents with field. Defaults to False.
        
        Returns:
            bool: True if index created or already exists, False on error.
    
        """
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot create index on '{collection_name}' - "
                    f"database not connected"
                )
                return False
            
            if not await self.is_collection_existed(collection_name):
                self.logger.warning(
                    f"Collection '{collection_name}' does not exist"
                )
                return False
            
            # Auto-generate index name if not provided
            if not index_name:
                index_name = "_".join(
                    f"{field}_{direction}" for field, direction in fields
                )
            
            # Check if index already exists
            existing_indexes = await self.db[collection_name].index_information()
            
            if index_name in existing_indexes:
                self.logger.info(
                    f"Index '{index_name}' already exists on '{collection_name}'"
                )
                return True
            
            self.logger.info(
                f"Creating index '{index_name}' on '{collection_name}' "
                f"(fields={fields}, unique={unique}, sparse={sparse})"
            )
            
            await self.db[collection_name].create_index(
                fields,
                name=index_name,
                unique=unique,
                sparse=sparse
            )
            
            self.logger.info(
                f"Successfully created index '{index_name}' on '{collection_name}'"
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error creating index '{index_name}' on '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def update_many(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        key_field: str,
        operations: Dict[UpdateOperation, Dict[str, Any]],
        batch_size: int = 1000
    ) -> bool:
        """
        Bulk upsert documents with flexible schema operations (async).
        
        Performs bulk write operations with configurable field mappings.
        Supports multiple update operations via UpdateOperation enum.
        
        Args:
            collection_name (str): Target collection name.
            documents (List[Dict[str, Any]]): Documents to upsert.
            key_field (str): Field name to use for matching existing documents.
            operations (Dict[UpdateOperation, Dict[str, Any]]): Mapping of
                operations to field mappings.
            batch_size (int): Number of documents per batch. Defaults to 1000.
        
        Returns:
            bool: True if operation completed (even with partial failures).
        
        """
        if not documents:
            self.logger.warning(
                f"No documents provided for update_many in '{collection_name}'"
            )
            return False
        
        try:
            if not await self._ensure_connected():
                self.logger.error(
                    f"Cannot update in '{collection_name}' - database not connected"
                )
                return False
            
            collection = self.db[collection_name]
            total_docs = len(documents)
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            self.logger.info(
                f"Starting bulk upsert in '{collection_name}': "
                f"{total_docs} documents in {total_batches} batches (batch_size={batch_size})"
            )
            
            for batch_num, i in enumerate(range(0, len(documents), batch_size), 1):
                batch = documents[i:i + batch_size]
                ops_list = []
                
                for doc in batch:
                    # Validate key field exists
                    if key_field not in doc:
                        self.logger.warning(
                            f"Document missing key field '{key_field}' - skipping"
                        )
                        continue
                    
                    # Build update document from operations
                    update_doc = {}
                    
                    for op, field_mapping in operations.items():
                        if op == UpdateOperation.SET:
                            # Standard field updates
                            set_fields = {}
                            for target_field, source_field in field_mapping.items():
                                if source_field in doc:
                                    set_fields[target_field] = doc[source_field]
                            if set_fields:
                                update_doc["$set"] = set_fields
                        
                        elif op == UpdateOperation.PUSH_BOUNDED:
                            # Array append with size limit
                            push_fields = {}
                            for target_array, source_field in field_mapping.items():
                                if source_field in doc:
                                    push_fields[target_array] = {
                                        "$each": [doc[source_field]],
                                        "$slice": -10000  # Keep last 10000 entries
                                    }
                            if push_fields:
                                update_doc["$push"] = push_fields
                        
                        elif op == UpdateOperation.PUSH:
                            # Simple array append
                            push_fields = {}
                            for target_array, source_field in field_mapping.items():
                                if source_field in doc:
                                    push_fields[target_array] = doc[source_field]
                            if push_fields:
                                update_doc["$push"] = push_fields
                        
                        elif op == UpdateOperation.CURRENT_DATE:
                            # Add current timestamp
                            update_doc["$currentDate"] = field_mapping
                        
                        elif op == UpdateOperation.SET_ON_INSERT:
                            # Set on new document only
                            set_on_insert_fields = {}
                            for target_field, source_field in field_mapping.items():
                                if source_field in doc:
                                    set_on_insert_fields[target_field] = doc[source_field]
                                else:
                                    # If source doesn't exist, use target as field name
                                    if target_field in doc:
                                        set_on_insert_fields[target_field] = doc[target_field]
                            if set_on_insert_fields:
                                update_doc["$setOnInsert"] = set_on_insert_fields
                        
                        elif op == UpdateOperation.UNSET:
                            # Remove fields
                            update_doc["$unset"] = field_mapping
                        
                        elif op == UpdateOperation.INC:
                            # Increment numeric fields
                            update_doc["$inc"] = field_mapping
                    
                    if update_doc:
                        ops_list.append(
                            UpdateOne(
                                {key_field: doc[key_field]},
                                update_doc,
                                upsert=True
                            )
                        )
                
                if not ops_list:
                    self.logger.warning(
                        f"Batch {batch_num}/{total_batches}: No valid operations"
                    )
                    continue
                
                try:
                    result = await collection.bulk_write(ops_list, ordered=False)
                    
                    self.logger.info(
                        f"Batch {batch_num}/{total_batches}: "
                        f"Matched={result.matched_count}, "
                        f"Modified={result.modified_count}, "
                        f"Upserted={len(result.upserted_ids)}"
                    )
                    
                except BulkWriteError as e:
                    write_errors = e.details.get("writeErrors", [])
                    
                    self.logger.error(
                        f"Batch {batch_num}/{total_batches}: BulkWriteError. "
                        f"Write errors: {len(write_errors)}. "
                        f"Error details: {e.details}"
                    )
                
                except Exception as e:
                    self.logger.error(
                        f"Batch {batch_num}/{total_batches}: "
                        f"Unexpected error: {type(e).__name__}: {str(e)}",
                        exc_info=True
                    )
            
            self.logger.info(
                f"Bulk upsert completed for '{collection_name}'"
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Critical error in update_many for '{collection_name}': "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False

