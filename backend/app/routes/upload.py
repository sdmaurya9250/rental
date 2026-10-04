# from fastapi import APIRouter, Request, Depends, HTTPException
# from routes.profile import get_current_user
# import uuid
#
# router = APIRouter()
#
# R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"
#
#
# @router.post("/upload-avatar")
# async def upload_avatar(
#     request: Request,
#     current_user: dict = Depends(get_current_user)
# ):
#     content_type = request.headers.get("content-type", "")
#     if not content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="Only image files are allowed")
#
#     body = await request.body()
#     if not body:
#         raise HTTPException(status_code=400, detail="No file received")
#
#     user_id = current_user["id"]
#     key = f"profiles/{user_id}/avatar.jpg"
#
#     images = request.scope["env"].IMAGES
#     await images.put(key, body, httpMetadata={"contentType": content_type})
#
#     image_url = f"{R2_PUBLIC_URL}/{key}"
#
#     # Save URL in database
#     db = request.scope["env"].DB
#     await db.prepare("UPDATE users SET image = ? WHERE id = ?").bind(image_url, user_id).run()
#
#     return {"image": image_url, "message": "Avatar uploaded successfully"}
#
#
# @router.post("/upload-gallery")
# async def upload_gallery(
#     request: Request,
#     current_user: dict = Depends(get_current_user)
# ):
#     content_type = request.headers.get("content-type", "")
#     if not content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="Only image files are allowed")
#
#     body = await request.body()
#     if not body:
#         raise HTTPException(status_code=400, detail="No file received")
#
#     user_id = current_user["id"]
#     file_id = str(uuid.uuid4())[:8]
#     key = f"profiles/{user_id}/gallery/{file_id}.jpg"
#
#     images = request.scope["env"].IMAGES
#     await images.put(key, body, httpMetadata={"contentType": content_type})
#
#     image_url = f"{R2_PUBLIC_URL}/{key}"
#
#     return {"url": image_url, "message": "Gallery image uploaded successfully"}


from fastapi import APIRouter, Request, Depends, HTTPException
from routes.profile import get_current_user
import uuid
import json

router = APIRouter()

R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"


def _ext_from_content_type(content_type: str) -> str:
    if "png" in content_type:
        return "png"
    if "webp" in content_type:
        return "webp"
    if "gif" in content_type:
        return "gif"
    return "jpg"


@router.post("/upload-avatar")
async def upload_avatar(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    content_type = request.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No file received")

    user_id = current_user["id"]
    ext = _ext_from_content_type(content_type)
    key = f"profiles/{user_id}/avatar.{ext}"

    images = request.scope["env"].IMAGES
    await images.put(key, body, httpMetadata={"contentType": content_type})

    image_url = f"{R2_PUBLIC_URL}/{key}"

    db = request.scope["env"].DB
    await db.prepare(
        "UPDATE users SET image = ? WHERE id = ?"
    ).bind(image_url, user_id).run()

    return {
        "image": image_url,
        "message": "Avatar uploaded successfully",
    }


@router.post("/upload-gallery")
async def upload_gallery(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    content_type = request.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No file received")

    user_id = current_user["id"]
    file_id = str(uuid.uuid4())[:8]
    ext = _ext_from_content_type(content_type)
    key = f"profiles/{user_id}/gallery/{file_id}.{ext}"

    images = request.scope["env"].IMAGES
    await images.put(key, body, httpMetadata={"contentType": content_type})

    image_url = f"{R2_PUBLIC_URL}/{key}"

    # Append to users.gallery in D1
    db = request.scope["env"].DB
    row = await db.prepare(
        "SELECT gallery FROM users WHERE id = ?"
    ).bind(user_id).first()

    gallery = []
    if row:
        raw = dict(row).get("gallery")
        if raw:
            try:
                gallery = json.loads(raw) if isinstance(raw, str) else list(raw)
            except Exception:
                gallery = []

    if image_url not in gallery:
        gallery.append(image_url)

    # Optional: max 6 images
    gallery = gallery[-6:]

    await db.prepare(
        "UPDATE users SET gallery = ? WHERE id = ?"
    ).bind(json.dumps(gallery), user_id).run()

    return {
        "url": image_url,
        "gallery": gallery,
        "message": "Gallery image uploaded successfully",
    }