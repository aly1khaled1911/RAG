from fastapi import FastAPI , APIRouter,Depends
import os
from helpers.config import get_settings , Settings


# Setting the router for all api/v1 endpoints
base_router=APIRouter(
    prefix="/api/v1",
    tags=["api_v1"]
)

# Making an endpoint get request for this router
@base_router.get("/")


# Making the function endpoint which returns the welcome message , the name of the app and the version
# Getting these from Settings which is ingected by get settings
async def welcome(app_settings : Settings =Depends(get_settings)):

    app_name=app_settings.APP_NAME
    app_version=app_settings.APP_VERSION
    return {"app_name" : app_name ,
            "app_version": app_version}