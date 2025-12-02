# Importing Base Controller for inheritance and Project Controller for manipulation projects
from .BaseController import BaseController
from .ProjectController import ProjectController

from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from models import ProcessingEnums
import os
from typing import List
from dataclasses import dataclass

# Data Transfer Object DTO for using in database
@dataclass
class Document:
    page_content : str
    metadata : dict


class ProcessController(BaseController):
    
    # Initialiazation function to initiate the super class
    # It's made if we need to broader the initialization of the project controller class
    def __init__(self, project_id : str):
        super().__init__()
        
        self.project_id=project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
    
    # This function only gets the file extention if it's text or pdf
    def get_file_extension(self , file_id : str):
        return os.path.splitext(file_id)[-1]

    # Now according to the file extension we select the suitable loader for this file
    def get_file_loader(self , file_id : str):

        # Gets the file path then getting its extension
        file_path=os.path.join(self.project_path,file_id)
        file_ext = self.get_file_extension(file_id=file_id)

        # Validation for the path of the file
        if not os.path.exists(file_path):
            return None

        # Now checking which ectension for the loader and if the extenstion is not supported we return None
        if file_ext == ProcessingEnums.TXT.value:
            return TextLoader(file_path,encoding='utf-8')

        if file_ext == ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path)
        return None

    # Loading the file Content
    def get_file_content(self,file_id : str):

        # Now loading the file loader then load the file content by using the suitable loader
        # If the function didn't return a loader then teh function get_file_content return None 
        loader=self.get_file_loader(file_id=file_id)

        if loader :
            return loader.load()
        return None

    # Processing the file content by getting the output of the loader , then process its text and metadata
    # And return the output in chunks
    def process_file_content(self,file_content : list ,file_id : str , chunk_size : int=100 , overlap_size : int=20):
        file_content_text = [ rec.page_content for rec in file_content ]
        file_content_metadata = [ rec.metadata for rec in file_content ]
#       chunks=text_splitter.create_documents(file_content_text,metadatas = file_content_metadata)
        chunks = self.process_simpler_splitter(texts=file_content_text,metadatas=file_content_metadata,chunk_size=chunk_size)
        return chunks
    
    # Processing with a simple splitter by just chunking over each new paragraph with \n
    def process_simpler_splitter(self , texts : List[str],metadatas:List[dict],chunk_size : int,splitter_tag = "\n"):

        # We make all pages in one text
        full_text = " ".join(texts)

        # Now for each splitting in the full text we strip it and make sure there's no empty lines
        lines = [doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip())> 1]

        # Generate an empty text of chunks
        chunks = []

        # Start with an empty current chunk
        current_chunk = ""

        # For each line in the lines we add the line and the splitter tag for the current chunk
        # Then we make sure it's less than our chunk size
        # Then we append this chunk as a Document Data Class in the chunks list
        for line in lines :
            current_chunk += line + splitter_tag
            if len(current_chunk) >= chunk_size:
                chunks.append(Document(
                    page_content=current_chunk,
                    metadata={}
                ))

                current_chunk = ""
        # For the last chunk we save it if it's length is greater than 0
        if len(current_chunk) >= 0:
                chunks.append(Document(
                    page_content=current_chunk,
                    metadata={}
                ))

        # Now return all created chunks
        return chunks