# Creating Interface to implement providers according to these function 
# to ensure all providers have the same behavior

# Importing abstraction methods and the abc class for interfacing
from abc import ABC ,abstractmethod

class LLMInterface(ABC):

    # Setting all functions as abstraction_method

    # Setting generation model
    @abstractmethod
    def set_generation_model(self , model_id : str):
        pass
    # Setting embedding model
    @abstractmethod
    def set_embedding_model(self , model_id : str , embedding_size : int):
        pass
    
    # Generating text from query
    @abstractmethod
    def generate_text(self , prompt : str, 
                    chat_history : list =[],max_output_token: int = None , temperature : float = None):
        pass

    # getting text embeddings
    @abstractmethod
    def embed_text(self , text:str, document_type : str = None):
        pass

    # Construction the prompt
    @abstractmethod
    def construct_prompt(self , prompt : str , role : str):
        pass