# test_account.py
import pytest
from sqlalchemy import select

from services.account import create_account
from db.postgresql.models.staff_account import StaffAccount, AccountType
from etc.local_error import HandledError

from .set_up.test_account_data import *
from test.unit_test.services.set_up.conftest import db_session


# @pytest.mark.asyncio
# async def test_create_account_success_with_db(db_session):
#     account_dto = get_sample_account_dto()

#     token = await create_account(account_dto, db_session)

#     account = await db_session.execute(
#         select(StaffAccount).filter(StaffAccount.token == token)
#     )
#     account = account.scalar_one_or_none()

#     assert account is not None
#     # assert account.username == "testuser01"
#     assert account.type == AccountType.STAFF

# @pytest.mark.asyncio
# async def test_create_account_already_exists(db_session):
#     account_dto = get_sample_account_dto()

#     await create_account(account_dto, db_session)

#     with pytest.raises(HandledError, match="duplicate key value"):
#         await create_account(account_dto, db_session)

