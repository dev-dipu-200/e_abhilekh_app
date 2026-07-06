from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_db
from app.database.user_model import User
from app.dependencies import get_current_org_admin
from app.module.settings.schema import AISettingsResponse, AISettingsUpdate
from app.module.settings import service as settings_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/ai")
async def get_ai_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_org_admin),
):
    settings = await settings_service.get_ai_settings(db, current_user)
    return SuccessResponse(
        result=AISettingsResponse(**settings),
        message="AI settings retrieved successfully",
        status_code=200,
    )


@router.put("/ai")
async def update_ai_settings(
    data: AISettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_org_admin),
):
    settings = await settings_service.update_ai_settings(db, current_user, data)
    return SuccessResponse(
        result=AISettingsResponse(**settings),
        message="AI settings updated successfully",
        status_code=200,
    )
