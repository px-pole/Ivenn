from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.attachments import router as attachments_router
from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.api.routes.maintenance import router as maintenance_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.reports import router as reports_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.warranties import router as warranties_router
from app.core.config import settings
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://tauri.localhost",
        "tauri://localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(categories_router)
app.include_router(items_router)
app.include_router(attachments_router)
app.include_router(warranties_router)
app.include_router(reports_router)
app.include_router(maintenance_router)
app.include_router(notifications_router)

for router in (
    health_router,
    auth_router,
    rooms_router,
    categories_router,
    items_router,
    attachments_router,
    warranties_router,
    reports_router,
    maintenance_router,
    notifications_router,
):
    app.include_router(router, prefix="/api/v1")
