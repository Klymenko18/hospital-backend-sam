from __future__ import annotations

from typing import Any, Dict, Optional


def extract_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts JWT claims from an API Gateway HTTP API Lambda proxy event.
    """
    ctx = event.get("requestContext", {})
    authorizer = ctx.get("authorizer", {})
    jwt = authorizer.get("jwt", {})
    claims = jwt.get("claims") or {}
    return claims


def require_admin(claims: Dict[str, Any]) -> None:
    """
    Ensures the token belongs to a user in the Admin group.
    """
    groups = claims.get("cognito:groups")
    if isinstance(groups, str):
        is_admin = "Admin" in groups.split(",")
    elif isinstance(groups, list):
        is_admin = "Admin" in groups
    else:
        is_admin = False
    if not is_admin:
        raise PermissionError("Admin privileges required.")


def get_caller_sub(claims: Dict[str, Any]) -> str:
    """
    Returns the caller's Cognito subject (sub).
    """
    sub = claims.get("sub")
    if not sub:
        raise PermissionError("Missing subject in token.")
    return sub
