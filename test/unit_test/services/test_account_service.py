import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError
from dtos.request.account import AccountCreateDto
from auth import encryption, jwt_token
from etc.local_error import HandledError
from db.postgresql.db_session import db_session
from services.account_service import create_account  # Adjust import path

from datetime import timedelta


@pytest.fixture
def mock_account():
    """Creates a mock account DTO"""
    mock_dto = MagicMock(spec=AccountCreateDto)
    mock_account = MagicMock()
    mock_account.password = "plain_password"
    mock_dto.get.return_value = mock_account
    return mock_dto, mock_account


def test_create_account_success(mock_account):
    mock_dto, mock_account = mock_account

    with (
        patch.object(encryption, "hash", return_value="hashed_password") as mock_hash,
        patch.object(jwt_token, "encode", return_value="mock_token") as mock_jwt,
        patch.object(db_session.session, "add") as mock_add,
        patch.object(db_session, "commit") as mock_commit,
    ):
        token = create_account(mock_dto)

        mock_hash.assert_called_once_with("plain_password")
        assert mock_account.password == "hashed_password"
        mock_jwt.assert_called_once_with(mock_account, timedelta(hours=1))
        mock_add.assert_called_once_with(mock_account)
        mock_commit.assert_called_once()
        assert token == "mock_token"


def test_create_account_integrity_error(mock_account):
    mock_dto, mock_account = mock_account

    with (
        patch.object(encryption, "hash", return_value="hashed_password"),
        patch.object(jwt_token, "encode", return_value="mock_token"),
        patch.object(db_session.session, "add"),
        patch.object(
            db_session,
            "commit",
            side_effect=IntegrityError("duplicate key", None, None),
        ),
    ):
        with pytest.raises(HandledError):
            create_account(mock_dto)
