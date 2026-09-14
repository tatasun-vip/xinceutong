"""
FastAPI 依赖注入
- get_current_user：从 Authorization 头解析 JWT，返回当前用户
- require_role：按角色鉴权
- get_redis：redis 客户端
- get_db：数据库 session（已在 database.py 定义）
"""
from enum import Enum
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.redis_client import get_redis as _get_redis
from app.models.user import User


class UserRole(str, Enum):
    USER = "user"
    PROMOTER = "promoter"
    ADMIN = "admin"


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 Authorization: Bearer <token> 头解析 JWT，查询并返回用户对象
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭证",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"token 无效：{e}",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 缺少 sub")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.status != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已停用")

    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    可选当前用户：未登录返回 None，不抛异常
    用于：测评提交等"匿名可用 / 登录可享特权"的接口
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user or user.status != 1:
            return None
        return user
    except Exception:
        return None


def require_role(*allowed_roles: UserRole):
    """
    工厂：构造一个依赖，校验当前用户角色必须在 allowed_roles 内
    用法：Depends(require_role(UserRole.ADMIN))
    """
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if UserRole(user.role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return user

    return _checker


def get_redis():
    """FastAPI 依赖：redis client（与 redis_client.get_redis 等价，方便 from app.core.deps import）"""
    return _get_redis()
