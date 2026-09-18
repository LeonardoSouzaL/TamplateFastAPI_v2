from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from crud.crud_lastmile_os_driver_metrics import CRUDLastMileOsDriverMetrics
from schemas.lastmile_os_driver_schema import LastMileOsDriverFilters

NOW = datetime(2026, 9, 18, 15, 0, tzinfo=timezone.utc)


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()


def _filters(**kwargs) -> LastMileOsDriverFilters:
    values = dict(
        type_mode="ilike",
        type_values=[
            "LASTMILE_COLLECT",
            "LASTMILE_NORMAL",
            "LASTMILE_DESINSTAL%",
            "LASTMILE_RETIRADA%",
        ],
        now=NOW,
    )
    values.update(kwargs)
    return LastMileOsDriverFilters(**values)


def test_visao_default_usa_ilike_e_nao_delivery():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.aggregate_by_driver_stmt(_filters()))
    assert "ilike" in compiled
    assert "lastmile_collect" in compiled
    assert "lastmile_desinstal%" in compiled
    assert "lastmile_delivery" not in compiled


def test_agrega_por_driver_id_nao_client_nem_designation():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.aggregate_by_driver_stmt(_filters()))
    assert "group by" in compiled
    assert "driver_id" in compiled
    assert "group by service_order.client_id" not in compiled
    assert "group by service_order.designation_id" not in compiled


def test_viagem_atual_usa_distinct_on_order_id():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.aggregate_by_driver_stmt(_filters()))
    assert "distinct on" in compiled
    assert "order_id" in compiled


def test_sla_usa_created_at_estimated_deadline_e_fuso_sp():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.aggregate_by_driver_stmt(_filters()))
    assert "estimated_deadline" in compiled
    assert "america/sao_paulo" in compiled
    assert "created_at" in compiled
    assert "end_date" in compiled


def test_visao_filtra_created_at_da_os():
    crud = CRUDLastMileOsDriverMetrics()
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 18, tzinfo=timezone.utc)
    compiled = _compile(
        crud.aggregate_by_driver_stmt(_filters(data_inicial=inicio, data_final=fim))
    )
    assert "2026-09-01" in compiled
    assert "2026-09-18" in compiled


def test_filtro_driver_id_na_viagem_atual():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.aggregate_by_driver_stmt(_filters(driver_id=1588)))
    assert "driver_id" in compiled
    assert "1588" in compiled


def test_status_viagem_agrega_upper_type_por_tecnico():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.aggregate_travel_status_stmt(_filters()))
    assert "upper" in compiled
    assert "distinct on" in compiled
    assert "group by" in compiled
    assert "driver_id" in compiled
    assert "group by service_order.client_id" not in compiled
    assert "group by service_order.designation_id" not in compiled


def test_rota_do_dia_usa_route_date_e_fuso_sp():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(
        crud.list_drivers_with_route_today_stmt(_filters(), [1588, 2001])
    )
    assert "route_date" in compiled
    assert "america/sao_paulo" in compiled
    assert "1588" in compiled
    assert "is not null" in compiled


def test_lookup_auth_app_inclui_last_opening():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(crud.get_driver_profiles_stmt([1588]))
    assert "auth_app" in compiled
    assert "last_opening" in compiled
    assert "1588" in compiled
    assert "password" not in compiled


def test_csv_exato_usa_in():
    crud = CRUDLastMileOsDriverMetrics()
    compiled = _compile(
        crud.aggregate_by_driver_stmt(
            _filters(
                type_mode="in",
                type_values=["LASTMILE_COLLECT", "LASTMILE_NORMAL"],
            )
        )
    )
    assert " in (" in compiled
    assert "lastmile_collect" in compiled
    assert "ilike" not in compiled
