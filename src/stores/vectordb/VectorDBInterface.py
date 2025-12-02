# Creating Interface to implement providers according to these function 
# to ensure all providers have the same behavior

# Importing abstraction methods and the abc class for interfacing
from abc import ABC , abstractmethod
from typing import List

class VectorDBinterface(ABC):

    # Setting all functions as abstraction_method

    # A function to connect to the database
    @abstractmethod
    def connect(self):
        pass

    # A function to disconnect from the database
    @abstractmethod
    def disconnect(self):
        pass
    
    # A function to validate if a collection existed or not
    @abstractmethod
    def is_collection_existed(self,collection_name : str) -> bool:
        pass

    # A function to list all collections in the vector database
    @abstractmethod
    def list_all_collections(self) -> List:
        pass
    
    # A function to get collection info
    @abstractmethod
    def get_collection_info(self,collection_name : str) -> dict:
        pass
    
    # A function to delete a collection
    @abstractmethod
    def delete_collection(self , collection_name : str) -> dict:
        pass

    # A function to create a collection
    @abstractmethod
    def create_collection(self , collection_name : str,
                                embedding_size: int,
                                do_reset : bool = False):
        pass
    
    # A function to insert one record
    @abstractmethod
    def insert_one(self, collection_name : str ,text : str , vector : list,
                         metadata : dict = None,
                         record_id : str = None):
        pass
    
    # A function to insert many records
    @abstractmethod
    def insert_many(self , collection_name : str,texts : list,vectors : list,
                           metadata : list = None,
                           record_ids : list = None,
                           batch_size : int = 50):
        pass
    
    # A function to search by a vector
    @abstractmethod
    def search_by_vector(self , collection_name : str , vector : list , limit : int):
        pass

