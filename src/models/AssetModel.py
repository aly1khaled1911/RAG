# Creating an asset model to manipulate assets in the database

# Importing the base data model to inherit from
from .BaseDataModel import BaseDataModel

# Import the schema of the asset to validate data
from .db_schemas import Asset

# Get the select statment to select from the database
from sqlalchemy.future import select

# Creating the AssetModel Class for interactions with the database
class AssetModel(BaseDataModel):

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
    async def create_asset(self, asset : Asset):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            # Now begin the session to insert the asset into the database
            async with session.begin():
                session.add(asset)
            # Commiting our changes
            await session.commit()
            # Refreshing database to get freshed data
            await session.refresh(asset)
        return asset

    # A function to get all project assets from the database
    async def get_all_project_assets(self , asset_project_id : str):
        
        # Making the db_client as our session to integrate with
        async with self.db_client() as session:

            # Preparing Statement to execute in the database
            stmt = select(Asset).where(Asset.asset_project_id == asset_project_id)
            # Execute the statement to get results
            result = await session.execute(stmt)

            # Saving the results in the records then return it
            records = result.scalars().all()
        return records

    # A function to the get any asset
    async def get_asset_record(self, asset_project_id: str, asset_name: str):

        # Making the db_client as our session to integrate with
        async with self.db_client() as session:
            # Preparing Statement to execute in the database
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_name == asset_name
            )
            # Execute the statement to get result
            result = await session.execute(stmt)

            # Saving the results in the record then return it
            record = result.scalar_one_or_none()
        return record