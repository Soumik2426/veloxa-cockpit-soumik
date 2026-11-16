from app.database.base import Base
from app.database.session import engine

# Import all models so SQLAlchemy registers them
from app.ingestion import models


def create_tables():
    print("Creating ingestion database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database schema creation completed!")

    print("\nCreated/verified tables:")

    for table_name in sorted(Base.metadata.tables.keys()):
        print(f" - {table_name}")


if __name__ == "__main__":
    create_tables()
