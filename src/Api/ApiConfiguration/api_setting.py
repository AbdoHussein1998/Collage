


from pydantic_settings import BaseSettings,SettingsConfigDict




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
    
    #########################
    # Qdrant Configuration
    #########################
    VECTOR_DB_API_KEY:str
    VECTOR_DB_URL:str
    VECTOR_SEARCH_FORMULA:str
    VECTOR_DATABASE_DEFULT_NAME:str


    #########################
    # Embedding Configuration
    #########################
    DEFAULT_EMBEDDING_MODEL:str
    DEFAULT_EMBEDDING_MODEL_API_KEY:str
    DEFAULT_EMBEDDING_PROVIDER:str
    DEFAULT_EMBEDDING_MODEL_CONNECTION_URL:str


    #########################
    # Generation Configuration
    #########################
    
    DEFAULT_GENERATION_MODEL:str
    DEFAULT_GENERATION_MODEL_CONNECTION_URL:str

    model_config = SettingsConfigDict(
    env_file="src/.env",
    extra="ignore"
)




def get_basic_settings() -> BasicSettings:
    """
    Get the basic settings for the application.
    """
    return BasicSettings()







