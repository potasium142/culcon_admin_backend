import sqlalchemy as sqla
import sqlalchemy_utils as sqlau

from config import env

import db.postgresql.models
from db.postgresql.models import *

URL_DATABASE = env.DB_URL

engine = sqla.create_engine(URL_DATABASE)
if not sqlau.database_exists(engine.url):
    sqlau.create_database(engine.url)

models.Base.metadata.create_all(engine)

DBSession: sqla.orm.Session = sqla.orm.sessionmaker(engine)
