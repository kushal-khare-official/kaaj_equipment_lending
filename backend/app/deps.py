from fastapi import Header, HTTPException, status

from app.shared.enums import Role


def current_role(x_role: str | None = Header(default=None)) -> Role:
    if x_role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Role header")
    try:
        return Role(x_role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")

