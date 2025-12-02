from helpers.config import get_settings,Settings
import os
import random
import string

# Building a Base controller for any other Controllers after this
class BaseController:

    # Initialization function to store settings
    def __init__(self):

        # Getting the configuration Settings
        self.app_settings = get_settings()
        self.base_dir=os.path.dirname(os.path.dirname(__file__))
        self.file_dir=os.path.join(self.base_dir,"assets/files")
        self.database_dir = os.path.join(self.base_dir,"assets/database")
    
    # This function is to generate a random string
    def generate_random_string(self, length: int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    # A function to get the database Path "If using Qdrant"
    def get_database_path(self, db_name : str):

        database_path = os.path.join(
            self.database_dir , db_name
        )
        
        if not os.path.exists(database_path):
            os.makedirs(database_path)

        return database_path