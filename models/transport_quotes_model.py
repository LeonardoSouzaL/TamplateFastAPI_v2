from sqlalchemy import Column, ForeignKey, Integer

from db.base_class import Base


class TransportQuote(Base):
    """Mapeamento slim e somente leitura de ``transport_quotes``."""

    __tablename__ = "transport_quotes"

    id = Column(Integer, primary_key=True)
    service_order_id = Column(Integer, ForeignKey("service_order.id"))
    estimated_deadline = Column(Integer, nullable=True)
