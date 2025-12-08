from fastapi import Request , HTTPException  
from fastapi.security import HTTPBearer , HTTPAuthorizationCredentials
from .AuthController import AuthController

class BearerController(HTTPBearer):

    def __init__(self , auto_error : bool = True):
        super(BearerController,self).__init__(auto_error=auto_error)
    
    async def __call__(self , request : Request):
        
        credentials : HTTPAuthorizationCredentials = await super(BearerController,self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code = 403 , detail = "invalid Authentication Scheme")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code = 403 , detail = "invalid or expired token")
            return credentials.credentials
        else:
            raise HTTPException(status_code = 403 , detail = "invalid or expired token")

    def verify_jwt(self,jwt_token : str):
        
        auth_controller = AuthController()
        IsTokenValid : bool = False

        payload = auth_controller.decodeJWT(jwt_token)
                
        if payload:
            IsTokenValid = True
        
        return IsTokenValid

