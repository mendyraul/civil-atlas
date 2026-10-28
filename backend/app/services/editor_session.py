"""Short-lived editorial sessions. The shared API key never becomes browser state."""

import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import HTTPException, Request
from app.core.config import settings

COOKIE = "civil_atlas_editor"
TTL = 2 * 60 * 60


def enabled():
    if not settings.editor_ui_enabled:
        raise HTTPException(404, "Not found")
    if not settings.editorial_api_key:
        raise HTTPException(
            503, "Configure EDITORIAL_API_KEY before enabling the editor"
        )


def sign(body):
    key = settings.editorial_api_key.encode()
    return hmac.new(
        key, b"civil-atlas-editor-v1:" + body.encode(), hashlib.sha256
    ).hexdigest()


def issue_session(reviewer):
    data = {
        "reviewer": reviewer,
        "expires": int(time.time()) + TTL,
        "csrf": secrets.token_hex(32),
    }
    body = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return body + "." + sign(body), data


def read_session(request: Request):
    enabled()
    try:
        body, signature = request.cookies.get(COOKIE, "").split(".")
        if not hmac.compare_digest(signature.encode(), sign(body).encode()):
            raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if (
            data["expires"] <= time.time()
            or not isinstance(data["reviewer"], str)
            or not data["reviewer"].strip()
        ):
            raise ValueError()
        return data
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise HTTPException(401, "Editor session expired. Sign in again.")


def same_origin(request):
    if request.headers.get("origin") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Editor changes require the same origin")


def require_editor(request: Request):
    data = read_session(request)
    if request.method not in ("GET", "HEAD"):
        same_origin(request)
        if not hmac.compare_digest(
            request.headers.get("x-csrf-token", "").encode(), data["csrf"].encode()
        ):
            raise HTTPException(403, "Reload the editor before saving")
    return data
