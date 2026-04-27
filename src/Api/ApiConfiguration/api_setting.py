


from pydantic_settings import BaseSettings




class BasicSettings(BaseSettings):   
    """
    Basic settings for the application.
    """

    #########################
    # Application Configuration
    #########################
    APP_NAME:str
    APP_VERSION:str
    
    #########################
    # MongoDB Configuration
    #########################
    MONGODB_URL:str
    MONGODB_DB_NAME:str
    MONGODB_COLLECTION_MAIN:str
    
    #########################
    # Qdrant Configuration
    #########################
    QDRANT_DB_API_KEY:str
    QDRANT_DB_URL:str
    VECTOR_SEARCH_FORMULA:str
    VECTOR_DATABASE_DEFULT_NAME:str


    #########################
    # Embedding Configuration
    #########################
    DEFAULT_EMBEDDING_MODEL:str
    DEFAULT_EMBEDDING_MODEL_CONNECTION_URL:str

    #########################
    # Generation Configuration
    #########################
    
    DEFAULT_GENERATION_MODEL:str
    DEFAULT_GENERATION_MODEL_CONNECTION_URL:str

    












