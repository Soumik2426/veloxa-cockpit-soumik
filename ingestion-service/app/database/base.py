from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.

    Every database entity will inherit from this class.
    """
    pass
