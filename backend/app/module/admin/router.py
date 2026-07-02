from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.module.admin.schema import AdminRegisterRequest
from app.module.admin import service as admin_service
from app.dependencies import get_current_superuser
from app.database.user_model import User
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    stats = await admin_service.get_dashboard_stats(db)
    return SuccessResponse(result=stats, message="Dashboard stats retrieved", status_code=200)


@router.post("/register")
async def register_admin(data: AdminRegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await admin_service.register_admin(
        db, email=data.email, username=data.username, password=data.password, full_name=data.full_name
    )
    return SuccessResponse(
        result={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_superuser": user.is_superuser,
        },
        message="Admin registered successfully",
        status_code=201,
    )


@router.delete("/clear-all")
async def clear_all(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_superuser)):
    await admin_service.clear_all_records(db)
    return SuccessResponse(result=None, message="All records cleared successfully", status_code=200)
