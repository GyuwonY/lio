
from fastapi import APIRouter, Depends, status, Response
from app.schemas.session_schema import CreateSessionRequest
from app.services.session_service import SessionService

router = APIRouter()


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def create_session(
    response: Response,
    session_service: SessionService = Depends(),
    *,
    creat_session_request: CreateSessionRequest,
):
    session_id = await session_service.create_session(portfolio_id=creat_session_request.portfolio_id)
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=session_service.context_expire_time
    )
    return
