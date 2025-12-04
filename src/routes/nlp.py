from fastapi import FastAPI , APIRouter, status , Request
from fastapi.responses import JSONResponse
import logging
from routes.schemas.nlp import PushRequest , SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal
from tqdm.auto import tqdm


logger = logging.getLogger('uvicorn.error')

# Setting the router for all api/v1/nlp endpoints
nlp_router = APIRouter(
    prefix = '/api/v1/nlp',
    tags = ["api_v1","nlp"]
)
# Making an endpoint post request for this router to push and index chunks
@nlp_router.post("/index/push/{project_id}")

# This is the function for indexing every chunk in the project in the vector database
async def index_project(request : Request,project_id : int , push_request : PushRequest):

    # Creating a project model and a chunk model to help integrate with the database 
    project_model = await ProjectModel.create_instance(db_client = request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client = request.app.db_client)
    
    # Getting the project itself or create it if it's not existed but here we get it
    project = await project_model.get_project_or_create_project(
        project_id = project_id
    )

    # If the project ID is invalid , return a json response with a bad request with project not found
    if not project:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal" : ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )

    # Initiating the NLP Controller to do necessary functions with it
    nlp_controller = NLPController(
        vectordb_client= request.app.vectordb_client,
        generation_client = request.app.generation_client,
        embedding_client = request.app.embedding_client,
        template_parser = request.app.template_parser
        )
    
    # Initiating Variabled for counting pages , and inserted items counts
    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx=0

    # Creating a collection name with the the project ID
    collection_name = nlp_controller.create_collection_name(project_id=project.project_id)

    # Inserting the collection in the vector database
    _ = await request.app.vectordb_client.create_collection(
        collection_name=collection_name,
        embedding_size = request.app.embedding_client.embedding_size,
        do_reset = push_request.do_reset
    )


    # Now this is the progress bar created to go along with the number of chunks inserted over processing time
    total_chunks_count = await chunk_model.get_total_chunks_count(project_id = project.project_id)
    print("total chunks is -------------------",total_chunks_count)
    pbar = tqdm(total=total_chunks_count, desc= "Vector Indexing",position=0)

    # The loop to insert the chunks into the database
    while has_records:
        # First is making sure how many chunks pages in the database
        page_chunks = await chunk_model.get_project_chunks(project_id = project.project_id,page_no=page_no)
        
        # If already there's chunks we will increase page_chunks by 1
        if len(page_chunks):
            page_no+=1
        
        # If there's not a single page in the database , we will trun the has_records flag off and break the while
        # As there aren't records in the project to be inserted in the vector database
        if not page_chunks or len(page_chunks)==0:
            has_records=False
            break
        
        # Now there are chunks in the project then we get their indices and increment the idx of the pages
        chunk_ids = [c.chunk_id for c in page_chunks]
        idx += len(page_chunks)

        # Inserting all chunks in the vector database and return a flag of the inserting status
        is_inserted = await nlp_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            chunks_ids = chunk_ids
        )

        # If there's an error with the inserting approach return a json response with bad request to indicate
        # ther's a failure inserting chunks
        if not is_inserted :
            return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal" : ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value
            }
        )
        # Update the progress bar as it's shown to us and increment the inserted items counts
        pbar.update(len(page_chunks))
        inserted_items_count += len(page_chunks)

    # Finally return a json response that's the process has ended and the number of chunks inserted
    return JSONResponse(
        content = {
            "signal": ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            "inserted_items_count" : inserted_items_count
        }
    )

# Making an endpoint get request for this router to get collection info
@nlp_router.get("/index/info/{project_id}")

# This is the function gets the project index info by givin it the project ID
async def get_project_index_info(request : Request,project_id : int):
    
    # Creating the project model to integrate with the database
    project_model = await ProjectModel.create_instance(
        db_client = request.app.db_client
    )

    # Getting the project to search for it's info in the database
    project = await project_model.get_project_or_create_project(
        project_id = project_id
    )

    # Making an NLP Controller to integrate with the vector database
    nlp_controller = NLPController(
        vectordb_client= request.app.vectordb_client,
        generation_client = request.app.generation_client,
        embedding_client = request.app.embedding_client,
        template_parser = request.app.template_parser
        )
    
    # Getting the collection info by searching the vector database to return it to the user
    collection_info = await nlp_controller.get_vector_collection_info(project=project)


    # Return a Json Response with the info of the collection and a signal that's the process is successfully done
    return JSONResponse(
        content = {
            "signal" : ResponseSignal.VECTOR_DB_COLLECTION_INFO_RETRIEVED.value,
            "collection_info": collection_info
        }
    )


# Making an endpoint post request for this router to search vectors by similarity
@nlp_router.post("/index/search/{project_id}")

#This is the function to search by similarity
async def search_index(request : Request , project_id : int , search_request : SearchRequest):
    
    # Creating the project model to integrate with the database
    project_model = await ProjectModel.create_instance(
        db_client = request.app.db_client
    )

    # Getting the project to search in its vectors
    project = await project_model.get_project_or_create_project(
        project_id = project_id
    )

    # Making an NLP Controller to integrate with the vector database
    nlp_controller = NLPController(
        vectordb_client= request.app.vectordb_client,
        generation_client = request.app.generation_client,
        embedding_client = request.app.embedding_client,
        template_parser = request.app.template_parser
        )
    
    # Search the vector database for relative results with cosine similarity to get relative texts
    results = await nlp_controller.search_vector_db_collection(project=project,text = search_request.text , limit = search_request.limit)
    

    # If there's not any search result , this will return a JSON Response with bad request
    if not results:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal" : ResponseSignal.VECTORDB_SEARCH_ERROR.value
            }
        )

    # If there's results already we make it dictionaties for score and the text itself
    results = [result.dict() for result in results]

    # We then return a JSOM response with the results and a flad indicating the operation success
    return JSONResponse(
        content = {
            "signal" : ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "results": results
        }
    )

# Making an endpoint post request for this router to answer the queries
@nlp_router.get("/index/answer/{project_id}")


#This is the function to answer the query
async def search_index(request : Request , project_id : int , search_request : SearchRequest):

    # Creating the project model to integrate with the database
    project_model = await ProjectModel.create_instance(
        db_client = request.app.db_client
    )
    # Getting the project to search in its vectors
    project = await project_model.get_project_or_create_project(
        project_id = project_id
    )

    # Making an NLP Controller to integrate with the vector database
    nlp_controller = NLPController(
        vectordb_client= request.app.vectordb_client,
        generation_client = request.app.generation_client,
        embedding_client = request.app.embedding_client,
        template_parser = request.app.template_parser
        )
    
    # Now using the answer_rag_question function we send the query and the project and the limit
    # to get the search results and give them to the LLM then the LLM answers it and give us the response back
    answer , full_prompt , chat_history = await nlp_controller.answer_rag_question(project= project ,
                                                                             query= search_request.text ,
                                                                             limit = search_request.limit)
    
    
    # If there's no answer from the database we send a Json response with bad request
    if not answer:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal" : ResponseSignal.RAG_ANSWER_ERROR.value
            }
        )
    
    # Now having the answer from the LLM , we send a Json response with the answer of the LLM 
    # and the chat history and also the full prompt and a flag indicating the process was successfull
    return JSONResponse(
            content = {
                "Signal" : ResponseSignal.RAG_ANSWER_SUCCESS.value,
                "Answer" : answer,
                "Chat History" : chat_history,
                "Full Prompt" : full_prompt
            }
        )
