from sqlalchemy import Column, Integer, String

from db.base_class import Base


class AranciaLocation(Base):
    """Mapeamento slim e somente leitura de ``logistica_groupaditionalinformation``."""

    __tablename__ = "logistica_groupaditionalinformation"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=True)
    group_id = Column(Integer, nullable=True)
