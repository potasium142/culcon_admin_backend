from db.postgresql.models.user_account import *

def preb_user_account_1():
    return UserAccount(
        id="User_001",  # Generate a valid UUID for the 'id' field
        email="user001@example.com",
        username="TestUser001",
        profile_name="Test User 001",  # You can set a profile name if needed
        password="hashedpassword",  # Use your hashed password, make sure it's valid
        status=UserAccountStatus.NORMAL,  # Valid UserAccountStatus
        address="123 Test Street, Test City, TC 12345",  # Address, optional field
        phone="123-456-9990",  # Valid phone number, make sure it's unique in tests
        profile_pic_uri="defaultProfile",  # or you can use a valid URI if necessary
        profile_description="This is a test user profile description",  # Optional field
        token="unique_token_001",  # Use a unique token for each test case
        online_status="OFFLINE",  # Set the default or desired online status
    )