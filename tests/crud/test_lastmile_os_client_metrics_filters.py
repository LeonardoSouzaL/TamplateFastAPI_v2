from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from crud.crud_lastmile_os_client_metrics import CRUDLastMileOsClientMetrics
from schemas.lastmile_os_client_schema import LastMileOsClientFilters

NOW = datetime(2026, 9, 18, 15, 0, tzinfo=timezone.utc)


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()


def _filters(**kwargs) -> LastMileOsClientFilters:
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
    return LastMileOsClientFilters(**values)


def test_visao_default_usa_ilike_e_nao_delivery():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_by_client_stmt(_filters()))
    assert "ilike" in compiled
    assert "lastmile_collect" in compiled
    assert "lastmile_desinstal%" in compiled
    assert "lastmile_delivery" not in compiled


def test_agrega_por_client_id_nao_designation():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_by_client_stmt(_filters()))
    assert "group by service_order.client_id" in compiled
    assert "group by service_order.designation_id" not in compiled


def test_viagem_atual_usa_distinct_on_order_id():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_by_client_stmt(_filters()))
    assert "distinct on" in compiled
    assert "order_id" in compiled


def test_sla_usa_created_at_estimated_deadline_e_fuso_sp():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_by_client_stmt(_filters()))
    assert "estimated_deadline" in compiled
    assert "america/sao_paulo" in compiled
    assert "created_at" in compiled
    assert "end_date" in compiled


def test_sem_tecnico_filtra_driver_id_nulo():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_by_client_stmt(_filters()))
    assert "driver_id" in compiled
    assert "is null" in compiled


def test_visao_filtra_created_at_da_os():
    crud = CRUDLastMileOsClientMetrics()
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 18, tzinfo=timezone.utc)
    compiled = _compile(
        crud.aggregate_by_client_stmt(_filters(data_inicial=inicio, data_final=fim))
    )
    assert "2026-09-01" in compiled
    assert "2026-09-18" in compiled


def test_filtro_cliente_id_na_visao():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_by_client_stmt(_filters(cliente_id=27)))
    assert "client_id" in compiled
    assert "27" in compiled


def test_status_viagem_agrega_upper_type_por_cliente():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(crud.aggregate_travel_status_stmt(_filters()))
    assert "upper" in compiled
    assert "distinct on" in compiled
    assert "group by service_order.client_id" in compiled
    assert "group by service_order.designation_id" not in compiled


def test_csv_exato_usa_in():
    crud = CRUDLastMileOsClientMetrics()
    compiled = _compile(
        crud.aggregate_by_client_stmt(
            _filters(
                type_mode="in",
                type_values=["LASTMILE_COLLECT", "LASTMILE_NORMAL"],
            )
        )
    )
    assert " in (" in compiled
    assert "lastmile_collect" in compiled
    assert "ilike" not in compiled
