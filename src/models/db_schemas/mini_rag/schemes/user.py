from .mini_rag_base import SQLAlchemyBase
from sqlalchemy import Column , Integer , DateTime , func , String
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(SQLAlchemyBase):
    __tablename__ = "users"

    user_id = Column(Integer , primary_key = True , autoincrement = True)
    user_uuid = Column(UUID(as_uuid = True),default = uuid.uuid4,unique = True , nullable = False)

    user_email = Column(String(50) , nullable = False)
    user_password = Column(String(16) , nullable = False)
    
    created_at = Column(DateTime(timezone = True), server_default = func.now(),nullable = False)