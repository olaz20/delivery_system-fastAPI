from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File,Request
from pathlib import Path
import uuid
from app.core.config import settings
import shutil


async def validate_image_file(goods_image: UploadFile=File(None)):
    if goods_image:
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        file_extension = Path(goods_image.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format. Use JPG, JPEG, or PNG")
        if goods_image.size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image size exceeds 5MB")
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(exist_ok=True)
        file_extension = Path(goods_image.filename).suffix
        goods_image_path = upload_dir / f"goods_{uuid.uuid4()}{file_extension}"
        with goods_image_path.open("wb") as buffer:
            shutil.copyfileobj(goods_image.file, buffer)

