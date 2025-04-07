import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError
from dtos.request.account import AccountCreateDto
from auth import encryption, jwt_token
from etc.local_error import HandledError

from sqlalchemy.ext.asyncio import AsyncSession
from services.account import create_account  # Adjust import path

from datetime import timedelta


@pytest.fixture
def mock_account():
    """Creates a mock account DTO"""
    mock_dto = MagicMock(spec=AccountCreateDto)
    mock_account = MagicMock()
    mock_account.password = "plain_password"
    mock_dto.get.return_value = mock_account
    return mock_dto, mock_account


@pytest.mark.asyncio
async def test_create_account_success(mock_account):
    mock_dto, mock_account = mock_account

    mock_session = AsyncMock(spec=AsyncSession)
    
    # Ensure async with session.begin(): works properly
    mock_transaction = AsyncMock()
    mock_session.begin.return_value = mock_transaction
    mock_session.__aenter__.return_value = mock_session  # Ensure async with session
    mock_session.__aexit__.return_value = None

    with (
        patch.object(encryption, "hash", return_value="hashed_password") as mock_hash,
        patch.object(jwt_token, "encode", return_value="mock_token") as mock_jwt,
        patch.object(mock_session, "add", new_callable=AsyncMock) as mock_add,
        patch.object(mock_session, "commit", new_callable=AsyncMock) as mock_commit,
    ):
        token = await create_account(mock_dto, mock_session)

        mock_hash.assert_called_once_with("plain_password")
        assert mock_account.password == "hashed_password"
        mock_jwt.assert_called_once_with(mock_account, timedelta(hours=1))
        mock_add.assert_called_once_with(mock_account)
        mock_commit.assert_called_once()
        assert token == "mock_token"


@pytest.mark.asyncio
async def test_create_account_integrity_error(mock_account):
    mock_dto, mock_account = mock_account

    # Create an AsyncMock for the session
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mocking context manager and begin
    mock_session.__aenter__.return_value = mock_session  # Mock __aenter__
    mock_session.__aexit__.return_value = None  # Mock __aexit__
    mock_session.begin.return_value = AsyncMock()  # Mock the session's 'begin'

    # Correct the mocked IntegrityError with the expected error message
    integrity_error = IntegrityError("duplicate key", None, None)
    integrity_error._message = lambda: "duplicate key"  # Mocking the error message method

    with (
        patch.object(encryption, "hash", return_value="hashed_password"),
        patch.object(jwt_token, "encode", return_value="mock_token"),
        patch.object(mock_session, "add", new_callable=AsyncMock),
        patch.object(
            mock_session,
            "commit",
            new_callable=AsyncMock,
            side_effect=integrity_error,  # Raise the mocked IntegrityError
        ),
    ):
        # Ensure create_account raises the HandledError with the correct message
        with pytest.raises(HandledError, match="duplicate key"):
            await create_account(mock_dto, mock_session)