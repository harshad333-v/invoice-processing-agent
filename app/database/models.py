import os
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoice_agent.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class InvoiceRecord(Base):
    __tablename__ = "invoice_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_filename: Mapped[str] = mapped_column(String(255), default="invoice")
    source_sha256: Mapped[str] = mapped_column(String(64), default="", index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), default="", index=True)
    invoice_json: Mapped[str] = mapped_column(Text)
    issues_json: Mapped[str] = mapped_column(Text, default="[]")
    risk_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(40), default="needs_review", index=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    correction_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    audit_events: Mapped[list["AuditRecord"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class AuditRecord(Base):
    __tablename__ = "invoice_audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice_records.id"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    actor: Mapped[str] = mapped_column(String(120), default="system")
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    invoice: Mapped[InvoiceRecord] = relationship(back_populates="audit_events")


def init_db():
    Base.metadata.create_all(engine)
