# Setting the Qdrant Provider

# Importing the VectorDBInterface to implement
from ..VectorDBInterface import VectorDBinterface
from ..VectorDBEnums import DistanceMethodEnums

from qdrant_client import models, QdrantClient
import logging
from typing import List
from models.db_schemas import RetrievedDocument


# Creating the class QdrantDBProvider that implements the VectorDBInterface , with inheriting from it
class QdrantDBProvider(VectorDBinterface):
    
    # Construct the class and give it all parameters needed
    async def __init__(self,db_client : str ,default_vector_size : int = 786 , distance_method : str = None,index_threshold : int = 100):
        
        # Setting the class parameters 
        self.client=None
        self.db_client = db_client
        self.distance_method=None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE

        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger= logging.getLogger("uvicorn")

    # Setting the connect function to connect to the vector database
    async def connect(self):
        self.client = QdrantClient(path = self.db_client)

    # Setting the disconnect function to disconnect from the vector database
    async def disconnect(self):
        self.client=None

    # Validating if a certain collection exists or not
    async def is_collection_existed(self, collection_name : str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)


    # A function to list all connections in the vector database
    async def list_all_collections(self) -> List:
        return self.client.get_connections()
    
    # A function to get all collection related info
    async def get_collection_info(self, collection_name : str) -> str:
        return self.client.get_collection(collection_name = collection_name)

    # A function to delete a certain collectio
    async def delete_collection(self, collection_name):
        
        # Validating if the collection existed first then delete it
        if self.is_collection_existed(collection_name):
            return self.client.delete_collection(collection_name = collection_name)
        return None
    
    # A functio to create a collection , give the collection the name ,
    # the embedding size and if it's existed and we want to reset it
    async def create_collection(self, collection_name, embedding_size, do_reset = False):
        
        # Validating if the do_reset flag is up to delete the collection first
        if do_reset :
            _ = self.delete_collection(collection_name=collection_name)
        
        # Validating if the collection existed first and if not existed we process in creating the colelction
        if not self.is_collection_existed(collection_name=collection_name):
            # Send a logging message that's the collection is being created
            self.logger.info(f"Creating new Qdrant collection : {collection_name}")

            # Create the collection with the vector database client , giving its name , embedding size and the distance method
            _ = self.client.create_collection(
                collection_name = collection_name,
                vectors_config=models.VectorParams(
                    size = embedding_size,
                    distance = self.distance_method
                )
            )
            return True
        return False
    
    # A function to insert one record into the database
    async def insert_one(self, collection_name, text, vector, metadata = None, record_id = None):
        
        # Validate first if the collection existed
        if not self.is_collection_existed(collection_name=collection_name):
            
            # If the collection doesn't exist lof that the record can't be inserted
            self.logger.error(F"Can not insert new record to non existed collection {collection_name}")
            return False

        # Now if the collection existed upload the record to that collection with it's metadata and text
        try :
            _ = self.client.upload_records(
                collection_name = collection_name,
                records = [
                    models.Record(
                        id = [record_id],
                        vector = vector,
                        payload = {
                            "text" : text,
                            "metadata" : metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(F"Error while inserting recore {e}")
            return False
        return True
    
    # A function to insert many records to the vector database
    async def insert_many(self, collection_name, texts, vectors, metadata = None, record_ids = None, batch_size = 50):
        
        # Validate if the collection existed first
        if not self.is_collection_existed(collection_name=collection_name):
            
            # If the collection doesn't exist , log a message that you can insert in a non existed collection
            self.logger.error(F"Can not insert new record to non existed collection {collection_name}")
            return False
        
        # Tailor the metadata to the same size of the records if it's already not given
        if metadata is None:
            metadata = [None] * len(texts)

        # Assign indices to records
        if record_ids is None:
            record_ids = list(range(0,len(texts)))

        # looping over records to make it batches to insert in the vector database
        for i in range(0,len(texts),batch_size):
            
            # Assign for each batch its texts and its vectors and its metadatas and its indices
            batch_texts = texts[i:i+batch_size]
            batch_vectors = vectors[i:i+batch_size]
            batch_metadata = metadata[i:i+batch_size]
            batch_record_ids = record_ids [i:i+batch_size]

            # Making a list comprehension for each batch to make it ready for uploading as the vector database takes it
            batch_records = [
                models.Record(
                    id = batch_record_ids[record],
                    vector = batch_vectors[record],
                    payload = {
                        "text" : batch_texts[record],
                        "metadata" : batch_metadata[record]
                    }
                )

                for record in range(len(batch_texts))
            ]

            # Inserting the batch and go to the next batch in the for loop
            try :
                _ = self.client.upload_records(
                    collection_name = collection_name,
                    records = batch_records
                )

            # Print an error if the uploading of the batch is not successfull
            except Exception as e:
                self.logger.error(f"error while inserting batch {e}")
                return False

        return True
        
    # A function to search by vector to get similar results of the vector
    async def search_by_vector(self, collection_name, vector, limit : int = 5):
        
        # Use the database client to search and give it the collection name and the vector and the limit of how many chunks he should return
        results = self.client.search(
            collection_name = collection_name,
            query_vector = vector,
            limit = limit
        )


        # Validate the search results as if there're not any results return None
        if not results or len(results) == 0:
            return None
        

        # Return the retrieved documents and their score of similarity
        return [
            RetrievedDocument(**{
                "score" : result.score,
                "text" : result.payload["text"]
            })
            for result in results 
        ]       