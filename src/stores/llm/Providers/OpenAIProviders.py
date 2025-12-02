# Setting the OpenAI Provider

# Importing the LLMInterface to implement
from ..LLMInterface import LLMInterface

from openai import OpenAI
import logging
from ..LLMEnum import OpenAIEnums
from typing import List , Union

# Creating the class OpenAIProvider that implements the LLMInterface , with inheriting from it
class OpenAIProvider(LLMInterface):

    # Construct the class and give it all parameters needed
    def __init__(self , api_key : str , api_url : str = None,
                default_input_max_characters : int = 1000,
                default_generation_max_output_tokens : int = 1000,
                default_generation_temperature : float = 0.1):
        
        # Setting the class parameters 
        self.api_key=api_key
        self.api_url = api_url
        
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = OpenAI(api_key = self.api_key , base_url = self.api_url)
        self.enums = OpenAIEnums

        self.logger = logging.getLogger(__name__)

    # This function is to set the generation model by giving it the model id we will use from OpenAI
    def set_generation_model(self , model_id : str):
        self.generation_model_id = model_id
    
    # This function is to set the embedding model and its size 
    # by giving it the model id we will use from OpenAI and the embedding size
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
            "content":self.process_text(prompt)
        }

    # This function is to generate text from the LLM
    def generate_text(self , prompt : str, 
                    chat_history : list =[],max_output_token: int = None , temperature : float = None):
        
        # Validate client was set
        if not self.client:
            self.logger.error("OpenAI client wasn't set.")
            return None

        # Validate generation model was set
        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI wasn't set")
            return None

        # Checking if there's max output tokens has been given or not , if not set it with its default value
        max_output_token = max_output_token if max_output_token else self.default_generation_max_output_tokens
        
        # Checking if there's temperature has been given or not , if not set it with its default value
        temperature = temperature if temperature else self.default_generation_temperature

        # Constructing the chat history to give it to the model with the context
        chat_history.append(self.construct_prompt(prompt = prompt , role = OpenAIEnums.USER.value))

        # Getting the response from the LLM
        response = self.client.chat.completions.create(
            model = self.generation_model_id,
            messages= chat_history,
            max_tokens = max_output_token,
            temperature = temperature
        )

        # Checking the return value from the response if there's no choices , or it's length =0 or response 0 doesn't exist
        # If any of these return None
        if not response or not response.choices or len(response.choices) ==0 or not response.choices[0].message:
            self.logger.error("Error while generating text with OpenAI")
            return None
        
        # Now if the response validated return its content
        return response.choices[0].message["content"]
        
    
    # This function is to get text embeddings
    def embed_text(self , text: Union[str , List[str]], document_type : str = None):
        
        # Making sure the text is string , it it's append it to a list
        if isinstance(text,str):
            text = [text]

        # Validate the OpenAI client was set
        if not self.client:
            self.logger.error("OpenAI client wasn't set.")
            return None

        # Validate the embedding model client was set
        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI wasn't set")
            return None

        # Get the embedding from the LLM by sending the client the text
        response = self.client.embeddings.create(
            model = self.embedding_model_id,
            input = text
        )

        # Validate response in some aspects
        if not response or not response.data or len(response.data) ==0 or not response.data[0].embedding:
            self.logger.error("Error while embedding text with OpenAI.")
            return None
        
        # Return the embeddings if the response is validated
        return [record.embedding for record in response.data]