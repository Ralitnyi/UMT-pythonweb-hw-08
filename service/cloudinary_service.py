import cloudinary
import cloudinary.uploader

from db import settings


cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


async def upload_avatar(file_data: bytes, user_id: int) -> str:
    """Upload avatar to Cloudinary and return URL"""
    result = cloudinary.uploader.upload(
        file_data,
        folder=f'avatars/user_{user_id}',
        transformation=[
            {'width': 250, 'height': 250, 'crop': 'fill'},
        ],
    )
    return result.get('secure_url')