# Creating a Chunk model to manipulate assets in the database

# Importing the base data model to inherit fromfrom .BaseDataModel import BaseDataModel
from .BaseDataModel import BaseDataModel

# Import the schema of the asset to validate data
from .db_schemas import DataChunk

# Get the select statemnt to select from the database
from sqlalchemy.future import select

# Get the select function to execute function in the database
from sqlalchemy import func , delete

# Import the ObjectID to validate funcitons input
from bson.objectid import ObjectId


# Creating the ChunkModel Class for interactions with the database
class ChunkModel(BaseDataModel):

    # initialization for the class to set the database client
    def __init__(self,db_client : object):
        super().__init__(db_client=db_client)
        self.db_client = self.db_client

    # Creating a class method to create an object from the class using await
    @classmethod
    async def create_instance(cls , db_client : object):
        instance = cls(db_client)
        return instance

    # A function to insert chunk into the database
    async def insert_chunk(self , chunk : DataChunk):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Now begin the session to insert the chunk into the database
            async with session.begin():
                session.add(chunk)

            # Commiting our changes
            await session.commit()

            # Refreshing database to get freshed data
            await session.refresh(chunk)

        return chunk
    
    # A function to get a chunk from the database
    async def get_chunk(self,chunk_id: str):

        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Now begin the session to get the chunk into the database
            async with session.begin():

                # Prepare the statement and execute the query to get the chunk
                result = await session.execute(select(DataChunk).where(DataChunk.chunk_id == chunk_id))
                chunk = result.scalar_get_one_or_none()
        return chunk
        

    # A function to the insert many chunks
    async def insert_many_chunks(self,chunks : list,batch_size : int =100):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Now begin the session to insert the asset into the database
            async with session.begin():

                # Loop over chunks to insert them in the batches then insert batcehs one by one
                for i in range(0,len(chunks),batch_size):
                    batch = chunks[i:i+batch_size]
                    session.add_all(batch)
            
            # Commit our changes then return length of all chunks
            await session.commit()
        return len(chunks)
        

    # A function to delete chunks by project ID , to delete all project related chunks
    async def delete_chunks_by_project_id(self,project_id : ObjectId):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Now begin the session to insert the asset into the database
            async with session.begin():

                # Prepare the statement and execute it to delete every chunk that's project Id is equal the project Id we take as a parameter
                result = await session.execute(delete(DataChunk).where(DataChunk.chunk_project_id == project_id))
            
            # Commiting our changes
            await session.commit()

        # Return how many rows were deleted from the database
        return result.rowcount
    

    # A function to get all project related chunks
    async def get_project_chunks(self,project_id : ObjectId , page_no : int = 1 , page_size : int = 50):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Now begin the session to insert the asset into the database
            async with session.begin():

                # Perpare the get statement to get chunks
                stmt = select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page_no -1) * page_size).limit(page_size)
                
                # Executing the statement and save the result
                result = await session.execute(stmt)

                # get all results and save them in records then return them
                records = result.scalars().all()
        return records
    

    # A function to count all chunks in a single project
    async def get_total_chunks_count(self , project_id : ObjectId):
        
        # Initiate the records count with zero to store the chunks count
        records_count = 0

        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Prepare the statement to count the chunks in a single project
            count_sql = select(func.count(DataChunk.chunk_id)).where(DataChunk.chunk_project_id == project_id)
            
            # Execute the statement and return the number of the cunks in record count then return them
            records_count = await session.execute(count_sql)
            records_count = records_count.scalar()

            return records_count