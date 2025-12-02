# Creating a project model to manipulate assets in the database

# Importing the base data model to inherit from
from .BaseDataModel import BaseDataModel

# Import the schema of the project to validate data
from .db_schemas import Project

# Get the select statemnt to select from the database
from sqlalchemy.future import select

# Get the select function to execute function in the database
from sqlalchemy import func

# Creating the ProjectModel Class fo interactions with the database
class ProjectModel(BaseDataModel):
    
    # initialization for the class to set the database client
    def __init__(self,db_client : object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    # Creating a class method to create an object from the class using await
    @classmethod
    async def create_instance(cls , db_client : object):
        instance = cls(db_client)
        return instance
    
    # A function to create a project into the database
    async def create_project(self , project : Project):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            # Now begin the session to insert the project into the database
            async with session.begin():
                session.add(project)
            # Commiting our changes
            await session.commit()
            # Refreshing database to get freshed data
            await session.refresh(project)
        return project

    # A function to get the project or create it if there's not a one
    async def get_project_or_create_project(self , project_id : str):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            # Now begin the session to insert the project into the database
            async with session.begin():
                # Create the query we wish to execute
                query = await session.execute(select(Project).where(Project.project_id == project_id))
                # now execute the query
                project = query.scalar_one_or_none()
                # check if the query returned a record or not , if not create one and return it
                if project is None:
                    project_record = Project(project_id = project_id)
                    project = await self.create_project(project = project_record)
                return project

    # A function to get all projects that's in the database
    async def get_all_projects(self,page : int = 1 ,page_size : int = 10):

        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            # Now begin the session to insert the project into the database
            async with session.begin():
                # Create the statement and execute it to get
                total_documents = await session.execute(select(
                    func.count(Project.project_id)
                )).scalar_one()

                # Getting number of total pages
                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                # make the statement to select all projects and return them
                query = select(Project).offset(( page - 1 )* page_size).limit(page_size)
                projects = await session.execute(query).scalars.all()

                return projects , total_pages