from datetime import datetime
from typing import Tuple

from sqlalchemy import Date, and_, cast, func, or_, select
from sqlalchemy.sql import ColumnElement

from models.order_travels_model import OrderTravel
from models.service_order_model import ServiceOrder
from models.transport_quotes_model import TransportQuote

APP_TZ = "America/Sao_Paulo"


def latest_travel_subquery():
    """Viagem atual da OS: maior ``order_travels.id`` por ``order_id``."""
    return (
        select(
            OrderTravel.order_id.label("order_id"),
            OrderTravel.driver_id.label("driver_id"),
            OrderTravel.status_id.label("status_id"),
            OrderTravel.end_date.label("end_date"),
            OrderTravel.quote_id.label("quote_id"),
        )
        .distinct(OrderTravel.order_id)
        .order_by(OrderTravel.order_id, OrderTravel.id.desc())
        .subquery("latest_travel")
    )


def sp_date(column) -> ColumnElement:
    return cast(func.timezone(APP_TZ, column), Date)


def sla_expressions(
    latest_travel,
    now: datetime,
) -> Tuple[ColumnElement, ColumnElement, ColumnElement]:
    """Atraso, dentro do prazo e sem prazo (mesmo recorte do by-pa)."""
    deadline_date = sp_date(ServiceOrder.created_at) + TransportQuote.estimated_deadline
    end_date = sp_date(latest_travel.c.end_date)
    today = sp_date(now)
    has_prazo = and_(
        TransportQuote.estimated_deadline.is_not(None),
        TransportQuote.estimated_deadline > 0,
    )
    atraso = and_(
        has_prazo,
        or_(
            and_(
                latest_travel.c.end_date.is_not(None),
                end_date > deadline_date,
            ),
            and_(
                latest_travel.c.end_date.is_(None),
                today > deadline_date,
            ),
        ),
    )
    dentro_do_prazo = and_(
        has_prazo,
        or_(
            and_(
                latest_travel.c.end_date.is_not(None),
                end_date <= deadline_date,
            ),
            and_(
                latest_travel.c.end_date.is_(None),
                today <= deadline_date,
            ),
        ),
    )
    sem_prazo = or_(
        TransportQuote.id.is_(None),
        TransportQuote.estimated_deadline.is_(None),
        TransportQuote.estimated_deadline == 0,
    )
    return atraso, dentro_do_prazo, sem_prazo


def atendida_no_prazo_expression(latest_travel) -> ColumnElement:
    """Atendida no prazo: ``end_date`` preenchido, há prazo e atendimento no limite.

    Não reutiliza ``dentro_do_prazo`` de ``sla_expressions`` (esse inclui
    aberto ainda no prazo).
    """
    deadline_date = sp_date(ServiceOrder.created_at) + TransportQuote.estimated_deadline
    end_date = sp_date(latest_travel.c.end_date)
    has_prazo = and_(
        TransportQuote.estimated_deadline.is_not(None),
        TransportQuote.estimated_deadline > 0,
    )
    return and_(
        has_prazo,
        latest_travel.c.end_date.is_not(None),
        end_date <= deadline_date,
    )
