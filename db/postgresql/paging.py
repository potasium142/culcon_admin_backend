from math import ceil
from pydantic import BaseModel
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.db_session import db_session


class Page(BaseModel):
    page_index: int = 0
    page_size: int = 7


def paging(query, page: Page):
    offset = page.page_index * page.page_size
    return query.limit(
        page.page_size,
    ).offset(
        offset,
    )


async def table_size(col, ss: AsyncSession):
    return await ss.scalar(sqla.select(sqla.func.count(col))) or 0


def page_param(
    index: int = 0,
    size: int = 7,
):
    return Page(
        page_index=index,
        page_size=size,
    )


def display_page(content, size: int, pg: Page):
    return {
        "content": content,
        "total_element": size,
        "total_page": ceil(size / pg.page_size),
        "page_index": pg.page_index,
    }
