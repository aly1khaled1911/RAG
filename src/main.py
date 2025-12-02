from fastapi import FastAPI

from routes import base
from routes import data
from routes import nlp

from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine , AsyncSession
from sqlalchemy.orm import sessionmaker


app=FastAPI()

# Making the Start-Up Function which initiatlize every possible variable
@app.on_event("startup")
async def startup_span():

    # Getting Settings and credientials from the settings class which contains environment variables
    settings=get_settings()

    # Initializing data base connection
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}" 
    
    # Creating Async Engine to make ORM sessions
    app.db_engine = create_async_engine(postgres_conn)

    # Using the engine to create async session for database operations , expire on commit keeps the session on even after commiting
    app.db_client=sessionmaker(
        app.db_engine, class_ = AsyncSession , expire_on_commit = False
        )

    # Creating the factory instance for the LLM provider
    llm_provider_factory = LLMProviderFactory(settings)

    # Creating the factory instance for the vector database provider
    vectordb_provider_factory = VectorDBProviderFactory(config = settings,db_client=app.db_client)


    # Generation_client , creating the generation client from the provider and setting the model ID for it
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)

    # Embedding_client , creating the embedding client from the provider and setting the model ID and the embedding size for it
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id = settings.EMBEDDING_MODEL_ID,
                                             embedding_size = settings.EMBEDDING_MODEL_SIZE)
    

    # Vectordb_client , creating the vector database client and connect to this client giving the chosen vector database back end then connecting to it
    app.vectordb_client=vectordb_provider_factory.create_provider(provider=settings.VECTOR_DB_BACKEND)
    await app.vectordb_client.connect()

    # Templates , setting the language for the template for the llm
    app.template_parser = TemplateParser(language = settings.PRIMARY_LANGUAGE , default_language = settings.DEFAULT_LANGUAGE) 

# Define shutdown events like cleaning the database connection and the vector database connection
@app.on_event("shutdown")
async def shutdown_span():
    app.db_engine.dispose()
    await app.vectordb_client.disconnect()




# Registering routers to the main app
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)