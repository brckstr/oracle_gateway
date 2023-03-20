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
    id: str
    id_column: str
    tables: List[str]
    statement: str

class Foo(BaseModel):
    id: int
    name: str


async def map_list_foos_result_to_foos(
    result: AsyncIterable[Mapping[str, Any]]
) -> AsyncGenerator[Foo, None]:
    """Map a list foos DB result to a list of foos."""
    async for row in result:
        yield Foo(**row)


async def list_foos_query(
    db: DbPoolConnAndCursor
) -> AsyncGenerator[dict[str, Any], None]:
    """List all foos."""
    cursor = await db.conn.cursor()
    await cursor.execute("SELECT id, name FROM foo")
    cursor_rows_as_dicts(cursor)
    rows = (row async for row in cursor_rows_as_gen(cursor))
    async for row in result_keys_to_lower(rows):
        yield row


@handle_db_errors
async def _get_foos(db: DbPoolConnAndCursor) -> list[Foo]:
    result = list_foos_query(db)
    foos = [x async for x in map_list_foos_result_to_foos(result)]
    return foos


@router.get("/", response_model=list[Foo])
async def read_foos(db: DbPoolConnAndCursor = Depends(get_db_cursor)):
    foos = await _get_foos(db)
    logger.info(f"Fetched {len(foos)} foos")
    return foos

@router.post("/", status_code=status.HTTP_201_CREATED)
async def update_records(query_info: QueryInfoBase, db: DbPoolConnAndCursor = Depends(get_db_cursor)):
    cursor = await db.conn.cursor()
    query_info = models.QueryInfo(**dict(query_info))
    await cursor.execute(f"select \"sourceSystemLastModifiedDateTime_str\" from {query_info.tables[0]} WHERE \"{query_info.id_column}\" = '{query_info.id}'")      
    existing_record = await cursor.fetchone()
    if existing_record:
        for table in query_info.tables:
            await cursor.execute(f"DELETE FROM {table} where \"{query_info.id_column}\" = '{query_info.id}'")
    await cursor.execute(query_info.statement)
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
