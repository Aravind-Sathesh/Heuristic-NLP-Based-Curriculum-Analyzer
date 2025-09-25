from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import curriculum_routes, qpaper_routes

app = FastAPI(title="Curriculum Analyzer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers from the api module
app.include_router(curriculum_routes.router,
                   prefix="/curriculum", tags=["Curriculum Analysis"])
app.include_router(qpaper_routes.router, prefix="/qpaper",
                   tags=["Question Paper Analysis"])


@app.get("/")
def read_root():
    return {"status": "Curriculum Analyzer API is running!"}
