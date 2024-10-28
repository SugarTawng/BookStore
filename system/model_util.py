import os
import datetime
import uuid
import enum

from sqlalchemy import inspect, func
from sqlalchemy.orm import Query
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

from system.exceptions import NotFound

class JsonSerializer:
    __json_public__ = None
    __json_hidden__ = None
    __json_modifiers__ = None

    def get_field_names(self):
        for p in self.__mapper__.iterate_properties:
            yield p.key
        for p in sa_inspect(self.__class__).all_orm_descriptors:
            if type(p) == hybrid_property:
                yield p.__name__

    def to_json(self):
        field_names = self.get_field_names()

        public = self.__json_public__ or field_names
        hidden = self.__json_hidden__ or []
        modifiers = self.__json_modifiers__ or dict()

        rv = dict()
        for key in public:
            rv[key] = getattr(self, key)
        for key, modifier in modifiers.items():
            value = getattr(self, key)
            rv[key] = modifier(value, self)
        for key in hidden:
            rv.pop(key, None)

        for item in rv:
            if hasattr(rv[item], "to_json"):
                rv[item] = rv[item].to_json()
            elif isinstance(rv[item], datetime.datetime):
                rv[item] = rv[item].isoformat()
            elif isinstance(rv[item], uuid.UUID):
                rv[item] = str(rv[item])
            elif isinstance(rv[item], (int, float, bool, dict, list)):
                rv[item] = rv[item]
            elif isinstance(rv[item], enum.Enum) and hasattr(rv[item], "name"):
                rv[item] = rv[item].name
            elif rv[item] is None:
                continue
            else:
                rv[item] = str(rv[item])
        return rv


class ModelGeneralTasks:
    def add(self, session=None):
        """
        add only
        """
        if not session:
            session = inspect(self).session
        try:
            session.add(self)
        except (SQLAlchemyError, DBAPIError) as e:
            session.rollback()
            raise e
        session.close()
        return self

    def save(self, session=None):
        """
        commit
        """
        if not session:
            session = inspect(self).session
        try:
            session.commit()
        except (SQLAlchemyError, DBAPIError) as e:
            session.rollback()
            raise e
        session.close()
        return self

    def delete(self, session=None):
        if not session:
            session = inspect(self).session
        try:
            session.delete(self)
        except (SQLAlchemyError, DBAPIError) as e:
            session.rollback()
            raise e
        session.close()

    def dynamic_update(self, data):
        in_db_fields = list(map(lambda table_dot_column: str(table_dot_column).split('.').pop(), self.__table__.columns))

        for key, value in data.items():
            if hasattr(self, key) and key in in_db_fields:
                setattr(self, key, value)


class GeneralQuery(Query):
    def find_by_id(self, id):
        return self.get(id)

    def get_or_404(self, id, custom_message=None):
        rv = self.get(id)
        if rv is None:
            try:
                clsname = self._entities[0].mapper.class_.__name__ # 1st class only
            except IndexError:
                clsname = "Object"
            raise NotFound(f"{clsname}: id with value {str(id)} does not exist.")
        return rv

    def find_by_filter(self, model, filter, get_all=False):
        query = self
        for k, v in filter.items():
            query = query.filter(model.__table__.columns[k] == v)

        if get_all is False:
            return query.first()

        return query.all()

    def find_all(self, offset=0, limit=None, order=None):
        offset, limit = self.normalize_offset_limit(offset, limit)
        return self.order_by(order).offset(offset).limit(limit).all()

    def find_all_with_attributes(self, model, attributes):
        this = self
        offset = attributes.pop("offset", 0)
        limit = attributes.pop("limit", 10)
        offset, limit = self.normalize_offset_limit(offset, limit)
        order_by = attributes.pop("order_by", "created_at")
        for k, v in attributes.items():
            if isinstance(v, list):
                this = this.filter(model.__table__.columns[k].in_(v))
            else:
                this = this.filter(model.__table__.columns[k] == v)
        items = this.order_by(order_by).offset(offset).limit(limit).all()
        count = this.count()
        return dict(items=items, count=count, offset=offset, limit=limit)

    def find_all_by_filter_and_count(self, filter, offset=0, limit=10, order=None):
        offset, limit = self.normalize_offset_limit(offset, limit)
        return self.filter(filter).order_by(order).offset(offset).limit(limit).all()

    @staticmethod
    def find_all_and_count_with_cmd_query_and_model(
        model, cmd_query, attributes):
        field_can_filter = model.__filter_field__ or list()
        for k, v in attributes.items():
            if k in field_can_filter:
                if isinstance(v, list):
                    cmd_query = cmd_query.filter(
                        model.__table__.columns[k].in_(v))
                else:
                    cmd_query = cmd_query.filter(
                        model.__table__.columns[k] == v)
        return cmd_query

    def filter_or_404(self, model, filter):
        rv = self.find_by_filter(model, filter)
        if len(rv) == 0:
            raise NotFound("Object does not exist.")
        return rv[0]

    def max(self, model, column, filters):
        query = self.session.query(func.max(column))
        for k, v in filters.items():
            query = query.filter(model.__table__.columns[k] == v)
        return query.first()[0]

    def min(self, model, column, filters):
        query = self.session.query(func.min(column))
        for k, v in filters.items():
            query = query.filter(model.__table__.columns[k] == v)
        return query.first()[0]

    def sum(self, model, column, filters):
        query = self.session.query(func.sum(column))
        for k, v in filters.items():
            query = query.filter(model.__table__.columns[k] == v)
        return query.first()[0]

    def add_range_condition(self, column, range_from=None, range_to=None):
        query = self
        if range_from is not None:
            query = query.filter(column >= range_from)
        if range_to is not None:
            query = query.filter(column <= range_to)
        return query

    @staticmethod
    def normalize_offset_limit(offset, limit):
        if offset < 0:
            offset = 0
        if isinstance(limit, int) and limit < 0:
            limit = 10
        return offset, limit
