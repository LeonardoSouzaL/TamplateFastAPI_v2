from sqlalchemy import Column, Integer, String

from db.base_class import Base


class OrderType(Base):
    """Mapeamento slim e somente leitura de ``order_types``."""

    __tablename__ = "order_types"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
