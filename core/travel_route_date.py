"""Data efetiva da viagem: ``coalesce(route_date, created_at)``."""

from sqlalchemy import func

from models.order_travels_model import OrderTravel

TRAVEL_ROUTE_DATE_FILTER_FIELD = "_route_date_effective"


def travel_route_date_expression(model=None):
    target = model or OrderTravel
    return func.coalesce(target.route_date, target.created_at)
