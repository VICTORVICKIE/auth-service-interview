from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Boolean,
    ForeignKey,
    JSON,
    TIMESTAMP,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Test(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class Organisation(Base):
    __tablename__ = "organisation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    status = Column(Integer, default=0, nullable=False)
    personal = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    members = relationship("Member", back_populates="organisation")
    roles = relationship("Role", back_populates="organisation")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile = Column(JSON, default={}, nullable=False)
    status = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    members = relationship("Member", back_populates="user")


class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    org_id = Column(
        Integer,
        ForeignKey("organisation.id", ondelete="CASCADE"),
        nullable=False,
    )

    organisation = relationship("Organisation", back_populates="roles")


class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(
        Integer,
        ForeignKey("organisation.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    role_id = Column(
        Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    organisation = relationship("Organisation", back_populates="members")
    user = relationship("User", back_populates="members")
