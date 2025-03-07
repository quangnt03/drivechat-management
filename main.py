import os 
from fastapi import FastAPI
from routes.item_routes import item_router
from services.db import DatabaseService
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://pgvector:pgvector@localhost:5433/pgvector_db")

app = FastAPI()
db_service = DatabaseService(db_url=DB_CONNECTION)


app.include_router(item_router, prefix="/items", tags=["items"])    