import sqlalchemy.orm

from db.postgresql import DBSession


class Session:
    session: sqlalchemy.orm.Session = DBSession()

    def commit(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e


db_session = Session()
