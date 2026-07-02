from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.module.auth.schema import LoginRequest
from app.module.auth import service as auth_service
from app.dependencies import get_current_user
from app.database.user_model import User
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, data.email, data.password)
    token = auth_service.create_access_token({"sub": user.id, "email": user.email})
    return SuccessResponse(
        result={
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_superuser": user.is_superuser,
            "organization_id": user.organization_id,
        },
        message="Login successful",
        status_code=200,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return SuccessResponse(result=None, message="Logged out successfully", status_code=200)
