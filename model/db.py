from sqlalchemy import MetaData
from flask_sqlalchemy import Model, SQLAlchemy

from system.model_util import JsonSerializer, ModelGeneralTasks, GeneralQuery


class PowerPaintModel(Model, JsonSerializer, ModelGeneralTasks):
    pass


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata, model_class=PowerPaintModel,
                query_class=GeneralQuery)
