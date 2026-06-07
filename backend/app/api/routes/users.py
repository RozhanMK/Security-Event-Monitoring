from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    RateLimitDep
)
from app.core.security import get_password_hash, verify_password
from app.api.logging import get_current_function_name
from app.models import (
    UpdatePassword,
    UserPublic,
    UserRegister,
    UserUpdate,
    Message,
    Severity,
)

router = APIRouter(prefix="/users", tags=["users"])

@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdate, current_user: CurrentUser, rate_limit: RateLimitDep, request: Request
) -> Any:
    """
    Update own user.
    """
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            crud.create_event(
                session=session,
                event_type="user.profile_update_failed",
                severity=Severity.LOW,
                source=get_current_function_name(),
                event_data={
                    "reason": "email_already_exists"
                },
                ip=request.client.host,
                user_id=current_user.id,
            )
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    crud.create_event(
        session=session,
        event_type="user.profile_updated",
        severity=Severity.LOW,
        source=get_current_function_name(),
        event_data={
            "fields_changed": list(user_in.keys())
        },
        ip=request.client.host,
        user_id=current_user.id,
    )
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser, rate_limit: RateLimitDep, request: Request
) -> Any:
    """
    Update own password.
    """
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        crud.create_event(
            session=session,
            event_type="auth.failed_password_change",
            severity=Severity.MEDIUM,
            source=get_current_function_name(),
            event_data={
                "reason": "incorrect_current_password"
            },
            ip=request.client.host,
            user_id=current_user.id,
        )
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        crud.create_event(
            session=session,
            event_type="auth.failed_password_change",
            severity=Severity.LOW,
            source=get_current_function_name(),
            event_data={
                "reason": "same_password"
            },
            ip=request.client.host,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    crud.create_event(
        session=session,
        event_type="auth.password_changed",
        severity=Severity.LOW,
        source=get_current_function_name(),
        event_data={},
        ip=request.client.host,
        user_id=current_user.id,
    )
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser, request: Request) -> Any:
    """
    Delete own user.
    """
    session.delete(current_user)
    session.commit()
    crud.create_event(
        session=session,
        event_type="user.account_deleted",
        severity=Severity.HIGH,
        source=get_current_function_name(),
        event_data={},
        ip=request.client.host,
        user_id=current_user.id,
    )
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(rate_limit: RateLimitDep, session: SessionDep, user_in: UserRegister, request: Request) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        crud.create_event(
            session=session,
            event_type="auth.failed_signup",
            severity=Severity.LOW,
            source=get_current_function_name(),
            event_data={
                "reason": "email_already_exists"
            },
            ip=request.client.host,
            user_id=None,
        )
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user = crud.create_user(session=session, user_create=user_in)
    crud.create_event(
        session=session,
        event_type="auth.signup_success",
        severity=Severity.LOW,
        source=get_current_function_name(),
        event_data={},
        ip=request.client.host,
        user_id=user.id,
    )
    return user

