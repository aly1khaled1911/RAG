# Importing Base Controller to inherit from
from .BaseController import BaseController


import time
import jwt

class AuthController(BaseController):

    # this function is to set the secret and the algorithm we will use
    def __init__(self):
        super().__init__()
        self.JWT_Secret = self.app_settings.SECRET
        self.JWT_Algorithm = self.app_settings.ALGORITHM
    
    def signJWT(self,UserID : str):
        payload = {
            "UserID" : UserID,
            "expiry": time.time() + self.app_settings.EXPIRING_TIME
        }
        token =  jwt.encode(payload,self.JWT_Secret , self.JWT_Algorithm)
        return {"access token": token}
    
    def decodeJWT(self , token : str):

        try:
            decoded_token = jwt.decode(token , self.JWT_Secret , algorithms=[self.JWT_Algorithm])
            return decoded_token if decoded_token["expiry"] >=time.time() else None
        except :
            return {}
        