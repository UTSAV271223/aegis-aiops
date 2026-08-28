from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from backend.core.config import settings
from backend.core.security import create_access_token, verify_password, get_password_hash
from backend.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

DEMO_USER = {
    "username": "admin@aegis.internal",
    "hashed_password": get_password_hash("AegisSecure2026!")
}

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != DEMO_USER["username"] or not verify_password(form_data.password, DEMO_USER["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": DEMO_USER["username"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}