# Importing Base Controller for inheritance
from .BaseController import BaseController

from models.db_schemas import Project , DataChunk
from stores.llm.LLMEnum import DocumentTypeEnums
from typing import List
import json

class NLPController(BaseController):
    
    # Initialiazation function to initiate the super class
    # It's made if we need to broader the initialization of the project controller class
    def __init__(self,vectordb_client , generation_client , embedding_client , template_parser):
        
        super().__init__()

        # Setting th Vector database client , the generation client , the embedding client and the template parser
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    # Creating the collection name of the vectors in the database by combining the vector_size , the project_id
    # and the collection_ standart
    def create_collection_name(self , project_id : str):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    
    # Reseting the collection of the database by deleteing it if needed
    async def reset_vectordb_collection(self , project : Project):

        # We get the collection name we want to delete then delete it by the db client
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name=collection_name)

    # A function to get the collection info if we wanted
    async def get_vector_collection_info(self , project : Project):
        
        # We get the collection name we want to get its info about
        collection_name = self.create_collection_name(project_id = project.project_id)

        # Then we get it's info using the db client
        collection_info = await self.vectordb_client.get_collection_info(collection_name = collection_name)

        # We then transform it into a dictionary to be loaded as a json because the database object isn't serializable
        return json.loads(json.dumps(collection_info,default=lambda x : x.__dict__))
    
    # This function is for indexing chunks into the database
    async def index_into_vector_db(self , project : Project ,
                             chunks : List[DataChunk] ,
                             chunks_ids : List[int],
                             do_reset : bool = False):

        # Getting the collection name we want to save the chunks in for making the collection and saving the chunks
        collection_name = self.create_collection_name(project_id= project.project_id)

        # Now getting the texts of the chunks and the metadatas
        texts = [chunk.chunk_text for chunk in chunks]

        metadatas = [chunk.chunk_metadata for chunk in chunks]

        # Getting the vectors for each text in the texts list
        vectors = self.embedding_client.embed_text(text=texts,document_type = DocumentTypeEnums.DOCUMENT.value)

        # First before inserting the texts we create a collection in the database
        _ = await self.vectordb_client.create_collection(collection_name = collection_name , embedding_size = self.embedding_client.embedding_size, do_reset = do_reset)

        # Now inserting the chunks with its vectors in the database
        await self.vectordb_client.insert_many(collection_name = collection_name , texts = texts , metadata = metadatas , vectors = vectors , record_ids = chunks_ids)

        return True

    # This function is to search the vector database with the query of the user and return the most related 100 results
    async def search_vector_db_collection(self , project : Project , text : str , limit : int = 100):

        # Setting the query vectoy = None
        query_vector = None

        # Creating the collection name we want to search in
        collection_name = self.create_collection_name(project_id= project.project_id)

        # Now getting the vector of the query the user asked for
        vectors = self.embedding_client.embed_text(text , document_type = DocumentTypeEnums.QUERY.value)

        # Validation of the vectors existence and it's length
        if not vectors or len(vectors) == 0:
            return False
        
        # Validation if the vectors is already a list and has a length then setting the query vector as vector[0]
        # Because the embedding vectors consists of list of lists and has only one list in the second dimension
        if isinstance(vectors,List) and len(vectors) > 0:
            query_vector = vectors[0]

        # Validating the Query Vector existence
        if not query_vector:
            return False
        
        # Searching the vector database in the collection with the query vector and return the results
        results = await self.vectordb_client.search_by_vector(
            collection_name = collection_name,
            vector = query_vector,
            limit = limit
        )

        # Validating the results returned
        if not results:
            return False

        # If there are results then return it
        return results
    
    # This function is to answer the query of the user
    async def answer_rag_question(self,project : Project , query : str , limit : int = 10):
        
        # Setting initial values for answer , full prompt and chat history
        answer , full_prompt , chat_history = None , None , None

        # Now retrieve the related documents to the user query
        retrieved_documents = await self.search_vector_db_collection(project= project , text= query , limit = limit)


        # If there's and error with the retrieved documents return these None Values
        if not retrieved_documents or len(retrieved_documents) ==0:
            return answer , full_prompt , chat_history
        
        # Setting the system promt with the template parser values , Defines assistant behavior
        system_prompt = self.template_parser.get("rag" , "system_prompt")

        # Setting the document prompts with the template parser values , define document shape
        document_prompts = "\n".join([
            self.template_parser.get("rag" , "document_prompt",{
                "doc_num" : idx+1,
                "chunk_text" : self.generation_client.process_text(doc.text)
            })
            for idx , doc in enumerate(retrieved_documents)
        ])

        # Setting the footer prompt with the template parser values , injecting the query of the user
        footer_prompt = self.template_parser.get("rag" , "footer_prompt",{
            "query" : query,
            
        })

        # Construciton chat history if there's one
        chat_history = [
            self.generation_client.construct_prompt(
                prompt = system_prompt ,
                role = self.generation_client.enums.SYSTEM.value
            )
        ]

        # Now construct the full prompt to be sent to the llm
        full_prompt = "\n\n".join([ document_prompts , footer_prompt ])

        # Getting the answer from the LLM to send back to the user
        answer = self.generation_client.generate_text(
            prompt = full_prompt,
            chat_history = chat_history
        )

        # Now to the user send back the answer , the full prompt and the chat history
        return answer , full_prompt , chat_history
    
    # This function is to answer the query of the user
    async def answer_any_question(self , document : str):
        
        # Setting initial values for answer , full prompt and chat history
        answer , chat_history = None , None
        
        # Setting the system promt with the template parser values , Defines assistant behavior
        stories_prompt = self.template_parser.get("rag" , "stories_prompt")

        # Setting the footer prompt with the template parser values , injecting the query of the user
        story_footer_prompt = self.template_parser.get("rag" , "story_footer_prompt",{"document_text" : document})

        # Construciton chat history if there's one
        chat_history = [
            self.generation_client.construct_prompt(
                prompt = stories_prompt,
                role = self.generation_client.enums.SYSTEM.value
            )
        ]
        # Getting the answer from the LLM to send back to the user
        answer = self.generation_client.generate_text(
            prompt = story_footer_prompt,
            chat_history = chat_history
        )
        # Now to the user send back the answer , the full prompt and the chat history
        return answer