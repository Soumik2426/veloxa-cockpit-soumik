import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Locate and load the .env file
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def get_connection():
    """Create and return a PostgreSQL database connection."""

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


if __name__ == "__main__":
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        current_database(),
                        current_user,
                        version();
                """)

                result = cursor.fetchone()

                print("Database connected successfully!")
                print("Database:", result[0])
                print("User:", result[1])
                print("PostgreSQL:", result[2])

    except Exception as exception:
        print("Database connection failed!")
        print("Error:", exception)
