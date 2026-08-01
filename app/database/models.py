from datetime import datetime, timezone
import enum
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class SubmissionStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentCategory(str, enum.Enum):
    STORE_RECEIPT = "store_receipt"
    RESTAURANT_RECEIPT = "restaurant_receipt"
    INVOICE = "invoice"
    USPS_SHIPPING_LABEL = "usps_shipping_label"
    UPS_SHIPPING_LABEL = "ups_shipping_label"
    FEDEX_SHIPPING_LABEL = "fedex_shipping_label"
    GENERIC_SHIPPING_LABEL = "generic_shipping_label"
    UNKNOWN = "unknown"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False), default=UserRole.USER, nullable=False
    )
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    document_category: Mapped[str] = mapped_column(String(64), default=DocumentCategory.UNKNOWN.value, nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    match_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus, native_enum=False), default=SubmissionStatus.UPLOADED, nullable=False, index=True
    )
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extracted_fields: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    corrected_fields: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="submissions")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="submission")


class TemplateModel(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    configuration_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submission_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    submission: Mapped[Optional["Submission"]] = relationship("Submission", back_populates="audit_logs")
