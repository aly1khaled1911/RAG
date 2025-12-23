# Setting the CoHere Provider

# Importing the LLMInterface to implement

from ..LLMInterface import LLMInterface
from ..LLMEnum import CoHereEnums , DocumentTypeEnums
import cohere
import logging
from typing import List , Union

# Creating the class CoHereProvider that implements the LLMInterface , with inheriting from it
class CoHereProvider(LLMInterface):

    # Construct the class and give it all parameters needed
    def __init__(self , api_key : str ,
                        default_input_max_characters : int = 10000,
                        default_generation_max_output_tokens : int = 10000,
                        default_generation_temperature : float = 0.1):

        # Setting the class parameters 
        self.api_key=api_key
        
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(api_key = self.api_key)
        self.enums = CoHereEnums

        self.logger = logging.getLogger(__name__)

    # This function is to set the generation model by giving it the model id we will use from CoHere
    def set_generation_model(self , model_id : str):
        self.generation_model_id = model_id
    
    # This function is to set the embedding model and its size 
    # by giving it the model id we will use from CoHere and the embedding size
    def set_embedding_model(self , model_id : str , embedding_size : int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    # This function is to process text to validate text length
    def process_text(self , text : str):
        return text[:self.default_input_max_characters].strip()
    
    # This functio used to construct the prompt that will be sent to the LLM
    def construct_prompt(self , prompt : str , role : str):
        return {
            "role":role,
            "text":prompt
        }

    # This function is to generate text from the LLM
    def generate_text(self , prompt : str, 
                    chat_history : list =[],max_output_tokens: int = None , temperature : float = None):
        
        # Validate Client was set
        if not self.client:
            self.logger.error("CoHere client wasn't set.")
            return None

        # Validate generation model was set
        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere wasn't set")
            return None
        
        # Checking if there's max output tokens has been given or not , if not set it with its default value
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        
        # Checking if there's temperature has been given or not , if not set it with its default value
        temperature = temperature if temperature else self.default_generation_temperature

        # Getting the response from the LLM
        response = self.client.chat(model = self.generation_model_id ,
                                    chat_history = chat_history ,
                                    message = prompt,
                                    temperature = temperature,
                                    max_tokens = max_output_tokens)
        
        # Checking the return value from the response if there's no response , or it's length =0
        # If any of these return None
        if not response or not response.text or len(response.text)==0:
            self.logger.error("Error while generating text with CoHere")
            return None
        
        # Now if the response validated return its content
        return response.text
    
    # This function is to get text embeddings
    def embed_text(self , text: Union[str,List[str]], document_type : str = None):
        
        # Making sure the text is string , it it's append it to a list
        if isinstance(text , str):
            text = [text]

        # Validate the CoHere client was set
        if not self.client:
            self.logger.error("CoHere client wasn't set.")
            return None

        # Validate the embedding model client was set
        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere wasn't set")
            return None

        # Validate the input type given to the model , if it's query , if it's not then it's a document
        input_type = CoHereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnums.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        # Get the embedding from the LLM by sending the client the text
        response = self.client.embed(
            model=self.embedding_model_id,
            texts=[self.process_text(t) for t in text],
            input_type=input_type,
            embedding_types=['float']
        )

        # Validate response in some aspects
        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("Error while embedding text with cohere")
            return None
        
        # Return the embeddings if the response is validated
        return [f for f in response.embeddings.float]