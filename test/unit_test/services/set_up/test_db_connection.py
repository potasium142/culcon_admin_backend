from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
from sqlalchemy.future import select

# Database URL
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

# Create an async engine for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)


# Test connection
async def test_connection():
    try:
        async with engine.connect() as conn:
            # Correctly use select(1) for SQLAlchemy async
            result = await conn.execute(select(1))
            # Fetch the result from the query
            scalar_result = result.scalar()
            print(f"Connection successful: {scalar_result}")
    except Exception as e:
        print(f"Error connecting to the database: {e}")


# Run the test function
asyncio.run(test_connection())
