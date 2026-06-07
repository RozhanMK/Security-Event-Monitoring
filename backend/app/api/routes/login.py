from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep, RateLimitDep
from app.core import security
from app.core.config import settings
from app.models import Message, NewPassword, Token, UserPublic, UserUpdate, SecurityEventCreate, Severity
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)
from app.api.logging import get_current_function_name

router = APIRouter(tags=["login"])
 

@router.post("/login/access-token")
def login_access_token(
    rate_limit: RateLimitDep, session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.get_user_by_email(session=session, email=form_data.username)
    if user:
        user = crud.authenticate(
            session=session, email=form_data.username, password=form_data.password
        )
        if user:
            crud.create_event(
                session=session,
                event_type="auth.login_success",
                severity=Severity.LOW,
                source=get_current_function_name(),
                event_data={},
                ip=request.client.host,
                user_id=user.id,
            )
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            return Token(
                access_token=security.create_access_token(
                    user.id, expires_delta=access_token_expires
                )
            )
        reason = "Wrong Password"
        crud.create_event(
            session=session,
            event_type="auth.failed_login",
            severity=Severity.LOW,
            source=get_current_function_name(),
            event_data={"reason": reason},
            ip=request.client.host,
            user_id=user.id,
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")


    reason = "Email doesn't exist"
    crud.create_event(
        session=session,
        event_type="auth.failed_login",
        severity=Severity.LOW,
        source=get_current_function_name(),
        event_data={"reason": reason},
        ip=request.client.host,
        user_id=None
    )
    raise HTTPException(status_code=400, detail="Incorrect email or password")
    


@router.post("/login/test-token", response_model=UserPublic)
def test_token(rate_limit: RateLimitDep, current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(rate_limit: RateLimitDep, email: str, session: SessionDep, request:Request) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    # Always return the same response to prevent email enumeration attacks
    # Only send email if user actually exists
    if user:
        crud.create_event(
            session=session,
            event_type="auth.password_recovery_requested",
            severity=Severity.LOW,
            source=get_current_function_name(),
            event_data={},
            ip=request.client.host,
            user_id=user.id,
        )
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    else:
        crud.create_event(
            session=session,
            event_type="auth.failed_password_recovery",
            severity=Severity.LOW,
            source=get_current_function_name(),
            event_data={"reason": "Email not exist"},
            ip=request.client.host,
            user_id=None
        )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password/")
def reset_password(
    rate_limit: RateLimitDep,
    session: SessionDep,
    body: NewPassword,
    request: Request,
) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)

    if not email:
        crud.create_event(
            session=session,
            event_type="auth.failed_password_reset",
            severity=Severity.MEDIUM,
            source=get_current_function_name(),
            event_data={"reason": "Invalid or expired token"},
            ip=request.client.host,
            user_id=None,
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid token",
        )

    user = crud.get_user_by_email(
        session=session,
        email=email,
    )

    if not user:
        crud.create_event(
            session=session,
            event_type="auth.failed_password_reset",
            severity=Severity.HIGH,
            source=get_current_function_name(),
            event_data={
                "reason": "Token valid but user not found"
            },
            ip=request.client.host,
            user_id=None,
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid token",
        )

    user_in_update = UserUpdate(
        password=body.new_password
    )

    crud.update_user(
        session=session,
        db_user=user,
        user_in=user_in_update,
    )

    crud.create_event(
        session=session,
        event_type="auth.password_reset_success",
        severity=Severity.LOW,
        source=get_current_function_name(),
        event_data={},
        ip=request.client.host,
        user_id=user.id,
    )

    return Message(
        message="Password updated successfully"
    )

