from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database.base import engine, Base
from app.module.admin.router import router as admin_router
from app.module.users.router import router as users_router
from app.module.organization.router import router as organization_router
from app.module.role.router import router as role_router
from app.module.department.router import router as department_router
from app.module.document_type.router import router as document_type_router
from app.module.file_manage.router import router as file_manage_router
from app.module.auth.router import router as auth_router
from app.settings.config import settings
from app.utils.response import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE documents ADD COLUMN designation VARCHAR(255)"))
        except Exception:
            pass
    yield


app = FastAPI(title="E-Abhilekh API", version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(organization_router, prefix="/api/v1")
app.include_router(role_router, prefix="/api/v1")
app.include_router(department_router, prefix="/api/v1")
app.include_router(document_type_router, prefix="/api/v1")
app.include_router(file_manage_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(result=None, message=exc.detail, status_code=exc.status_code).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(result=None, message="Internal server error", status_code=500).model_dump(),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
