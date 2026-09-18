from sqlalchemy import Boolean, Column, Integer, String

from db.base_class import Base


class EquipamentStatus(Base):
    """Mapeamento slim e somente leitura de ``status_equipament``."""

    __tablename__ = "status_equipament"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    description = Column(String)
    finished = Column(Boolean, default=False)
