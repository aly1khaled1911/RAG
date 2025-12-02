# Creating a factory to handle Vector database interfacing

# Importing VectorDBEnums enums and all providers we have to switch from
from .providers import QdrantDBProvider , PGVectorProvider
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker

# Create a vector database Provider Factory Class to handle which provider we will use
class VectorDBProviderFactory:

    # Construct the class with setting configurations and giving it to the class
    def __init__(self,config , db_client : sessionmaker = None):
        self.config = config
        self.base_controller = BaseController()
        self.db_client= db_client

    # Now selecting which provider according to the environment variable
    # Whether it's Qdrant provider or PGVector provider
    def create_provider(self,provider : str):
        
        # Now checking what is given , and setting the provider according to this parameter
        if provider == VectorDBEnums.QDRANT.value:

            # If it's qdrant , return QdrantDBProvider
            qdrant_db_client = self.base_controller.get_database_path(db_name=self.config.VECTOR_DB_PATH)
            return QdrantDBProvider(
                db_client=qdrant_db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        
        # If it's PGVector , return PGVectorProvider
        if provider == VectorDBEnums.PGVECTOR.value:
            return PGVectorProvider(
                db_client=self.db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
                )
            
        # if provider isn't supported , return None
        return None


