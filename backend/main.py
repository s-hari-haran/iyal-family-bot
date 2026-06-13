import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routes import tools, webhook, insights, trust

# Initialize FastAPI App
app = FastAPI(
    title="Family Financial Memory OS API",
    description="The execution and persistence layer for Bolna Voice AI Agent",
    version="1.0.0"
)

# Configure CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to specific Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(tools.router)
app.include_router(webhook.router)
app.include_router(insights.router)
app.include_router(trust.router)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
import logging

logger = logging.getLogger("uvicorn")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    decoded_body = body.decode("utf-8")
    logger.error(f"FASTAPI VALIDATION ERROR at {request.url.path}!")
    logger.error(f"Validation Errors: {exc.errors()}")
    logger.error(f"Raw Request Body: {decoded_body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": decoded_body}
    )

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Family Financial Memory OS",
        "description": "Orchestrating structured family money memories via Bolna Voice AI"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
