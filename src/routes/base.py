from fastapi import FastAPI , APIRouter,Depends , Body
import os
from helpers.config import get_settings , Settings
from .schemas.base import PostScheme , UserLoginScheme , UserSchema
from controllers import AuthController , BearerController




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


posts = [
    {
        "id":1,
        "title":"penguins",
        "text":"here are penguins"
    },
    {
        "id":2,
        "title":"tigers",
        "text":"here are tigers"
    },
    {
        "id":3,
        "title":"koalas",
        "text":"here are koalas"
    }
]
users = []

def check_user(data : UserLoginScheme):
    
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
        
    return False

@base_router.get("/posts")
def get_posts():
    return {"data":posts}

@base_router.get("/posts/{id}")
def get_single_post(id:int):
    
    if id > len(posts):
        return "Wrong Id number"
    else:
        for post in posts:
            if post["id"]==id:
                return {"data":post}
            
@base_router.post("/posts",dependencies = [Depends(BearerController())])
def add_post(post : PostScheme):
    
    post.id = len(posts) + 1
    posts.append(post.dict())
    return {
        "info": "post added"
    }

@base_router.post("/user/signup")
def user_signup(user : UserSchema = Body(default=None)):
    
    auth_controller = AuthController()
    users.append(user)
    return auth_controller.signJWT(user.email)

@base_router.post("/user/login")
def user_signup(user : UserLoginScheme = Body(default=None)):

    auth_controller = AuthController()    
    if check_user(user):
        return auth_controller.signJWT(user.email)
    else :
        return {"Info":"Invalid Login Details"}