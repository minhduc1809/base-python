import io
import uuid
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from PIL import Image
from miniopy_async import Minio
from app.core.config import settings
from app.core.logging import logger
from app.modules.file.models import FileModel


class FileService:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.minio_client = Minio(
            endpoint=f"{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket = settings.MINIO_BUCKET
        self.model = FileModel(db)

    async def ensure_bucket(self):
        exists = await self.minio_client.bucket_exists(self.bucket)
        if not exists:
            await self.minio_client.make_bucket(self.bucket)

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        user_id: str = "system",
        resize_width: Optional[int] = None,
    ) -> str:
        """Tải file lên MinIO S3, tự động resize ảnh với Pillow nếu requested."""
        await self.ensure_bucket()

        # Image processing with Pillow (substituting Sharp in Node.js)
        if resize_width and content_type.startswith("image/"):
            try:
                image = Image.open(io.BytesIO(file_bytes))
                aspect_ratio = image.height / image.width
                new_height = int(resize_width * aspect_ratio)
                resized_image = image.resize((resize_width, new_height), Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                resized_image.save(output, format=image.format or "JPEG")
                file_bytes = output.getvalue()
            except Exception as e:
                logger.warn("Image resize failed, using original file", error=str(e))

        ext = filename.split(".")[-1] if "." in filename else ""
        object_name = f"uploads/{uuid.uuid4().hex}.{ext}" if ext else f"uploads/{uuid.uuid4().hex}"

        await self.minio_client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=content_type,
        )
        # Save metadata to MongoDB
        await self.model.save_file_meta(
            filename=filename,
            object_name=object_name,
            size=len(file_bytes),
            content_type=content_type,
            user_id=user_id,
        )
        logger.info("Uploaded file to MinIO", object_name=object_name, size=len(file_bytes))
        return object_name

    async def delete_file(self, file_id: str) -> bool:
        """Xóa tệp tin khỏi MinIO và xóa metadata trong DB."""
        file_meta = await self.model.get_by_id(file_id)
        object_name = file_meta["objectName"] if file_meta else file_id

        try:
            await self.minio_client.remove_object(self.bucket, object_name)
        except Exception as e:
            logger.warn("Could not remove object from MinIO", object_name=object_name, error=str(e))

        await self.model.delete_meta(file_id)
        return True

    async def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Tạo Presigned Download URL."""
        return await self.minio_client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=object_name,
            expires=expires_seconds,
        )
