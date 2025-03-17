import os 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.item_routes import item_router
from services.db import DatabaseService
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://pgvector:pgvector@localhost:5433/pgvector_db")

app = FastAPI()
db_service = DatabaseService(db_url=DB_CONNECTION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(item_router, prefix="/api/v1/items", tags=["items"])    