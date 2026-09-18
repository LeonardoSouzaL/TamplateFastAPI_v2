from sqlalchemy import Column, DateTime, Integer, String

from db.base_class import Base


class AuthApp(Base):
    """Mapeamento slim e somente leitura de ``auth_app``.

    ``order_travels.driver_id`` aponta para ``uid``. Sem senha, e-mail ou
    demais colunas operacionais. ``last_opening`` alimenta a ociosidade.
    """

    __tablename__ = "auth_app"

    id = Column(Integer, primary_key=True)
    uid = Column(Integer, unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    cod_base = Column(String(50), nullable=True)
    nome_unidade = Column(String(150), nullable=True)
    last_opening = Column(DateTime(timezone=True), nullable=True)
