from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, JSON, Uuid
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class Lender(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "lenders"

    name = Column(String, nullable=False, unique=True)
    programs = relationship("LenderProgram", back_populates="lender", cascade="all, delete-orphan")
    versions = relationship("PolicyVersion", back_populates="lender", cascade="all, delete-orphan")


class LenderProgram(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "lender_programs"

    lender_id = Column(Uuid, ForeignKey("lenders.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # Term configuration (in months)
    term_min = Column(Integer, nullable=True)  # Minimum term offered
    term_max = Column(Integer, nullable=True)  # Maximum term offered
    term_default = Column(Integer, nullable=True)  # Default term for new equipment
    term_used_equipment = Column(Integer, nullable=True)  # Term for used/older equipment
    # Interest rate configuration (as percentage, e.g., 8.5 = 8.5%)
    interest_rate_min = Column(Numeric(5, 2), nullable=True)  # Minimum interest rate
    interest_rate_max = Column(Numeric(5, 2), nullable=True)  # Maximum interest rate
    interest_rate_default = Column(Numeric(5, 2), nullable=True)  # Default interest rate

    lender = relationship("Lender", back_populates="programs")
    criteria = relationship("LenderCriteria", back_populates="program", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", backref="lender_program")


class LenderCriteria(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "lender_criteria"

    program_id = Column(Uuid, ForeignKey("lender_programs.id"), nullable=False)
    field_key = Column(String, nullable=False)
    data_type = Column(String, nullable=False)  # int, decimal, string, bool
    operator = Column(String, nullable=False)  # range, in, not_in, contains, boolean
    value_min = Column(String, nullable=True)
    value_max = Column(String, nullable=True)
    values = Column(JSON, nullable=True)
    pattern = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    program = relationship("LenderProgram", back_populates="criteria")


class PolicyVersion(TimestampMixin, UUIDMixin, Base):
    __tablename__ = "policy_versions"

    lender_id = Column(Uuid, ForeignKey("lenders.id"), nullable=False)
    version = Column(String, nullable=False)
    effective_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    lender = relationship("Lender", back_populates="versions")

