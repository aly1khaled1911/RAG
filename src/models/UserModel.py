# Creating an asset model to manipulate assets in the database

# Importing the base data model to inherit from
from .BaseDataModel import BaseDataModel

from .db_schemas import User

from .enums.RolesEnum import Roles

# Get the select statment to select from the database
from sqlalchemy.future import select

# Get the select function to execute function in the database
from sqlalchemy import func , delete

# Creating the AssetModel Class for interactions with the database
class UserModel(BaseDataModel):

    # initialization for the class to set the database client
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    # Creating a class method to create an object from the class using await
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    # A function to create an asset into the database
    async def create_user(self, email : str , password : str , role : Roles):

        user = User()
        user.user_email = email
        user.user_password = password
        user.user_role = role
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            # Now begin the session to insert the asset into the database
            async with session.begin():
                session.add(user)
            # Commiting our changes
            await session.commit()
            # Refreshing database to get freshed data
            await session.refresh(user)
        return user

    # A function to delete a user
    async def delete_user(self , email : str):

        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Now begin the session to insert the asset into the database
            async with session.begin():

                # Prepare the statement and execute it to delete every chunk that's project Id is equal the project Id we take as a parameter
                await session.execute(delete(User).where(User.user_email == email))

            # Commiting our changes
            await session.commit()

    # A function to check if a user exists or not
    async def user_exists(self, email: str) -> bool:
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Prepare a select statement
            result = await session.execute(select(User).where(User.user_email == email))
            
            # Fetch first row
            user = result.scalar_one_or_none()

            return user is not None

    # A function to check the credentials of the user
    async def check_credentials(self, email: str, password: str) -> bool:
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            
            # Prepare a select statement
            result = await session.execute(select(User).where(User.user_email == email, User.user_password == password))
            # Fetch first row
            user = result.scalar_one_or_none()
            
            # Returining a flag whether it exists or not
            return user