from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_organizations: int
    total_users: int
    total_documents: int
    total_departments: int


class AdminRegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None


class AdminRegisterResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str | None = None
    is_superuser: bool
    message: str = "Admin registered successfully"


class ClearAllResponse(BaseModel):
    message: str = "All records cleared successfully"
