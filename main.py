from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from options import Options
from routes.categories import router as categories_router
from routes.expenses import router as expenses_router

# Initialize FastAPI app
app = FastAPI(
    title="Expense Tracker API",
    description="API for tracking expenses and categories with DynamoDB and caching support.",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(categories_router)
app.include_router(expenses_router)


@app.get("/")
async def root():
    """
    Root endpoint returning details about the API.
    """
    return {
        "status": "online",
        "service": "Expense Tracker API",
        "endpoints": {
            "GET /": "API info",
            "GET /expenses": "Get all expenses",
            "POST /expenses": "Add a new expense",
            "GET /categories": "Get all categories (cached)",
            "POST /categories": "Add a new category"
        },
        "target_ddb_table": Options.EXPENSES_TABLE_NAME
    }


if __name__ == "__main__":
    import uvicorn
    # Execute the app on host 0.0.0.0 and port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
