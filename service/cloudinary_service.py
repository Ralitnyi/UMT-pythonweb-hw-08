"""Cloudinary image upload service.

This module provides functionality for uploading user avatar images
to Cloudinary cloud storage with automatic transformation (resizing).
"""

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
    """Upload a user's avatar image to Cloudinary.

    Automatically resizes the image to 250x250 pixels and stores it
    in a user-specific folder.

    Args:
        file_data: The binary data of the image file to upload.
        user_id: The user's unique identifier for folder organization.

    Returns:
        str: The secure URL of the uploaded avatar image.
    """
    result = cloudinary.uploader.upload(
        file_data,
        folder=f'avatars/user_{user_id}',
        transformation=[
            {'width': 250, 'height': 250, 'crop': 'fill'},
        ],
    )
    return result.get('secure_url')