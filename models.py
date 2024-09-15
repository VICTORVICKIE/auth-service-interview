from sqlalchemy import (
    JSON,
    func,
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Organisation(Base):
    __tablename__ = "organisation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    status = Column(Integer, default=0, nullable=False)
    personal = Column(Boolean, default=False, nullable=True)
    settings = Column(JSON, default={}, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
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
    settings = Column(JSON, default={}, nullable=True)
    status = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
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
    settings = Column(JSON, default={}, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    organisation = relationship("Organisation", back_populates="members")
    user = relationship("User", back_populates="members")
