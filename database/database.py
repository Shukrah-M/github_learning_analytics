import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


# 1. Load variables from the .env file
load_dotenv()


# 2. Read database configuration from .env
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# 3. Create the PostgreSQL connection URL
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


# 4. Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)


# 5. Create a database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# 6. Function to test the database connection
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))

            print("Connected to PostgreSQL successfully!")
            print(result.fetchone()[0])

    except Exception as error:
        print("Database connection failed.")
        print(error)


# 7. Run the test only when this file is executed directly
if __name__ == "__main__":
    test_connection()