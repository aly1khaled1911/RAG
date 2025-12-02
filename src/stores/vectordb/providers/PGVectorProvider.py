# Setting the PGVector Provider

# Importing the VectorDBInterface to implement
from ..VectorDBInterface import VectorDBinterface

from ..VectorDBEnums import PgVectorDistanceMethonEnums , PgVectorIndexTypeEnums , PgVectorTableSchemeEnums , DistanceMethodEnums
import logging
from typing import List
from models.db_schemas import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json

# Creating the class PGVectorDBProvider that implements the VectorDBInterface , with inheriting from it
class PGVectorProvider(VectorDBinterface):

    # Construct the class and give it all parameters needed
    def __init__(self, db_client, default_vector_size : int = 786 , distance_method : str = None,index_threshold : int = 100):
        
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold

        if distance_method == DistanceMethodEnums.COSINE.value:
            distance_method = PgVectorDistanceMethonEnums.COSINE.value
        else:
            distance_method = PgVectorDistanceMethonEnums.DOT.value

        self.distance_method = distance_method

        self.pgvector_table_prefix = PgVectorTableSchemeEnums._PREFIX.value
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"

        self.logger = logging.getLogger("uvicorn")


    # Setting the connect function to connect to the vector database
    async def connect(self):

        # Setting the database client as session
        async with self.db_client() as session:

            # Begin the session to connect
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))
                await session.commit()
    
    # A function to disconenct from the database
    async def disconnect(self):
        pass
    
    # Checking if a collection exists or not
    async def is_collection_existed(self, collection_name):
        
        # set the record with none
        record = None
        
        # Setting the database client as session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():
                
                # Prepare the query for execution
                list_table = sql_text(f"SELECT * FROM pg_tables WHERE tablename = :collection_name")

                # Execute the query for results whether the collection existed or not
                results = await session.execute(list_table,{"collection_name":collection_name})

                # get the result object and save it to record
                record = results.scalar_one_or_none()
        
        # Retrun the flag
        return record
    
    # A function to list all collections in the vector database
    async def list_all_collections(self):
        
        # Setting the list where the data will be saved
        records = []
        
        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                # Prepare the query that will be executed
                all_tables = sql_text("SELECT table_name FROM pg_tables WHERE table_name LIKE :prefix")

                # Execute the query and save the results object
                results = await session.execute(all_tables,{"prefix" : self.pgvector_table_prefix})

                # Get the results object and save it to records
                records = results.scalar().all()
                
        return records
    
    # A functio to get all collection info
    async def get_collection_info(self, collection_name):

        # Validating first that the collection existed
        if not await self.is_collection_existed(collection_name=collection_name):
            return None

        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                # Prepare all queries that will be executed
                table_info_sql = sql_text(f"""
                                      SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                                      FROM pg_tables
                                      WHERE tablename = :collection_name
                                      """)
                count_sql = sql_text(f"SELECT COUNT (*) FROM {collection_name}")

                # Execute the queries and save the object results
                table_info = await session.execute(table_info_sql,{"collection_name":collection_name})
                record_count = await session.execute(count_sql)

                # save the results of the table info
                table_info = table_info.fetchone()
                
                # Return the collection info we retrieved
                return {
                    "table_info" :{"schemaname":table_info[0],
                    "tablename":table_info[1],
                    "tableowner":table_info[2],
                    "tablespace":table_info[3],
                    "hasindexes":table_info[4]},
                    "record_count" : record_count.scalar_one()
                }

    # A function to delete a collection from the vector database
    async def delete_collection(self, collection_name):

        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                # Log a message that the collection is being deleted
                self.logger.info(f"Deleting Collection {collection_name}")

                # Prepare the statement that will be executed
                delete_sql = sql_text(f"DROP TABLE IF EXISTS {collection_name}")

                #Execute teh statement and commit our changes
                await session.execute(delete_sql)
                await session.commit()
        
        return True
    
    # A function to create a collection
    async def create_collection(self, collection_name, embedding_size, do_reset = False):
        
        # Checking if the collection existed first and the do reset is up , delete the collection
        if do_reset:
           _ = await self.delete_collection(collection_name=collection_name)

        # Checking if the collection wanted to be created existed or not
        if not await self.is_collection_existed(collection_name=collection_name):
            
            # Log a message that the collection is being created
            self.logger.info(f"Creating collection {collection_name}")

            # Setting our vector database client as our session
            async with self.db_client() as session:

                # Begin the session execute queries
                async with session.begin():

                    # Prepare the query that will be executed
                    create_sql = sql_text(f"CREATE TABLE {collection_name} ("
                                          f"{PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY,"
                                          f"{PgVectorTableSchemeEnums.TEXT.value} text,"
                                          f"{PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}), "
                                          f"{PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\', "
                                          f"{PgVectorTableSchemeEnums.CHUNK_ID.value} integer,"
                                          f"FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)"
                                          ")")
                    
                    # Execute the queries and commit our changes
                    await session.execute(create_sql)
                    await session.commit()
            return True
        return False

    # Checking if there's andy index has been made to a specific table
    async def is_index_existed(self , collection_name : str):

        # Setting the default index name using the function "default_index_name"
        index_name = self.default_index_name(collection_name=collection_name)

        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                # Prepare the query that will be executed
                chech_sql = sql_text(f"""
                                    SELECT 1 FROM pg_indexes WHERE tablename = :collection_name AND indexname = :index_name
                                    """)
                
                # Execute the query and commit get our results
                results = await session.execute(chech_sql,{"collection_name":collection_name,"index_name":index_name})

                # Return a flag whether if the index existed or not
                return bool(results.scalar_one_or_none())

    # A function to create an index for a specific collection table
    async def create_vector_index(self ,collection_name:str,
                                        index_type : str = PgVectorIndexTypeEnums.HNSW.value):
        
        # Checking first if the index existed or not
        is_index_existed = await self.is_index_existed(collection_name=collection_name)

        # Return False if index already existed
        if is_index_existed:
            return False
        
        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():
                
                # Prepare the query that will be executed
                count_sql = sql_text(f"SELECT COUNT (*) FROM {collection_name}")
                
                # Execute the query and return its result
                result = await session.execute(count_sql)
                
                # Get the counts from that query
                counts = result.scalar_one()

                # Check if the counts is less than the index_threshould , because it's not necessary to
                # implement the index if the number of rows is small and return false if it's less
                # than the index
                if counts < self.index_threshold:
                    return False
                
                # After validation , now we're ready to create the index
                # Log a message that the index is being created
                self.logger.info(f"START : Creating index vector for collection: {collection_name}")

                # Perpare the index name we want to make
                index_name = self.default_index_name(collection_name=collection_name)

                # Prepare the statement for creating that index and give it the index type
                create_idx_sql = sql_text(
                    f"CREATE INDEX {index_name} ON {collection_name} "
                    f"USING {index_type} ({PgVectorTableSchemeEnums.VECTOR.value} {self.distance_method})"
                    )
                
                # Execute the query that creates the index
                await session.execute(create_idx_sql)

                # Log a message that the index has been created
                self.logger.info(f"END : Created index vector for collection : {collection_name}")


    # A function to reset vector index
    async def reset_vector_index(self , collection_name : str , index_type : str =PgVectorIndexTypeEnums.HNSW.value):

        # Prepare the index name we want to update
        index_name = self.default_index_name(collection_name=collection_name)

        
        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                ## Prepare the query that will  delete the index
                drop_sql = sql_text(f"DROP INDEX IF EXISTS {index_name}")

                # Execute the query
                await session.execute(drop_sql)

        # Creating the index again
        return await self.create_vector_index(colleciton_name=collection_name,index_type=index_type)


    # A function to insert a record into the collection ( the table )
    async def insert_one(self, collection_name, text, vector, metadata = None, record_id = None):
        
        # Validating that the collection is already existed before inserting any records
        if not await self.is_collection_existed(collection_name=collection_name):

            # If the collection doesn't exist log a message that the record can't be inserted
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        # Validating the rocord Id before inserting
        if not record_id:

            # If the record Id doesn't exist log a message that a new record can't be inserted withoud its Id
            self.logger.error(f"Can not insert new record without chunk_id: {collection_name}")
            return False

        
        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                # Prepare the query that will be executed to insert a new record
                insert_sql = sql_text(f"INSERT INTO {collection_name} "
                                        f"({PgVectorTableSchemeEnums.ID.value},{PgVectorTableSchemeEnums.TEXT.value},{PgVectorTableSchemeEnums.VECTOR.value},{PgVectorTableSchemeEnums.METADATA.value},{PgVectorTableSchemeEnums.CHUNK_ID.value}),"
                                        "VALUES (:text, :vector, :metadata, :chunk_id)"
                                        )
                # Construct the metadata that will be inserted with the record
                metadata_json = json.dumps(metadata,ensure_ascii=False) if metadata is not None else "{}"

                # Execute the query that will insert the record
                await session.execute(insert_sql,{
                    "text":text,
                    "vector":"[" + ",".join([str(v) for v in vector]) +"]",
                    "metadata":metadata_json,
                    "chunk_id":record_id
                })
                # Commit the changes
                session.commit()

                # Checking if we can make an index now or not
                await self.create_vector_index(colleciton_name=collection_name)
        return True
    
    # A function to insert many records in the vector database
    async def insert_many(self, collection_name, texts, vectors, metadata = None, record_ids = None, batch_size = 50):
        

        # Validating if a collection existed or not
        if not await self.is_collection_existed(collection_name=collection_name):
            
            # If the collection doesn't exist log a message , new records can't be inserted to non existed collection
            self.logger.error(f"Can not insert new records to non-existed collection: {collection_name}")
            return False
        
        # Validate the length of the records and the length of the vectors
        if len(vectors) != len(record_ids):

            # If they don't match , log a message that the data is invalid
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False
        
        # Tailor the metadata to the size of the texts
        if not metadata or len(metadata)==0:
            metadata = [None] * len(texts)
        
        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():
                
                # Constructing batches to be inserted into the database
                for enumerator in range(0,len(texts),batch_size):
                    batch_texts = texts[enumerator:enumerator+batch_size]
                    batch_vectors = vectors[enumerator:enumerator+batch_size]
                    batch_metadata = metadata[enumerator:enumerator+batch_size]
                    batch_record_ids = record_ids[enumerator:enumerator+batch_size]

                    # now constructing values to be replaced in the query
                    values = []

                    for _text , _vector , _metadata , _record_id in zip(batch_texts,batch_vectors,batch_metadata,batch_record_ids):
                        metadata_json = json.dumps(_metadata,ensure_ascii=False) if _metadata is not None else "{}"
                        values.append({
                            "text":_text,
                            "vector":"[" + ",".join([str(v) for v in _vector]) +"]",
                            "metadata":metadata_json,
                            "chunk_id":_record_id
                })

                    # Prepare the query that will be used to insert records to the vector database      
                    batch_insert_sql = sql_text(f"INSERT INTO {collection_name} "
                                        f"({PgVectorTableSchemeEnums.TEXT.value}, "
                                        f"{PgVectorTableSchemeEnums.VECTOR.value}, "
                                        f"{PgVectorTableSchemeEnums.METADATA.value}, "
                                        f"{PgVectorTableSchemeEnums.CHUNK_ID.value}) "
                                        f"VALUES (:text, :vector, :metadata, :chunk_id)")
                    
                    # Execute the query to insert the data
                    await session.execute(batch_insert_sql,values)

        # Create an index for this collection it there's not any and it's rows exceeds the threshold
        await self.create_vector_index(collection_name=collection_name)
        return True
    

    # A function to search in the vector database by the vector
    async def  search_by_vector(self, collection_name, vector, limit):
        
        # Validating if the collection exists or not first
        if not await self.is_collection_existed(collection_name=collection_name):

            # If the collection doesn't exist , log a message , cannot search records in a non existed collection
            self.logger.error(f"Can not search records in non-existed collection: {collection_name}")
            return False
        
        #constructing the vector that will be searched with
        vector = "[" + ",".join([str(v) for v in vector]) +"]"

        # Setting our vector database client as our session
        async with self.db_client() as session:

            # Begin the session execute queries
            async with session.begin():

                # Prepate the query that will search using the vector
                search_sql = sql_text(f"SELECT {PgVectorTableSchemeEnums.TEXT.value} as text, 1 - ({PgVectorTableSchemeEnums.VECTOR.value} <=> :vector) as score "
                                      f"FROM {collection_name} "
                                      f"ORDER BY score DESC "
                                      f"LIMIT {limit}"
                                      )
                
                # Execute the query and save results
                result = await session.execute(search_sql,{"vector":vector})

                # Turn the result object to records to response with them
                records = result.fetchall()

        # Return all retrieved documents and their score of the match with the vector
        return [
            RetrievedDocument(
                text = record.text,
                score = record.score
            )
            for record in records
        ]