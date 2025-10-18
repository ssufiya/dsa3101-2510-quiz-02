"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.questions import routes as questions_routes

app = FastAPI(
    title="Quiz Bank API",
    description="API for managing quiz questions and versions",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include questions router
app.include_router(
    questions_routes.router, 
    prefix="/api/questions", 
    tags=["Questions"]
)

@app.get("/")
async def root():
    """Health check"""
    return {"message": "Quiz Bank API is running!", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)