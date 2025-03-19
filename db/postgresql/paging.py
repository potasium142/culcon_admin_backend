from typing import Any
from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import Query


class Page(BaseModel):
    page_index: int = 0
    page_size: int = 7


def paging(query: Select[Any], page: Page) -> Select[Any]:
    offset = page.page_index * page.page_size + 1
    return query.limit(
        page.page_size,
    ).offset(
        offset,
    )


def page_param(
    index: int = 0,
    size: int = 7,
):
    return Page(
        page_index=index,
        page_size=size,
    )
