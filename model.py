from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declared_attr
from flask import current_app as app
BAD_REQUEST = 400
MAX_LENGTH = 1000
INTERNAL_SERVER_ERROR = 500
db = SQLAlchemy()


def log_error(message: str, status_code: int) -> tuple[dict, int]:
    app.logger.error(message)
    return dict(status="error", content=dict(message=message)), status_code


class TableAction(db.Model):
    __abstract__ = True

    @classmethod
    def delete_table(cls):
        cls.query.delete()
        result = cls.commit()
        if result is None:
            return True
        commit_result, message = result
        if commit_result is False:
            return log_error(message, INTERNAL_SERVER_ERROR)

    @classmethod
    def register_data(cls, filter_dict: dict, **kwargs) -> bool | tuple[dict, int]:
        """register data to database, if ID exists, update data
        Args:
            filter_dict (dict): filter dict for query
            **kwargs: data to be inserted or updated
        Returns:
            bool | tuple[jsonify, int]:
            bool: successfull insert or update
            tuple[jsonify, int]: insert or update failed, return error message and status code
        """

        db_instance = cls(
            **kwargs,
        )
        app.logger.debug(
            f"Registering to table {cls.__tablename__} with value {kwargs}")
        if (cls.query.filter_by(**filter_dict).first()) is None:
            db.session.add(db_instance)

        elif cls.UPDATABLE is True and filter_dict:
            app.logger.warning(
                f"Updating table {cls.__tablename__} with value {kwargs}")
            cls.query.filter_by(**filter_dict).update(kwargs)
        else:
            return log_error("ID already exists", BAD_REQUEST)

        commit_status = cls.commit()
        if isinstance(commit_status, tuple):
            _, message = commit_status
            return log_error(message, INTERNAL_SERVER_ERROR)

    @classmethod
    def delete_data(cls, **kwargs) -> bool | tuple[dict, int]:
        """delete data from database
        Args:
            **kwargs: filter dict for query
        Returns:
            bool | tuple[jsonify, int]:
            bool: successfull delete
            tuple[jsonify, int]: delete failed, return error message and status code
        """
        result = cls.query.filter_by(**kwargs).delete()
        if result == 0:
            return log_error("ID not found", BAD_REQUEST)

        commit_status = cls.commit()
        if isinstance(commit_status, tuple):
            _, message = commit_status
            return log_error(message, INTERNAL_SERVER_ERROR)

    @staticmethod
    def commit() -> tuple[bool, str]:
        try:
            return db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return False, f"IntegrityError {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, str(e)


class BaseModel(TableAction):
    __abstract__ = True
    UPDATABLE = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self):
        return f"<{self.__tablename__} {self.__dict__}>"


class Status(BaseModel):
    """
    status of task(emulation of celery task)
    """
    UPDATABLE = True
    task_id = db.Column(db.String, primary_key=True)
    current = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    error = db.Column(db.String(MAX_LENGTH))
    status = db.Column(db.String(30), nullable=False)
