import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from system.model_util import JsonSerializer, ModelGeneralTasks, GeneralQuery
print('url', os.environ["SQLALCHEMY_DATABASE_URI"])

engine = create_engine(os.environ["SQLALCHEMY_DATABASE_URI"])



Session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base(bind=engine, cls=(JsonSerializer, ModelGeneralTasks))
Base.query = Session.query_property(GeneralQuery)
