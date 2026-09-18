from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func

from db.base_class import Base


class ServiceOrder(Base):
    """Mapeamento slim e somente leitura de ``service_order``."""

    __tablename__ = "service_order"

    id = Column(Integer, primary_key=True)
    order_type_id = Column(Integer, ForeignKey("order_types.id"))
    order_state_id = Column(Integer, ForeignKey("status_equipament.id"))
    client_id = Column(Integer, ForeignKey("logistica_groupaditionalinformation.id"))
    designation_id = Column(Integer, ForeignKey("logistica_groupaditionalinformation.id"))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
