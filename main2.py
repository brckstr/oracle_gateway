from fastapi import FastAPI
# from connection_pool import database_instance
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status, HTTPException, Depends, APIRouter

from dataclasses import Field
from pydantic import BaseModel
from typing import Optional, List


class QueryInfoBase(BaseModel):
    id: str
    id_column: str
    tables: List[str]
    statement: str



# Fast API
app = FastAPI()

origins = ["localhost","127.0.0.1"]
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Start up event
# @app.on_event("startup")
# async def startup():
#     await database_instance.connect()

# Main route
@app.get("/")
async def root():
    return {"message": "Oracle Gateway"}


# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def update_records(query_info: QueryInfoBase):
#     connection = pool.acquire()
#     cursor = connection.cursor()
#     query_info = models.QueryInfo(**dict(query_info))
#     for table in query_info.tables:
#         await cursor.execute(f"DELETE FROM {table} where \"paxFlightLegs_id\" = '{query_info.id}'")
#     await cursor.execute(query_info.statement)

#     result = await database_instance.execute(
#         query="INSERT INTO public.user (id, fname,lname, email, password) VALUES ('{}', '{}', '{}', '{}', '{}')".format(db_user.id, db_user.fname,db_user.lname, db_user.email, db_user.password))
#     if result == "INSERT 0 1":
#         return db_user
#     else:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="Something went wrong")