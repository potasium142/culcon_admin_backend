from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.postgresql import DBSession, engine


class Session:
    session: AsyncSession = DBSession()

    async def commit(self):
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e


async def get_session():
    session = async_sessionmaker(engine)
    try:
        yield session()
    finally:
        await session().close()


db_session = Session()
