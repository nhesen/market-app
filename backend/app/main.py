from fastapi import FastAPI,Request
import logging,time
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.customer_routes import router as customer_router
from app.api.audit_routes import router as audit_router
from app.api.platform_routes import router as platform_router
from app.api.content_routes import router as content_router
from app.api.vision_routes import router as vision_router
from app.core.config import settings
from app.db.session import Base, engine
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="0.1.0")
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger("martiq.request")
@app.middleware("http")
async def request_log(request:Request,call_next):
    started=time.perf_counter()
    try:
        response=await call_next(request);logger.info("method=%s path=%s status=%s duration_ms=%.1f",request.method,request.url.path,response.status_code,(time.perf_counter()-started)*1000);return response
    except Exception:
        logger.exception("method=%s path=%s status=500",request.method,request.url.path);raise
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.include_router(customer_router)
app.include_router(audit_router)
app.include_router(platform_router)
app.include_router(content_router)
app.include_router(vision_router)
app.mount("/uploads",StaticFiles(directory=settings.upload_dir),name="uploads")
app.mount("/assets",StaticFiles(directory="assets"),name="assets")

@app.get("/health")
def health(): return {"status": "ok", "service": "martiq-api"}
