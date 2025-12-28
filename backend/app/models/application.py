from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, JSON, Uuid
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.shared.enums import ApplicationStatus, DocumentStatus


class Application(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "applications"

    status = Column(Enum(ApplicationStatus, name="application_status"), nullable=False, default=ApplicationStatus.PROCESSING)
    merchant_email = Column(String, nullable=False)

    guarantors = relationship("Guarantor", back_populates="application", cascade="all, delete-orphan")
    business_credit = relationship("BusinessCredit", back_populates="application", uselist=False, cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="application", cascade="all, delete-orphan")
    loan_request = relationship("LoanRequest", back_populates="application", uselist=False, cascade="all, delete-orphan")
    document_requests = relationship("DocumentRequest", back_populates="application", cascade="all, delete-orphan")
    match_runs = relationship("MatchRun", back_populates="application", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan")


class Guarantor(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "guarantors"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False)
    is_primary = Column(Boolean, default=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    fico = Column(Integer, nullable=True)
    cdl_flag = Column(Boolean, default=False, nullable=False)
    homeownership = Column(Boolean, default=False, nullable=True)
    bankruptcy_discharged_at = Column(Date, nullable=True)

    application = relationship("Application", back_populates="guarantors")


class BusinessCredit(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "business_credit"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False, unique=True)
    paynet_score = Column(Integer, nullable=True)
    tradelines = Column(JSON, nullable=True)
    revolving_utilization = Column(Integer, nullable=True)

    application = relationship("Application", back_populates="business_credit")


class Equipment(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "equipment"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False)
    type = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    mileage = Column(Integer, nullable=True)
    titled = Column(Boolean, default=False, nullable=False)
    private_party = Column(Boolean, default=False, nullable=False)
    hours = Column(Integer, nullable=True)

    application = relationship("Application", back_populates="equipment")


class LoanRequest(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "loan_requests"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False, unique=True)
    amount = Column(Numeric(14, 2), nullable=True)
    term_months = Column(Integer, nullable=True)
    down_payment = Column(Numeric(14, 2), nullable=True)

    application = relationship("Application", back_populates="loan_request")


class DocumentRequest(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "document_requests"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False)
    type = Column(String, nullable=False)
    status = Column(Enum(DocumentStatus, name="document_status"), nullable=False, default=DocumentStatus.REQUESTED)
    requested_by = Column(String, nullable=True)

    application = relationship("Application", back_populates="document_requests")
    uploads = relationship("DocumentUpload", back_populates="request", cascade="all, delete-orphan")


class DocumentUpload(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "document_uploads"

    request_id = Column(Uuid, ForeignKey("document_requests.id"), nullable=False)
    url = Column(String, nullable=False)
    status = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    request = relationship("DocumentRequest", back_populates="uploads")


class AuditLog(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "audit_logs"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=True)
    actor = Column(String, nullable=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Uuid, nullable=True)
    action = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)

    application = relationship("Application", back_populates="audit_logs")


class MatchRun(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "match_runs"

    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False)
    status = Column(String, nullable=False, default="running")
    check_results = Column(JSON, nullable=True)

    application = relationship("Application", back_populates="match_runs")
    results = relationship("MatchResult", back_populates="match_run", cascade="all, delete-orphan")


class MatchResult(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "match_results"

    match_run_id = Column(Uuid, ForeignKey("match_runs.id"), nullable=False)
    lender_program_id = Column(Uuid, ForeignKey("lender_programs.id", ondelete="SET NULL"), nullable=True)
    eligible = Column(Boolean, nullable=False, default=False)
    fit_score = Column(Integer, nullable=True)
    reasons = Column(String, nullable=True)
    criterion_results = Column(JSON, nullable=True)

    match_run = relationship("MatchRun", back_populates="results")

