import os
from datetime import datetime, timedelta
from typing import Annotated, List, Optional, Tuple

import resend
from faker import Faker
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request

from auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models import Member, Organisation, Role, User

load_dotenv()


POSTGRES_URL = os.getenv("POSTGRES_URL")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

assert POSTGRES_URL is not None
assert RESEND_API_KEY is not None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(POSTGRES_URL),
)
Base = declarative_base()


fake = Faker()
app = FastAPI(title="Auth Service API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")
resend.api_key = RESEND_API_KEY


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def send_mail(to: List[str], subject: str, body: str):
    params: resend.Emails.SendParams = {
        "from": "onboarding@resend.dev",
        "to": to,
        "subject": subject,
        "html": body,
    }
    _: resend.Email = resend.Emails.send(params)
    return {"message": "Mail Sent"}


@app.get("/")
def read_root():
    return {"Hello": "World"}


class UserData(BaseModel):
    org: str
    email: str
    password: str


@app.post("/signup")
def signup(
    req: Request,
    user_data: Annotated[UserData, Form()],
    db: Session = Depends(get_db),
):
    org = (
        db.query(Organisation)
        .filter(Organisation.name == user_data.org)
        .first()
    )
    if org:
        raise HTTPException(
            status_code=400, detail="Organisation already exist"
        )

    org = Organisation(name=user_data.org)
    db.add(org)
    db.commit()
    db.refresh(org)

    hashed_password = hash_password(user_data.password)
    user = User(email=user_data.email, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    role = (
        db.query(Role)
        .filter(Role.name == "owner", Role.org_id == org.id)
        .first()
    )
    if not role:
        role = Role(name="owner", org_id=org.id)
        db.add(role)
        db.commit()

    member = Member(user_id=user.id, org_id=org.id, role_id=role.id)
    db.add(member)
    db.commit()

    verify_token = create_access_token(
        data={"id": member.id}, expires_delta=timedelta(days=7)
    )

    send_mail(
        to=["s.vickie14@gmail.com"],
        subject="AuthService - User Registered",
        body=f"User with following mail {user_data.email} registered to {user_data.org} as {role.name}, Please verify using {req.base_url}verify-email/?token={verify_token}",
    )
    return {
        "message": "Verification link sent, Please verify the email",
        "verify_token": verify_token,
    }


class RoleData(BaseModel):
    email: str
    org: str
    role: str


@app.get("/verify-email/")
def verify_email(token: str, db: Session = Depends(get_db)):
    token_data = decode_token(token)

    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid Token")

    member = db.query(Member).filter(Member.id == token_data.get("id")).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    user = db.query(User).filter(User.id == member.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    member.status = 1
    db.commit()
    return {"message": "User verified successfully"}


@app.get("/create-member")
def create_member(token: str, db: Session = Depends(get_db)):
    user_data = decode_token(token)
    if user_data is None:
        raise HTTPException(status_code=401, detail="Invalid Token")

    org = (
        db.query(Organisation)
        .filter(Organisation.name == user_data.get("org"))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    random_password = fake.password(10)
    hashed_password = hash_password(random_password)
    user = User(email=user_data.get("email"), password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    role = (
        db.query(Role)
        .filter(Role.name == "member", Role.org_id == org.id)
        .first()
    )
    if not role:
        role = Role(name="member", org_id=org.id)
        db.add(role)
        db.commit()

    member = Member(user_id=user.id, org_id=org.id, role_id=role.id, status=1)
    db.add(member)
    db.commit()

    send_mail(
        to=["s.vickie14@gmail.com"],
        subject="AuthService - Joined Organisation",
        body=f"User with following mail {user.email} joined {org.name} as {role.name} with default password - {random_password}",
    )
    return {"message": "Member joined"}


@app.post("/invite-member")
def invite_member(
    req: Request,
    invite_data: RoleData,
    db: Session = Depends(get_db),
    access_token: str = Depends(oauth2_scheme),
):
    user_data = decode_token(access_token)
    if user_data is None:
        raise HTTPException(status_code=401, detail="Invalid Token")

    if user_data.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Insufficient Permission")

    org = (
        db.query(Organisation)
        .filter(Organisation.name == user_data.get("org"))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    inviting_member = (
        db.query(Member).filter(Member.id == user_data.get("id")).first()
    )

    if not inviting_member:
        raise HTTPException(
            status_code=403,
            detail=f"Not authorized to invite members for {user_data.get('org')}",
        )

    invited_user = (
        db.query(User).filter(User.email == invite_data.email).first()
    )
    if invited_user:
        existing_member = (
            db.query(Member)
            .filter(Member.user_id == invited_user.id, Member.org_id == org.id)
            .first()
        )
        if existing_member:
            raise HTTPException(
                status_code=400,
                detail="User is already a member of this organisation",
            )

    invite_token = create_access_token(
        data={"email": invite_data.email, "org": org.name, "invite": True},
        expires_delta=timedelta(days=7),
    )
    send_mail(
        to=["s.vickie14@gmail.com"],
        subject="AuthService - Member Invite",
        body=f"You ({invite_data.email}) have been invited to {org.name} as member, Invitation - {req.base_url}create-member/?token={invite_token}",
    )
    return {
        "message": f"Successfully invited {invite_data.email} to {org.name}",
        "invite_token": invite_token,
    }


@app.post("/signin")
def signin(user: Annotated[UserData, Form()], db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(
        user.password, str(db_user.password)
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    org = db.query(Organisation).filter(Organisation.name == user.org).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = (
        db.query(Member)
        .filter(Member.user_id == db_user.id, Member.org_id == org.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=404, detail="User is not a member of this organization"
        )

    if not bool(membership.status):
        raise HTTPException(
            status_code=401,
            detail=f"Please verify email {db_user.email} by following verification link in the email.",
        )

    role = (
        db.query(Role)
        .join(Member, Role.id == Member.role_id)
        .filter(Member.user_id == db_user.id, Member.org_id == org.id)
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=404, detail="Role not present in organization"
        )

    access_token = create_access_token(
        data={
            "email": db_user.email,
            "id": membership.id,
            "org": org.name,
            "role": role.name,
        }
    )
    refresh_token = create_refresh_token(
        data={
            "email": db_user.email,
            "id": membership.id,
            "org": org.name,
            "role": role.name,
        }
    )
    send_mail(
        to=["s.vickie14@gmail.com"],
        subject="AuthService - Login Alert",
        body=f"User with following mail {user.email} has logged in",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/refresh-token/")
def refresh_token(
    access_token: str = Depends(oauth2_scheme),
    refresh_token: str = Form(...),
):
    refresh_token_data = decode_token(refresh_token)
    if refresh_token_data is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token_data = decode_token(access_token)
    if access_token_data is None:
        new_access_token = create_access_token(
            data={"email": refresh_token_data["email"]}
        )
        return {
            "message": "Access token is invalid but Refresh is valid",
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    else:
        return {
            "message": "Access token is still valid",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


class PassReset(BaseModel):
    email: str
    old: str
    new: str


@app.post("/reset-password")
def reset_password(
    user_data: Annotated[PassReset, Form()],
    db: Session = Depends(get_db),
    access_token: str = Depends(oauth2_scheme),
):
    access_token_data = decode_token(access_token)
    if access_token_data is None:
        raise HTTPException(status_code=401, detail="Invalid Token")

    db_user = db.query(User).filter(User.email == user_data.email).first()
    if (
        not db_user
        or not verify_password(user_data.old, str(db_user.password))
        or user_data.email != access_token_data.get("email")
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db_user.password = hash_password(user_data.new)
    db.commit()

    send_mail(
        to=["s.vickie14@gmail.com"],
        subject="AuthService - Password Updated",
        body=f"User with following mail {user_data.email} updated their password",
    )
    return {"message": "Password updated successfully"}


@app.post("/update-role/")
def update_role(
    user_data: RoleData,
    db: Session = Depends(get_db),
    access_token: str = Depends(oauth2_scheme),
):
    access_token_data = decode_token(access_token)
    if access_token_data is None:
        raise HTTPException(status_code=401, detail="Invalid Token")

    if access_token_data.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Insufficient Permission")

    db_user = db.query(User).filter(User.email == user_data.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    org = (
        db.query(Organisation)
        .filter(Organisation.name == user_data.org)
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = (
        db.query(Member)
        .filter(Member.user_id == db_user.id, Member.org_id == org.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=403, detail="User is not a member of this organization"
        )

    org_id = membership.org_id
    role = (
        db.query(Role)
        .filter(Role.name == user_data.role, Role.org_id == org_id)
        .first()
    )

    if not role:
        role = Role(name=user_data.role, org_id=org_id)
        db.add(role)
        db.commit()
        db.refresh(role)

    membership.role_id = role.id
    db.commit()
    return {"message": f"Member role updated to {user_data.role} successfully"}


class MemberDelete(BaseModel):
    email: str
    org: str


@app.delete("/delete-member/")
def delete_member(
    user_data: MemberDelete,
    db: Session = Depends(get_db),
    access_token: str = Depends(oauth2_scheme),
):
    access_token_data = decode_token(access_token)
    if access_token_data is None:
        raise HTTPException(status_code=401, detail="Invalid Token")

    if access_token_data.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Insufficient Permission")

    db_user = db.query(User).filter(User.email == user_data.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    org = (
        db.query(Organisation)
        .filter(Organisation.name == user_data.org)
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = (
        db.query(Member)
        .filter(Member.user_id == db_user.id, Member.org_id == org.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=403, detail="User is not a member of this organization"
        )
    db.delete(membership)
    db.commit()
    return {
        "message": f"Member {user_data.email} removed from {user_data.org} successfully"
    }


def parse_date_range(date_range: str) -> Tuple[datetime, datetime]:
    try:
        begin_str, end_str = date_range.split(" to ")
        begin_dt = datetime.strptime(begin_str, "%Y-%m-%dT%H:%M:%S")
        end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%S")
        return begin_dt, end_dt
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date range format. Use ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS'.",
        )


@app.get("/role-wise-count")
def get_role_wise_count(
    db: Session = Depends(get_db),
    created_range: Optional[str] = Query(
        None,
        description="Date range filter (ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS')",
    ),
    updated_range: Optional[str] = Query(
        None,
        description="Date range filter (ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS')",
    ),
    status: Optional[int] = Query(None, description="Filter by member status"),
):
    query = db.query(
        Role.name.label("role_name"),
        func.count(Member.user_id).label("member_count"),
    ).join(Member, Role.id == Member.role_id)

    # Apply status filter if provided
    if status is not None:
        query = query.filter(Member.status == status)

    # Apply date range filter if provided
    if created_range:
        try:
            begin_dt, end_dt = parse_date_range(created_range)
            query = query.filter(
                Member.created_at >= begin_dt, Member.created_at <= end_dt
            )
        except HTTPException as e:
            raise e
    if updated_range:
        try:
            begin_dt, end_dt = parse_date_range(updated_range)
            query = query.filter(
                Member.created_at >= begin_dt, Member.created_at <= end_dt
            )
        except HTTPException as e:
            raise e

    # Group by role name and get the counts
    result = query.group_by(Role.name).all()

    return [
        {"role_name": row.role_name, "member_count": row.member_count}
        for row in result
    ]


@app.get("/org-wise-count")
def get_organisation_wise_count(
    db: Session = Depends(get_db),
    created_range: Optional[str] = Query(
        None,
        description="Date range filter (ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS')",
    ),
    updated_range: Optional[str] = Query(
        None,
        description="Date range filter (ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS')",
    ),
    status: Optional[int] = Query(None, description="Filter by org status"),
):
    query = db.query(
        Organisation.name.label("organisation_name"),
        func.count(Member.user_id).label("member_count"),
    ).join(Member, Organisation.id == Member.org_id)

    # Apply status filter if provided
    if status is not None:
        query = query.filter(Organisation.status == status)

    # Apply date range filter if provided
    if created_range:
        try:
            begin_dt, end_dt = parse_date_range(created_range)
            query = query.filter(
                Organisation.created_at >= begin_dt,
                Organisation.created_at <= end_dt,
            )
        except HTTPException as e:
            raise e
    if updated_range:
        try:
            begin_dt, end_dt = parse_date_range(updated_range)
            query = query.filter(
                Organisation.created_at >= begin_dt,
                Organisation.created_at <= end_dt,
            )
        except HTTPException as e:
            raise e
    result = query.group_by(Organisation.name).all()

    return [
        {
            "organisation_name": row.organisation_name,
            "member_count": row.member_count,
        }
        for row in result
    ]


@app.get("/org-role-wise-count")
def get_organisation_role_wise_count(
    r: Request,
    db: Session = Depends(get_db),
    created_range: Optional[str] = Query(
        None,
        description="Date range filter (ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS')",
    ),
    updated_range: Optional[str] = Query(
        None,
        description="Date range filter (ISO format: 'YYYY-MM-DDTHH:MM:SS to YYYY-MM-DDTHH:MM:SS')",
    ),
    org_status: Optional[int] = Query(
        None, description="Filter by org status"
    ),
    member_status: Optional[int] = Query(
        None, description="Filter by member status"
    ),
):
    query = (
        db.query(
            Organisation.name.label("organisation_name"),
            Role.name.label("role_name"),
            func.count(Member.user_id).label("member_count"),
        )
        .join(Member, Organisation.id == Member.org_id)
        .join(Role, Member.role_id == Role.id)
    )

    # Apply status filter if provided
    if org_status is not None:
        query = query.filter(Organisation.status == org_status)

    if member_status is not None:
        query = query.filter(Member.status == member_status)
    # Apply date range filter if provided
    if created_range:
        try:
            begin_dt, end_dt = parse_date_range(created_range)
            query = query.filter(
                Organisation.created_at >= begin_dt,
                Organisation.created_at <= end_dt,
                Member.created_at >= begin_dt,
                Member.created_at <= end_dt,
            )
        except HTTPException as e:
            raise e
    if updated_range:
        try:
            begin_dt, end_dt = parse_date_range(updated_range)
            query = query.filter(
                Organisation.created_at >= begin_dt,
                Organisation.created_at <= end_dt,
                Member.created_at >= begin_dt,
                Member.created_at <= end_dt,
            )
        except HTTPException as e:
            raise e

    result = query.group_by(Organisation.name, Role.name).all()

    return [
        {
            "organisation_name": row.organisation_name,
            "role_name": row.role_name,
            "member_count": row.member_count,
        }
        for row in result
    ]
