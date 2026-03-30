"""
SQLAlchemy ORM Models for Wallet Passes
Maps to the existing MariaDB schema defined in schema.sql
"""

from sqlalchemy import (
    create_engine, Column, String, Text, Integer, Enum, ForeignKey,
    Index, UniqueConstraint, TIMESTAMP, func, Boolean
)
from sqlalchemy.orm import (
    declarative_base, relationship, sessionmaker, Session
)
import configs
from datetime import datetime


# ---------------------------------------------------------------------------
# Engine & Session Factory
# ---------------------------------------------------------------------------

DATABASE_URL = (
    f"mysql+pymysql://{configs.DB_USER}:{configs.DB_PASSWORD}"
    f"@{configs.DB_HOST}:{configs.DB_PORT}/{configs.DB_NAME}"
    "?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

Base = declarative_base()


# ============================================================================
# Classes_Table  +  child tables
# ============================================================================

class ClassesTable(Base):
    __tablename__ = "Classes_Table"

    class_id = Column(String(255), primary_key=True)
    class_type = Column(String(100), nullable=False)
    issuer_name = Column(String(255))
    base_color = Column(String(50))
    logo_url = Column(Text)
    hero_image_url = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    # Relationships to child tables
    generic_fields = relationship(
        "GenericClassFields", uselist=False, back_populates="parent",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    event_ticket_fields = relationship(
        "EventTicketClassFields", uselist=False, back_populates="parent",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    loyalty_fields = relationship(
        "LoyaltyClassFields", uselist=False, back_populates="parent",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    transit_fields = relationship(
        "TransitClassFields", uselist=False, back_populates="parent",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    # Relationship to passes
    passes = relationship(
        "PassesTable", back_populates="parent_class",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class GenericClassFields(Base):
    __tablename__ = "GenericClass_Fields"

    class_id = Column(
        String(255), ForeignKey("Classes_Table.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    header = Column(String(255))
    card_title = Column(String(255))

    parent = relationship("ClassesTable", back_populates="generic_fields")

    text_module_rows = relationship(
        "GenericClassTextModuleRows", back_populates="parent_generic_fields",
        cascade="all, delete-orphan", passive_deletes=True,
        order_by="GenericClassTextModuleRows.row_index"
    )

class GenericClassTextModuleRows(Base):
    __tablename__ = "GenericClass_TextModuleRows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(
        String(255), ForeignKey("GenericClass_Fields.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False, index=True,
    )
    row_index = Column(Integer, nullable=False, default=0)
    left_header = Column(String(255), nullable=True)
    left_body = Column(Text, nullable=True)
    middle_header = Column(String(255), nullable=True)
    middle_body = Column(Text, nullable=True)
    right_header = Column(String(255), nullable=True)
    right_body = Column(Text, nullable=True)

    parent_generic_fields = relationship("GenericClassFields", back_populates="text_module_rows")


class EventTicketClassFields(Base):
    __tablename__ = "EventTicketClass_Fields"

    class_id = Column(
        String(255), ForeignKey("Classes_Table.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    event_name = Column(String(255))
    venue_name = Column(String(255))
    venue_address = Column(String(500))
    event_start = Column(String(50))

    parent = relationship("ClassesTable", back_populates="event_ticket_fields")


class LoyaltyClassFields(Base):
    __tablename__ = "LoyaltyClass_Fields"

    class_id = Column(
        String(255), ForeignKey("Classes_Table.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    program_name = Column(String(255))

    parent = relationship("ClassesTable", back_populates="loyalty_fields")


class TransitClassFields(Base):
    __tablename__ = "TransitClass_Fields"

    class_id = Column(
        String(255), ForeignKey("Classes_Table.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    transit_type = Column(String(100))
    transit_operator_name = Column(String(255))

    parent = relationship("ClassesTable", back_populates="transit_fields")


# ============================================================================
# Passes_Table  +  child tables
# ============================================================================

class PassesTable(Base):
    __tablename__ = "Passes_Table"

    object_id = Column(String(255), primary_key=True)
    class_id = Column(
        String(255), ForeignKey("Classes_Table.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    holder_name = Column(String(255), nullable=False)
    holder_email = Column(String(255), nullable=False)
    status = Column(Enum("Active", "Expired", name="pass_status"), nullable=False, default="Active")
    sync_status = Column(Enum("synced", "pending", "failed", name="sync_status"), default="pending")
    last_synced_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("class_id", "holder_email", name="unique_class_holder"),
        Index("idx_class_id", "class_id"),
        Index("idx_status", "status"),
        Index("idx_holder_email", "holder_email"),
        Index("idx_created_at", "created_at"),
    )

    # Relationships
    parent_class = relationship("ClassesTable", back_populates="passes")

    event_ticket_fields = relationship(
        "EventTicketFields", uselist=False, back_populates="parent_pass",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    generic_fields = relationship(
        "GenericFields", uselist=False, back_populates="parent_pass",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    text_modules = relationship(
        "PassTextModules", back_populates="parent_pass",
        cascade="all, delete-orphan", passive_deletes=True,
        order_by="PassTextModules.display_order",
    )
    messages = relationship(
        "PassMessages", back_populates="parent_pass",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class EventTicketFields(Base):
    __tablename__ = "EventTicket_Fields"

    object_id = Column(
        String(255), ForeignKey("Passes_Table.object_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    ticket_holder_name = Column(String(255))
    confirmation_code = Column(String(255))
    seat = Column(String(255))
    section = Column(String(255))
    gate = Column(String(255))

    parent_pass = relationship("PassesTable", back_populates="event_ticket_fields")


class GenericFields(Base):
    __tablename__ = "Generic_Fields"

    object_id = Column(
        String(255), ForeignKey("Passes_Table.object_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    header_value = Column(String(255))
    subheader_value = Column(String(255))
    card_title = Column(String(255), nullable=True)
    logo_url = Column(Text, nullable=True)
    hero_image_url = Column(Text, nullable=True)
    hex_background_color = Column(String(50), nullable=True)
    barcode_type = Column(String(100), nullable=True)
    barcode_value = Column(Text, nullable=True)

    parent_pass = relationship("PassesTable", back_populates="generic_fields")


class PassTextModules(Base):
    __tablename__ = "Pass_Text_Modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(
        String(255), ForeignKey("Passes_Table.object_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False, index=True,
    )
    module_id = Column(String(255))
    header = Column(String(255))
    body = Column(Text)
    display_order = Column(Integer, default=0)

    parent_pass = relationship("PassesTable", back_populates="text_modules")


class PassMessages(Base):
    __tablename__ = "Pass_Messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(
        String(255), ForeignKey("Passes_Table.object_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False, index=True,
    )
    message_id = Column(String(255))
    header = Column(String(255))
    body = Column(Text)
    message_type = Column(String(100))
    start_date = Column(String(100))
    end_date = Column(String(100))

    parent_pass = relationship("PassesTable", back_populates="messages")


# ============================================================================
# Notifications_Table
# ============================================================================

class NotificationsTable(Base):
    __tablename__ = "Notifications_Table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(String(255), index=True)
    object_id = Column(String(255), index=True)
    event_type = Column(
        Enum("class_update", "pass_update", "custom_message", name="event_type"),
        default="custom_message",
    )
    status = Column(Enum("Sent", "Failed", name="notif_status"), nullable=False)
    message = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.now, index=True)


# ============================================================================
# Apple Wallet Specific Tables
# ============================================================================

from sqlalchemy import JSON

class ApplePassesTable(Base):
    """Stores individual Apple Wallet Passes."""
    __tablename__ = "Apple_Passes_Table"

    serial_number = Column(String(255), primary_key=True)
    class_id = Column(String(255), index=True)
    pass_type_id = Column(String(255), nullable=False)
    
    holder_name = Column(String(255), nullable=False)
    holder_email = Column(String(255), nullable=False)
    
    status = Column(Enum("Active", "Expired", name="apple_pass_status"), nullable=False, default="Active")
    auth_token = Column(String(255), nullable=False) # Token used by Apple devices
    
    # Store the varied fields as JSON
    pass_data = Column(JSON, nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    visual_data = relationship("ApplePassDataTable", back_populates="pass_info", uselist=False, cascade="all, delete-orphan")


class ApplePassDataTable(Base):
    __tablename__ = "Apple_Pass_Data"

    serial_number = Column(String(255), ForeignKey("Apple_Passes_Table.serial_number", ondelete="CASCADE"), primary_key=True)

    background_color = Column(String(50))
    logo_url = Column(String(512))
    icon_url = Column(String(512))
    strip_url = Column(String(512))

    organization_name = Column(String(255))
    logo_text = Column(String(255))

    header_fields = Column(JSON, default=list)
    primary_fields = Column(JSON, default=list)
    secondary_fields = Column(JSON, default=list)
    auxiliary_fields = Column(JSON, default=list)
    back_fields = Column(JSON, default=list)

    pass_info = relationship("ApplePassesTable", back_populates="visual_data")


class AppleNotificationsTable(Base):
    """Stores push notification history for Apple Wallet passes."""
    __tablename__ = "Apple_Notifications_Table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pass_type_id = Column(String(255), index=True)
    serial_number = Column(String(255), index=True)
    status = Column(Enum("Sent", "Failed", name="apple_notif_status"), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now, index=True)


class AppleDeviceRegistrations(Base):
    """Tracks which Apple devices have registered to receive push updates
    for specific passes."""
    __tablename__ = "Apple_Device_Registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_library_id = Column(String(255), nullable=False, index=True)
    push_token = Column(String(255), nullable=False)
    serial_number = Column(String(255), nullable=False, index=True)
    pass_type_id = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("device_library_id", "serial_number", name="unique_device_pass"),
    )
