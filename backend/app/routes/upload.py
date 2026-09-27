from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException
from routes.profile import get_current_user
import uuid

router = APIRouter()

# Replace this with your real public R2 URL
R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"

@router.post("/upload-avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    user_id = current_user["id"]
    key = f"profiles/{user_id}/avatar.jpg"

    # Upload to R2
    images = request.scope["env"].IMAGES
    await images.put(key, await file.read(), httpMetadata={"contentType": file.content_type})

    image_url = f"{R2_PUBLIC_URL}/{key}"

    # Save URL in database
    db = request.scope["env"].DB
    await db.prepare("UPDATE users SET image = ? WHERE id = ?").bind(image_url, user_id).run()

    return {"image": image_url, "message": "Avatar uploaded successfully"}


@router.post("/upload-gallery")
async def upload_gallery(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    user_id = current_user["id"]
    file_id = str(uuid.uuid4())[:8]
    key = f"profiles/{user_id}/gallery/{file_id}.jpg"

    images = request.scope["env"].IMAGES
    await images.put(key, await file.read(), httpMetadata={"contentType": file.content_type})

    image_url = f"{R2_PUBLIC_URL}/{key}"

    return {"url": image_url, "message": "Gallery image uploaded successfully"}