from collections.abc import AsyncIterable, Mapping
from typing import Any, AsyncGenerator, List

from fastapi import APIRouter, Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi_oracle import (
    DbPoolConnAndCursor,
    IntermittentDatabaseError,
    close_db_pools,
    cursor_rows_as_dicts,
    cursor_rows_as_gen,
    get_db_cursor,
    handle_db_errors,
    result_keys_to_lower,
)
from pydantic import BaseModel


router = APIRouter()


class QueryInfoBase(BaseModel):
    collection: str
    id: str
    id_column: str
    timestamp: str
    timestamp_column: str
    tables: List[str]
    statement: str


@router.get("/")
async def read_foos():
    return {"Service": "Oracle Gateway"}

@router.post("/", status_code=status.HTTP_201_CREATED)
async def update_records(query_info: QueryInfoBase, db: DbPoolConnAndCursor = Depends(get_db_cursor)):
    cursor = await db.conn.cursor()
    query_info = QueryInfoBase(**dict(query_info))
    await cursor.execute(f"select {query_info.timestamp_column} from {query_info.tables[0]} WHERE {query_info.id_column} = '{query_info.id}'")      
    existing_record = await cursor.fetchone()
    if existing_record:
        if existing_record[query_info.timestamp_column] <= query_info.timestamp:
            for table in query_info.tables:
                await cursor.execute(f"DELETE FROM {table} where {query_info.id_column} = '{query_info.id}'")
        else:
            return {}
    await cursor.execute(query_info.statement)
    await db.conn.commit()
    return {}

async def intermittent_database_error_handler(
    request: Request,
    exc: IntermittentDatabaseError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": [
                {
                    "msg": f"{exc}",
                    "type": "intermittent_database_error",
                }
            ],
        },
    )


app = FastAPI(
    on_shutdown=[close_db_pools],
    exception_handlers={
        IntermittentDatabaseError: intermittent_database_error_handler,
    },
)
app.include_router(router)
