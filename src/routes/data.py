from fastapi import FastAPI , APIRouter,Depends ,UploadFile , status , Request , File
from fastapi.responses import JSONResponse
from typing import List
import os
from helpers.config import get_settings , Settings
from controllers import DataController , ProjectController , ProcessController , NLPController
import aiofiles
from models import ResponseSignal
import logging
from .schemas.data import ProcessRequest
from models.db_schemas import DataChunk , Asset
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.enums.AssetTypeEnum import AssetTypeEnum


logger=logging.getLogger('uvicorn.error')

# Setting the router for all api/v1/data endpoints
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"]
)

# Making an endpoint post request for this router to upload the pdf file  , The function gets injected with settings
@data_router.post("/upload/{project_id}")
async def upload_data(request : Request,project_id: int, files : List[UploadFile] = File(...),
                      app_settings : Settings = Depends(get_settings)):

    # Creating project model to get project from db or create the project into the database
    project_model=await ProjectModel.create_instance(db_client=request.app.db_client)
    
    # Creating an asset model to store the file information into the database
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_project(project_id=project_id)
    
    # Creating data controller instance to help make necessary operations for the file uploaded
    data_controller=DataController()

    uploaded_files = []


    for file in files:

        # Checking if the uploaded file in a valid file
        is_valid , result_signal =data_controller.validate_uploaded_file(file=file)

        # If the file is not valid : return a json response with a bad request telling this file is invalid
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal" : result_signal
                }
            )
        
        # Giving the file a unique ID and a unique path by generating them
        file_path , file_id =data_controller.generate_unique_filepath(original_file_name=file.filename,project_id=project_id)
        
        # Opening the file and saving it chunk by chunk , and if there's an error return a json response with a bad request
        try:
            async with aiofiles.open(file_path,"wb") as f:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
        except Exception as e:
            logger.error(f"error while uploading file : {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal" : result_signal
                }
            )
        
        # Creating an Asset resource to be inserted into the database
        asset_resource = Asset(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )

        # Using the asset_model created to insert the asset information into the database and return asset record as a flag
        asset_record = await asset_model.create_asset(asset=asset_resource)
        uploaded_files.append({
            "original_name": file.filename,
            "file_id": str(asset_record.asset_id)
        })

    # Return a json response to the API to tell the user the file is uploaded successfully
    return JSONResponse(
            content={
                "signal" : ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                "files": uploaded_files
            }
        )
    

# Making an endpoint post process request for this router to process the pdf file
@data_router.post("/process_file_chunks/{project_id}")

# Making sure the function gets the request body of the process request
async def process_file_chunks(request : Request,project_id : int, process_request : ProcessRequest):

    # storing the parameters into variables to use it later
    file_id=process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset=process_request.do_reset

    # Creating instances for chunks , projects and assets to be stored in the database
    chunk_model=await ChunkModel.create_instance(db_client=request.app.db_client)
    project_model=await ProjectModel.create_instance(db_client=request.app.db_client)
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    # Creating or getting a project with the given project ID to process the chunks
    project = await project_model.get_project_or_create_project(project_id=project_id)

    # Making controller to access all functions needed to process the file and making it embeddings
    process_controller = ProcessController(project_id = project_id)
    nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                   generation_client=request.app.generation_client,
                                   embedding_client= request.app.embedding_client,
                                   template_parser= request.app.template_parser)
    

    # Getting all file ids in the project to process them all
    project_file_ids={}

    # If the file ID in the process request getting the asset record for this file from the database
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id = project.project_id ,
            asset_name = process_request.file_id)

    # If there's not any asset record with this file ID , return a bad request , we can't process a file that's not existed
        if asset_record is None :
            return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal": ResponseSignal.FILE_ID_ERROR.value
            }
        )

    # For the project we get all the files IDs in it and their names , It nearly is a one record
        project_file_ids = {
            asset_record.asset_id : asset_record.asset_name,
            
        }
    # if there's no file ID in the request then we will process all the files
    else:
        project_files = await asset_model.get_all_project_assets(asset_project_id = project.project_id)
        project_file_ids = { record.asset_id : record.asset_name for record in project_files}
    
    # If there isn't any file in the asset , also return a bad request that the project hasn't any file in it
    if len(project_file_ids ) == 0:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal": ResponseSignal.NO_FILES_ERROR.value
            }
        )

    # the do reset flag we gets from the API , If it's one , we will delete the collection associated with this project
    # And also we will delete the chunks associated with this project before inserting any
    if do_reset == 1:

        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)
        
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)

    no_records = 0
    no_files = 0

    # Now for every file in the project we will process it
    for asset_id , file_id in project_file_ids.items():
        # Getting the file content using the process controller
        file_content = process_controller.get_file_content(file_id=file_id)

        # If the file content is None we will return an error and continue for the other file
        if file_content is None:
            logger.error(f"Error while processing file : {file_id}")
            continue
        
        # Now getting the file chunks by process the file content
        file_chunks=process_controller.process_file_content_chunks(file_content=file_content , file_id=file_id,chunk_size=chunk_size,overlap_size=overlap_size)
        
        # Another validation if the file chunks is None or len ==0
        # Return a json respone with a bad request that the processing failed
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal" : ResponseSignal.PROCESSING_FAILED.value}
            )
        
        # If we have chunks now we create it as the DataChunk scheme we agreed upon to be inserted into the data base
        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order= i+1,
                chunk_project_id=project.project_id,
                chunk_asset_id = asset_id
                
            )
            for i,chunk in enumerate (file_chunks)
        ]

        # Now insert the chunks and increase the number of records inserted to complete for another file
        # Also increasing the number of files processed
        no_records += await chunk_model.insert_many_chunks(file_chunks_records)
        no_files +=1

    # Now returning a json response that the fiels has been successfullu inserted
    return JSONResponse({
        "content":{"signal" : ResponseSignal.PROCESSING_SUCCESS.value},
        "inserted_chunks":no_records,
        "processed_file" : no_files
    })

# Making an endpoint post process request for this router to process the pdf file
@data_router.post("/process_file/{project_id}")

# Making sure the function gets the request body of the process request
async def process_file(request : Request,project_id : int, process_request : ProcessRequest):

    # storing the parameters into variables to use it later
    file_id=process_request.file_id
    do_reset=process_request.do_reset

    # Creating instances for chunks , projects and assets to be stored in the database
    chunk_model=await ChunkModel.create_instance(db_client=request.app.db_client)
    project_model=await ProjectModel.create_instance(db_client=request.app.db_client)
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    # Creating or getting a project with the given project ID to process the chunks
    project = await project_model.get_project_or_create_project(project_id=project_id)

    # Making controller to access all functions needed to process the file and making it embeddings
    process_controller = ProcessController(project_id = project_id)
    nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                   generation_client=request.app.generation_client,
                                   embedding_client= request.app.embedding_client,
                                   template_parser= request.app.template_parser)
    

    # Getting all file ids in the project to process them all
    project_file_ids={}

    # If the file ID in the process request getting the asset record for this file from the database
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id = project.project_id ,
            asset_name = process_request.file_id)

    # If there's not any asset record with this file ID , return a bad request , we can't process a file that's not existed
        if asset_record is None :
            return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal": ResponseSignal.FILE_ID_ERROR.value
            }
        )

    # For the project we get all the files IDs in it and their names , It nearly is a one record
        project_file_ids = {
            asset_record.asset_id : asset_record.asset_name,
            
        }
    # if there's no file ID in the request then we will process all the files
    else:
        project_files = await asset_model.get_all_project_assets(asset_project_id = project.project_id)
        project_file_ids = { record.asset_id : record.asset_name for record in project_files}
    
    # If there isn't any file in the asset , also return a bad request that the project hasn't any file in it
    if len(project_file_ids ) == 0:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal": ResponseSignal.NO_FILES_ERROR.value
            }
        )

    # the do reset flag we gets from the API , If it's one , we will delete the collection associated with this project
    # And also we will delete the chunks associated with this project before inserting any
    if do_reset == 1:

        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)
        
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)

    no_records = 0
    no_files = 0

    # Now for every file in the project we will process it
    for asset_id , file_id in project_file_ids.items():
        # Getting the file content using the process controller
        file_content = process_controller.get_file_content(file_id=file_id)

        # If the file content is None we will return an error and continue for the other file
        if file_content is None:
            logger.error(f"Error while processing file : {file_id}")
            continue
        
        # Now getting the file chunks by process the file content
        file_chunk=process_controller.process_file_content_all(file_content=file_content , file_id=file_id)
        
        # Another validation if the file chunks is None or len ==0
        # Return a json respone with a bad request that the processing failed
        if file_chunk is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal" : ResponseSignal.PROCESSING_FAILED.value}
            )
        
        # If we have chunks now we create it as the DataChunk scheme we agreed upon to be inserted into the data base
        file_chunk =DataChunk(
                chunk_text=file_chunk.page_content,
                chunk_metadata=file_chunk.metadata,
                chunk_type = 'Document',
                chunk_order= 0,
                chunk_project_id=project.project_id,
                chunk_asset_id = asset_id)

        # Now insert the chunks and increase the number of records inserted to complete for another file
        # Also increasing the number of files processed
        
        await chunk_model.insert_chunk(chunk=file_chunk)
        no_records+=1
        no_files +=1

    # Now returning a json response that the fiels has been successfullu inserted
    return JSONResponse({
        "content":{"signal" : ResponseSignal.PROCESSING_SUCCESS.value},
        "inserted_chunks":no_records,
        "processed_file" : no_files
    })
