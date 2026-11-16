from sqlalchemy import inspect

from app.database.session import engine
from app.database.base import Base

# Import models so SQLAlchemy registers them
from app.ingestion.models import SourceConnection


def verify_schema():
    inspector = inspect(engine)

    print("\nExisting PostgreSQL tables:")
    for table in inspector.get_table_names():
        print("-", table)

    print("\nSQLAlchemy registered tables:")
    for table in Base.metadata.tables:
        print("-", table)

    if inspector.has_table("source_connection"):
        print("\nsource_connection already exists in PostgreSQL.")

        print("\nExisting columns:")
        for column in inspector.get_columns("source_connection"):
            print(f"- {column['name']}: {column['type']}")
    else:
        print("\nsource_connection does not exist yet.")


if __name__ == "__main__":
    verify_schema()
