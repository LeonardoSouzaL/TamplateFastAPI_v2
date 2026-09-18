from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func

from db.base_class import Base


class OrderTravel(Base):
    """Mapeamento slim e somente leitura de ``order_travels``.

    Sem relacionamentos eager e sem hybrid ``atrasado`` (atraso do dashboard
    v2 usa ``end_date < agora``).
    """

    __tablename__ = "order_travels"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("service_order.id"))
    driver_id = Column(Integer, nullable=True)
    carrier_id = Column(Integer, ForeignKey("logistica_groupaditionalinformation.id"))
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status_id = Column(Integer, ForeignKey("status_equipament.id"))
    designation_id = Column(Integer, ForeignKey("logistica_groupaditionalinformation.id"))
    quote_id = Column(Integer, ForeignKey("transport_quotes.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    route_date = Column(DateTime(timezone=True), nullable=True)
