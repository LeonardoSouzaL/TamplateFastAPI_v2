from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.lastmile_os_overview_service import LastMileOsOverviewService
from services.lastmile_os_status_service import resolve_type_filter


def test_resolve_type_filter_default_nao_usa_delivery():
    mode, values = resolve_type_filter(None)
    assert mode == "ilike"
    assert "LASTMILE_DELIVERY" not in values


@pytest.mark.asyncio
async def test_order_type_csv_vazio_nao_consulta_banco():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(),
    ) as mock_overview:
        result = await service.get_overview(db=db, order_type="")

    mock_overview.assert_not_awaited()
    assert result.total == 0
    assert result.pendente_count == 0
    assert result.atendida_count == 0
    assert result.atendida_no_prazo_percent == 0.0
    assert result.fora_do_prazo_percent == 0.0
    assert result.efetividade_percent == 0.0


@pytest.mark.asyncio
async def test_mapeia_totais_e_calcula_percentuais():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    row = {
        "total": 200,
        "pendente": 50,
        "atendida": 150,
        "atendida_no_prazo": 120,
        "atraso": 40,
        "sem_tecnico": 15,
    }
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(return_value=row),
    ):
        result = await service.get_overview(db=db)

    assert result.vision == "LASTMILE"
    assert result.total == 200
    assert result.pendente_count == 50
    assert result.atendida_count == 150
    assert result.pendente_count + result.atendida_count == result.total
    assert result.atendida_no_prazo_count == 120
    assert result.fora_do_prazo_count == 40
    assert result.sem_tecnico_count == 15
    assert result.atendida_no_prazo_percent == 60.0
    assert result.fora_do_prazo_percent == 20.0
    assert result.efetividade_percent == 75.0


@pytest.mark.asyncio
async def test_total_zero_percentuais_zero():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    row = {
        "total": 0,
        "pendente": 0,
        "atendida": 0,
        "atendida_no_prazo": 0,
        "atraso": 0,
        "sem_tecnico": 0,
    }
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(return_value=row),
    ):
        result = await service.get_overview(db=db)

    assert result.atendida_no_prazo_percent == 0.0
    assert result.fora_do_prazo_percent == 0.0
    assert result.efetividade_percent == 0.0


@pytest.mark.asyncio
async def test_sem_viagem_conta_pendente_e_sem_tecnico():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    row = {
        "total": 4,
        "pendente": 4,
        "atendida": 0,
        "atendida_no_prazo": 0,
        "atraso": 0,
        "sem_tecnico": 4,
    }
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(return_value=row),
    ):
        result = await service.get_overview(db=db)

    assert result.pendente_count == 4
    assert result.atendida_count == 0
    assert result.sem_tecnico_count == 4
    assert result.pendente_count + result.atendida_count == result.total


@pytest.mark.asyncio
async def test_driver_preenchido_nao_entra_em_sem_tecnico():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    row = {
        "total": 3,
        "pendente": 1,
        "atendida": 2,
        "atendida_no_prazo": 2,
        "atraso": 0,
        "sem_tecnico": 0,
    }
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(return_value=row),
    ):
        result = await service.get_overview(db=db)

    assert result.sem_tecnico_count == 0


@pytest.mark.asyncio
async def test_aberto_vencido_e_fora_do_prazo_nao_e_atendida_no_prazo():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    row = {
        "total": 1,
        "pendente": 1,
        "atendida": 0,
        "atendida_no_prazo": 0,
        "atraso": 1,
        "sem_tecnico": 0,
    }
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(return_value=row),
    ):
        result = await service.get_overview(db=db)

    assert result.pendente_count == 1
    assert result.fora_do_prazo_count == 1
    assert result.atendida_no_prazo_count == 0
    assert result.atendida_count == 0


@pytest.mark.asyncio
async def test_atendido_no_limite_entra_no_prazo_aberto_no_prazo_so_pendente():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    row = {
        "total": 2,
        "pendente": 1,
        "atendida": 1,
        "atendida_no_prazo": 1,
        "atraso": 0,
        "sem_tecnico": 0,
    }
    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=AsyncMock(return_value=row),
    ):
        result = await service.get_overview(db=db)

    assert result.atendida_no_prazo_count == 1
    assert result.pendente_count == 1
    assert result.fora_do_prazo_count == 0
    assert result.pendente_count + result.atendida_count == result.total


@pytest.mark.asyncio
async def test_encaminha_filtros_de_visao():
    service = LastMileOsOverviewService()
    db = AsyncMock()
    captured = {}
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 18, tzinfo=timezone.utc)

    async def _capture(*, db, filters):
        captured["filters"] = filters
        return {
            "total": 0,
            "pendente": 0,
            "atendida": 0,
            "atendida_no_prazo": 0,
            "atraso": 0,
            "sem_tecnico": 0,
        }

    with patch(
        "services.lastmile_os_overview_service.crud_lastmile_os_overview_metrics.aggregate_overview",
        new=_capture,
    ):
        await service.get_overview(
            db=db,
            cliente_id=9,
            designation_id=24,
            data_inicial=inicio,
            data_final=fim,
        )

    filters = captured["filters"]
    assert filters.cliente_id == 9
    assert filters.designation_id == 24
    assert filters.data_inicial == inicio
    assert filters.data_final == fim
