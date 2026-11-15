from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def test_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        )

        print(f"Connected to: {result.scalar()}")

if __name__ == "__main__":
    test_connection()
