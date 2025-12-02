# Creating a factory to handle LLMs interfacing

# Importing LLM enums and all providers we have to switch from
from .LLMEnum import LLMEnums
from .Providers.OpenAIProviders import OpenAIProvider
from .Providers.CohereProvider import CoHereProvider

# Create an LLM Provider Factory Class to handle which provider we will use
class LLMProviderFactory:
    
    # Construct the class with setting configurations and giving it to the class
    def __init__(self,config : dict):
        self.config=config
    
    # Now selecting which provider according to the environment variable
    # Whether it's OpenAI provider or CoHere provider
    def create(self,provider : str):

        # Now checking what is given , and setting the provider according to this parameter
        if provider == LLMEnums.OPENAI.value:
             
             # If it's OpenAI , return OpenAIProvider
             return OpenAIProvider(
                 api_key = self.config.OPENAI_API_KEY, 
                 api_url = self.config.OPENAI_API_URL,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE

             )
        
        if provider == LLMEnums.COHERE.value:
             
             # If it's CoHere , return CoHereProvider
             return CoHereProvider(
                 api_key = self.config.COHERE_API_KEY, 
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
             )
        
        # if provider isn't supported , return None
        return None
