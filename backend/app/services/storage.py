import re,secrets
from pathlib import Path
from fastapi import HTTPException,UploadFile
from app.core.config import settings

ALLOWED={"image/jpeg":"jpg","image/png":"png","image/webp":"webp","video/mp4":"mp4"}
class LocalStorage:
    def __init__(self): self.root=Path(settings.upload_dir);self.root.mkdir(parents=True,exist_ok=True)
    async def save(self,file:UploadFile)->tuple[str,int,str]:
        mime=file.content_type or ""
        if mime not in ALLOWED: raise HTTPException(415,"Unsupported file type")
        data=await file.read(settings.max_upload_size+1)
        if len(data)>settings.max_upload_size: raise HTTPException(413,"File is too large")
        safe=re.sub(r"[^A-Za-z0-9._-]","_",Path(file.filename or "upload").name)[:80]
        key=f"{secrets.token_hex(16)}-{safe}.{ALLOWED[mime]}"; (self.root/key).write_bytes(data)
        return key,len(data),mime
storage=LocalStorage()

