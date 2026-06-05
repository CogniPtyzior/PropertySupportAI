"""
PropertySupport AI - app/db/base.py

SQLAlchemy declarative base used by all ORM models and Alembic migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
