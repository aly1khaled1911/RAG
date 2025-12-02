# Importing Base Controller to inherit from

from .BaseController import BaseController
import os

class ProjectController(BaseController):

    # Initialiazation function to initiate the super class
    # It's made if we need to broader the initialization of the project controller class
    def __init__(self):
        super().__init__()

    # This function is to get the project local path and if it doesn't exist , we make a new one
    def get_project_path(self,project_id : str):
        project_dir=os.path.join(
            self.file_dir,
            str(project_id)
        )

        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        return project_dir