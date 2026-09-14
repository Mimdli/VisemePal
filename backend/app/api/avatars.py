"""缓存数字人 GLB：优先 TalkingHead 示例模型（jsDelivr），其次 Ready Player Me。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import BACKEND_DIR

router = APIRouter(tags=["avatars"])

CACHE_DIR = BACKEND_DIR / "var" / "avatars"
AVATAR_ID = re.compile(r"^[a-fA-F0-9]{16,40}$")
NAME_RE = re.compile(r"^[a-z0-9-]{3,40}$")
ALLOWED_HOSTS = {
    "models.readyplayer.me",
    "avatars.readyplayer.me",
    "cdn.jsdelivr.net",
    "raw.githubusercontent.com",
}
JSDELIVR = "https://cdn.jsdelivr.net/gh/met4citizen/TalkingHead@main/avatars"
KNOWN_AVATARS = {
    "brunette": f"{JSDELIVR}/brunette.glb",
    "avatarsdk": f"{JSDELIVR}/avatarsdk.glb",
    "avaturn": f"{JSDELIVR}/avaturn.glb",
}
RPM_QUERY = (
    "morphTargets=ARKit,Oculus Visemes,mouthOpen,mouthSmile,eyesClosed,"
    "eyesLookUp,eyesLookDown&textureSizeLimit=1024&textureFormat=png"
)


def _cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}.glb"


async def _download(url: str, dest: Path) -> None:
    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"模型下载失败：{exc}") from exc
    if response.status_code != 200 or len(response.content) < 1024:
        raise HTTPException(status_code=502, detail="数字人模型下载失败")
    dest.write_bytes(response.content)


def _source_url(avatar_id: str) -> str:
    if avatar_id in KNOWN_AVATARS:
        return KNOWN_AVATARS[avatar_id]
    if AVATAR_ID.match(avatar_id):
        return f"https://models.readyplayer.me/{avatar_id}.glb?{RPM_QUERY}"
    raise HTTPException(status_code=400, detail="无效的形象 ID")


@router.get("/avatars/fetch")
async def fetch_avatar(src: str = Query(..., min_length=12)) -> FileResponse:
    parsed = urlparse(src)
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=400, detail="只支持 Ready Player Me 或 TalkingHead 模型链接")
    key = "custom-" + hashlib.sha1(src.encode("utf-8")).hexdigest()[:16]
    dest = _cache_path(key)
    if not dest.exists():
        await _download(src, dest)
    return FileResponse(dest, media_type="model/gltf-binary")


@router.get("/avatars/{avatar_id}.glb")
async def get_avatar(avatar_id: str) -> FileResponse:
    if not NAME_RE.match(avatar_id) and not AVATAR_ID.match(avatar_id):
        raise HTTPException(status_code=400, detail="无效的形象 ID")
    dest = _cache_path(avatar_id)
    if not dest.exists() or dest.stat().st_size < 1024:
        await _download(_source_url(avatar_id), dest)
    return FileResponse(dest, media_type="model/gltf-binary")
