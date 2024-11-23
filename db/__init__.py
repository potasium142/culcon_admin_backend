import sqlalchemy_utils as sqlau
import sqlalchemy as sqla
import db.models
from db.models import account

URL_DATABASE = "postgresql://culcon:culcon@localhost:5432/culcon_admin"

engine = sqla.create_engine(URL_DATABASE)
if not sqlau.database_exists(engine.url):
    sqlau.create_database(engine.url)

db.models.Base.metadata.create_all(engine)

DBSession: sqla.orm.Session = sqla.orm.sessionmaker(engine)
