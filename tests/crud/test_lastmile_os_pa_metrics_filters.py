from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from crud.crud_lastmile_os_pa_metrics import CRUDLastMileOsPaMetrics
from schemas.lastmile_os_pa_schema import LastMileOsPaFilters

NOW = datetime(2026, 9, 17, 15, 0, tzinfo=timezone.utc)


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()


def _filters(**kwargs) -> LastMileOsPaFilters:
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
    return LastMileOsPaFilters(**values)


def test_visao_default_usa_ilike_e_nao_delivery():
    crud = CRUDLastMileOsPaMetrics()
    compiled = _compile(crud.aggregate_by_pa_stmt(_filters()))
    assert "ilike" in compiled
    assert "lastmile_collect" in compiled
    assert "lastmile_desinstal%" in compiled
    assert "lastmile_delivery" not in compiled


def test_viagem_atual_usa_distinct_on_order_id():
    crud = CRUDLastMileOsPaMetrics()
    compiled = _compile(crud.aggregate_by_pa_stmt(_filters()))
    assert "distinct on" in compiled
    assert "order_id" in compiled


def test_sla_usa_created_at_estimated_deadline_e_fuso_sp():
    crud = CRUDLastMileOsPaMetrics()
    compiled = _compile(crud.aggregate_by_pa_stmt(_filters()))
    assert "estimated_deadline" in compiled
    assert "america/sao_paulo" in compiled
    assert "created_at" in compiled
    assert "end_date" in compiled


def test_sem_tecnico_filtra_driver_id_nulo():
    crud = CRUDLastMileOsPaMetrics()
    compiled = _compile(crud.aggregate_by_pa_stmt(_filters()))
    assert "driver_id" in compiled
    assert "is null" in compiled


def test_visao_filtra_created_at_da_os():
    crud = CRUDLastMileOsPaMetrics()
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 17, tzinfo=timezone.utc)
    compiled = _compile(
        crud.aggregate_by_pa_stmt(_filters(data_inicial=inicio, data_final=fim))
    )
    assert "2026-09-01" in compiled
    assert "2026-09-17" in compiled


def test_status_viagem_agrega_upper_type():
    crud = CRUDLastMileOsPaMetrics()
    compiled = _compile(crud.aggregate_travel_status_stmt(_filters()))
    assert "upper" in compiled
    assert "distinct on" in compiled
    assert "group by" in compiled


def test_csv_exato_usa_in():
    crud = CRUDLastMileOsPaMetrics()
    compiled = _compile(
        crud.aggregate_by_pa_stmt(
            _filters(
                type_mode="in",
                type_values=["LASTMILE_COLLECT", "LASTMILE_NORMAL"],
            )
        )
    )
    assert " in (" in compiled
    assert "lastmile_collect" in compiled
    assert "ilike" not in compiled
