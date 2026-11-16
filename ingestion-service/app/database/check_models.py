from app.database.base import Base

# Import all models to register them with SQLAlchemy
from app.ingestion import models


def check_models():
    print("\nRegistered SQLAlchemy models:")

    for table_name in sorted(Base.metadata.tables.keys()):
        print(f" - {table_name}")

    print(f"\nTotal registered tables: {len(Base.metadata.tables)}")


if __name__ == "__main__":
    check_models()
