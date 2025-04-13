import pytest
from unittest.mock import patch, MagicMock
from db.postgresql.models.user_account import UserAccount, UserAccountStatus, PostComment
from etc.local_error import HandledError
from db.postgresql.db_session import db_session
from services.customer import set_account_status, delete_comment

def test_set_account_status_success():
    mock_account = MagicMock(spec=UserAccount)
    mock_account.status = UserAccountStatus.NORMAL
    
    with patch.object(db_session.session, "get", return_value=mock_account) as mock_get, \
         patch.object(db_session, "commit") as mock_commit:

        set_account_status("some_user_id", UserAccountStatus.DEACTIVATE)
        
        mock_get.assert_called_once_with(UserAccount, "some_user_id")
        assert mock_account.status == UserAccountStatus.DEACTIVATE
        mock_commit.assert_called_once()

def test_set_account_status_not_found():
    with patch.object(db_session.session, "get", return_value=None):
        with pytest.raises(HandledError, match="Customer account not found"):
            set_account_status("invalid_user_id", UserAccountStatus.DEACTIVATE)



# @pytest.fixture
# def mock_comment():
#     """Fixture to create a mock comment object"""
#     mock_comment = MagicMock(spec=PostComment)
#     mock_comment.deleted = False  # Simulate an existing, active comment
#     return mock_comment


# def test_delete_comment_success(mock_comment):
#     """Test deleting a comment successfully marks it as deleted"""
#     with patch.object(db_session.session, "get", return_value=mock_comment) as mock_get, \
#          patch.object(db_session, "commit") as mock_commit:

#         delete_comment("user_123", "comment_456")

#         mock_get.assert_called_once_with(PostComment, {"account_id": "user_123", "id": "comment_456"})
#         assert mock_comment.deleted is True
#         mock_commit.assert_called_once()


# def test_delete_comment_not_found():
#     """Test raising an error when comment does not exist"""
#     with patch.object(db_session.session, "get", return_value=None):
#         with pytest.raises(HandledError, match="Comment not found"):
#             delete_comment("user_123", "comment_456")
