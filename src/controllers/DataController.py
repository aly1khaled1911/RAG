from fastapi import UploadFile

# Importing Base Controller to inherit from
from .BaseController import BaseController

# Importing Project Controller to use later
from .ProjectController import ProjectController
from models import ResponseSignal
import re , os


class DataController(BaseController):

    # Initialiazation function to initiate the super class
    # It's made if we need to broader the initialization of the project controller class
    def __init__(self):
        super().__init__()
        self.size_scale=1048576
    
    # Validation uploaded file if its type is supported in the files configuration and it's size also
    def validate_uploaded_file(self,file : UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False , ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        if file.size > (self.app_settings.FILE_MAX_SIZE * self.size_scale):
            return False , ResponseSignal.FILE_SIZE_EXCEEDED.value
        return True , ResponseSignal.FILE_VALIDATE_SUCCESS.value
    
    # Generating a unique file path for every file uploaded
    def generate_unique_filepath(self, original_file_name : str , project_id : str):

        # Generating random key value
        random_key = self.generate_random_string()
        
        # For the project which will the file be saved in , we get its path
        project_path=ProjectController().get_project_path(project_id=project_id)
        
        # Cleaning the file name to get a file name cleaned of any unknown characters
        cleaned_filename=self.get_clean_filename(original_file_name=original_file_name)
        
        # Now construct the new file path by adding the project path, the random key and the cleaned file name
        new_file_path = os.path.join(project_path,random_key+"_"+cleaned_filename)
        
        # Making sure that the path doesn't exist m and if it does we generate a random key again and consturct the file name again
        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(project_path,random_key+"_"+cleaned_filename)
        
        # Returning the file name
        return new_file_path ,random_key+"_"+cleaned_filename

    # Making a clean file name for the original file
    def get_clean_filename(self,original_file_name : str):
        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', original_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")
        return cleaned_file_name