from fastapi import FastAPI , APIRouter,Depends , Body , Request
import os
from helpers.config import get_settings , Settings
from .schemas.base import PostScheme , UserLoginScheme
from controllers import AuthController
from models.UserModel import UserModel
from controllers.RoleController import require_roles
from models.enums.RolesEnum import Roles


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

@base_router.post("/sign_up/{email}/{password}")
async def sign_up(request : Request,email : str , password : str , role : Roles):
    
    user_model = UserModel(request.app.db_client)
    
    if await user_model.user_exists(email=email):
        return {"info":"User already exists , try to login"}
    
    await user_model.create_user(email = email , password = password ,role=role )
    return {"info":"User Created"}


@base_router.validate_user("/validate_user")
def validate_user(post : PostScheme , payload = Depends(require_roles(Roles.ROOT))):
    return "You're Authenticated"

@base_router.post("/user/login")
async def user_login(request : Request ,user : UserLoginScheme = Body(default=None)):

    user_model = UserModel(db_client=request.app.db_client)

    user = await user_model.check_credentials(email = user.email , password=user.password)
    if user:
        auth_controller = AuthController()
        return auth_controller.signJWT(user.user_email , user.user_role)
    else :
        return {"Info":"Invalid Login Details"}