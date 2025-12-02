# Create a Base Data model to inherit from in every data class for manipulating database
from helpers.config import get_settings,Settings

# Creating the model and taking as initialization the database client to interface with the database
class BaseDataModel:
    def __init__(self,db_client : object):
        self.db_client=db_client
        self.app_settings=get_settings()