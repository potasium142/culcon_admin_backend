import sqlalchemy as sqla
import sqlalchemy_utils as sqlau

import db.models
from db.models import *

URL_DATABASE = "postgresql://culcon:culcon@localhost:5432/culcon"

engine = sqla.create_engine(URL_DATABASE)
if not sqlau.database_exists(engine.url):
    sqlau.create_database(engine.url)

db.models.Base.metadata.create_all(engine)

DBSession: sqla.orm.Session = sqla.orm.sessionmaker(engine)
