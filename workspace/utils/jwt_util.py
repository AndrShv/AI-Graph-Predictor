from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
import jwt
from jwt.exceptions import InvalidTokenError

from workspace.configs.settings import settings


class JwtUtil:
    @staticmethod
    def generate_token(
        user_id: UUID | str,
        email: str,
        roles: List[str],
        subscription: Optional[str] = "FREE",
        client_ip: Optional[str] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
        expiration = now + timedelta(minutes=expire_minutes)

        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "email": email,
            "roles": roles,
            "subscription": subscription,
            "client_ip": client_ip,
            "iat": now,
            "exp": expiration,
        }

        algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=algorithm)

    @staticmethod
    def parse_claims(token: str) -> Optional[Dict[str, Any]]:
        try:
            algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
            return jwt.decode(
                token, settings.JWT_SECRET, algorithms=[algorithm]
            )
        except InvalidTokenError:
            return None

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Алиас для parse_claims для единого интерфейса."""
        return JwtUtil.parse_claims(token)

    @staticmethod
    def is_valid(token: str) -> bool:
        return JwtUtil.parse_claims(token) is not None

    @staticmethod
    def get_user_id(token: str) -> Optional[str]:
        claims = JwtUtil.parse_claims(token)
        if not claims:
            return None
        return claims.get("sub") or claims.get("user_id") or claims.get("userId")

    @staticmethod
    def get_roles(token: str) -> List[str]:
        claims = JwtUtil.parse_claims(token)
        if not claims:
            return []
        return claims.get("roles") or claims.get("authorities") or []

    @staticmethod
    def get_subscription(token: str) -> Optional[str]:
        claims = JwtUtil.parse_claims(token)
        return claims.get("subscription") if claims else None

    @staticmethod
    def get_client_ip(token: str) -> Optional[str]:
        claims = JwtUtil.parse_claims(token)
        return (claims.get("client_ip") or claims.get("clientIp")) if claims else None