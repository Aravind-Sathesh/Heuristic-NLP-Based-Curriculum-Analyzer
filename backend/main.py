from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import curriculum_routes, qpaper_routes, combined_routes
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Curriculum Analyzer API")

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(curriculum_routes.router,
                   prefix="/curriculum", tags=["Curriculum Analysis"])
app.include_router(qpaper_routes.router, prefix="/qpaper",
                   tags=["Question Paper Analysis"])
app.include_router(combined_routes.router,
                   prefix="/api", tags=["Combined Analysis"])


@app.get("/")
def read_root():
    return {"status": "Curriculum Analyzer API is running!"}
