import hashlib
import os
import hmac
import json
import base64
import time
from fastapi import HTTPException, status

# Fallback only. In production set the JWT_SECRET environment variable
# (wrangler secret put JWT_SECRET); main.py copies it in on every request.
SECRET_KEY = "rentpeople-super-secret-key-change-this-in-production"

_PBKDF2_ITERATIONS = 60_000


def set_secret(value: str) -> None:
    global SECRET_KEY
    if value and value.strip():
        SECRET_KEY = value.strip()
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _legacy_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    """Salted PBKDF2. Format: pbkdf2$iterations$salt$hash"""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt}${dk}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    stored = hashed_password or ""
    if stored.startswith("pbkdf2$"):
        try:
            _, iters, salt, expected = stored.split("$")
            dk = hashlib.pbkdf2_hmac(
                "sha256", plain_password.encode(), bytes.fromhex(salt), int(iters)
            ).hex()
            return hmac.compare_digest(dk, expected)
        except Exception:
            return False
    # Old accounts: plain SHA-256. They are upgraded on next successful login.
    return hmac.compare_digest(_legacy_hash(plain_password), stored)


def needs_rehash(hashed_password: str) -> bool:
    return not (hashed_password or "").startswith("pbkdf2$")


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_access_token(data: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS

    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())

    message = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
    signature_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")

        message = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
        expected_sig_b64 = _b64_encode(expected_sig)

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        payload = json.loads(_b64_decode(payload_b64))

        if payload.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        return payload

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")