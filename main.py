import os
import uvicorn
import logging
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.routers.semantic_search import semantic_router
from app.api.routers.index_paper import index_paper_router
from app.api.routers.ask_arxiv import askarxiv_router
from app.api.routers.podcast import podcast_router
from app.api.routers.chat import chat_router

app = FastAPI(docs_url=None)

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv('FASTAPI_USERNAME'))
    correct_password = secrets.compare_digest(credentials.password, os.getenv('FASTAPI_PASSWORD'))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(get_current_username)):
    return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")

environment = os.getenv("ENVIRONMENT", "dev") # Default to 'development' if not set

if environment == "dev":
    logger = logging.getLogger("uvicorn")
    logger.warning("Running in development mode - allowing CORS for all origins")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[ "X-Experimental-Stream-Data"],
    )
else:
    logger = logging.getLogger("uvicorn")
    logger.warning("Running in production mode")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://paperbrain.org", "https://paperbrainv2.vercel.app"],  
        allow_credentials=True,
        allow_methods=["*"],
        expose_headers=[ "X-Experimental-Stream-Data"],
    )

app.include_router(semantic_router,) 
app.include_router(index_paper_router,) 
app.include_router(podcast_router,) 
app.include_router(askarxiv_router,) 
app.include_router(chat_router,) 


if __name__ == "__main__":
    app_host = os.getenv("APP_HOST", "127.0.0.1")
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = True if environment == "dev" else False

    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload)