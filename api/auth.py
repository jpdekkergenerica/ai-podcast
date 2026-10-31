import os
import time
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS = "https://appleid.apple.com/auth/keys"
_DEV_SECRET = "dev-secret-change-me-use-32chars!!"
JWT_SECRET = os.environ.get("API_JWT_SECRET", _DEV_SECRET)
JWT_TTL_SECONDS = int(os.environ.get("API_JWT_TTL", str(60 * 60 * 24 * 30)))
APPLE_CLIENT_ID = os.environ.get("APPLE_CLIENT_ID", "")
AUTH_DEV_MODE = os.environ.get("AUTH_DEV_MODE", "0") == "1"

if not AUTH_DEV_MODE and (len(JWT_SECRET) < 32 or JWT_SECRET == _DEV_SECRET):
    raise RuntimeError("Zet API_JWT_SECRET (minstens 32 tekens) of start lokaal met AUTH_DEV_MODE=1")

_bearer = HTTPBearer(auto_error=False)
_jwk_client: PyJWKClient | None = None


def _apple_keys() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(APPLE_JWKS)
    return _jwk_client


def verify_apple_identity_token(identity_token: str) -> dict:
    """Controleert het Apple identity token. In AUTH_DEV_MODE wordt het niet cryptografisch gecontroleerd."""
    if AUTH_DEV_MODE:
        try:
            return jwt.decode(identity_token, options={"verify_signature": False})
        except jwt.PyJWTError as e:
            # Dev: accepteer ook een kale "sub"-string via het login-endpoint
            raise HTTPException(400, f"Ongeldig dev-token: {e}") from e

    if not APPLE_CLIENT_ID:
        raise HTTPException(500, "APPLE_CLIENT_ID ontbreekt")
    try:
        key = _apple_keys().get_signing_key_from_jwt(identity_token)
        return jwt.decode(
            identity_token,
            key.key,
            algorithms=["RS256"],
            audience=APPLE_CLIENT_ID,
            issuer=APPLE_ISSUER,
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Apple-token ongeldig: {e}") from e


def issue_access_token(user: User) -> str:
    now = int(time.time())
    payload = {"sub": user.id, "apple_sub": user.apple_sub, "iat": now, "exp": now + JWT_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Login vereist")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Sessie ongeldig: {e}") from e
    user = db.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Gebruiker niet gevonden")
    return user
