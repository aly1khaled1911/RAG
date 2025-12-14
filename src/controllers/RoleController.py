from fastapi import Depends, HTTPException
from .BearerController import BearerController
from models.enums.RolesEnum import Roles

def require_roles(*allowed_roles : Roles): # the aestrick is to take multiple roles

    def role_checker(payload=Depends(BearerController())):
        
        user_role = payload["Role"]

        if user_role not in [role.value for role in allowed_roles]:
            
            raise HTTPException(status_code = 403 , detail = "You don't have these permissions")

        return payload

    return role_checker