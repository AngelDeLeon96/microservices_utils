from fastapi import HTTPException, Depends
from .jwt_utils import JwtHandler
import httpx
import os

PERMISSIONS_SERVICE_URL = os.getenv("PERMISSIONS_SERVICE_URL", "http://localhost:8000")


async def check_permission(role_name: str, resource: str, action: str) -> bool:
    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{PERMISSIONS_SERVICE_URL}/permissions/check",
            json={"role_name": role_name, "resource": resource, "action": action},
        )
        print(response.json())
        if response.status_code == 200:
            data = response.json().get("data", {})
            return data.get("has_permission", False)
        raise HTTPException(status_code=500, detail="Permission check failed")


def permission_required_dependency(resource: str, action: str):

    async def dependency(user=Depends(JwtHandler.get_current_user_role)):
        # Asume que `user` es un dict con 'role' (ej. {'id': 'user_id', 'role': 'admin'})
        # Si es str, asume que es el rol directamente
        if isinstance(user, str):
            role = user
        else:
            role = user.get("role")

        if not role:
            raise HTTPException(status_code=401, detail="Role not provided")

        has_perm = await check_permission(role, resource, action)
        print("has", has_perm)
        if not has_perm:
            raise HTTPException(status_code=403, detail="Permission denied")

        return user

    return dependency
