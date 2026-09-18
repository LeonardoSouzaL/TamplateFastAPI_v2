from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.lastmile_os_client_service import LastMileOsClientService
from services.lastmile_os_status_service import resolve_type_filter


def test_resolve_type_filter_default_nao_usa_delivery():
    mode, values = resolve_type_filter(None)
    assert mode == "ilike"
    assert "LASTMILE_DELIVERY" not in values


@pytest.mark.asyncio
async def test_order_type_csv_vazio_nao_consulta_banco():
    service = LastMileOsClientService()
    db = AsyncMock()
    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(),
    ) as mock_client, patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(),
    ) as mock_status, patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(),
    ) as mock_names:
        result = await service.get_by_client(db=db, order_type="")

    mock_client.assert_not_awaited()
    mock_status.assert_not_awaited()
    mock_names.assert_not_awaited()
    assert result.total == 0
    assert result.items == []
    assert result.cliente_ofensor is None
    assert result.ofensores == []
    assert result.melhor_cliente is None
    assert result.melhores == []


@pytest.mark.asyncio
async def test_mapeia_metricas_por_cliente_e_status_viagem():
    service = LastMileOsClientService()
    db = AsyncMock()
    rows = [
        {
            "client_id": 27,
            "chamado_count": 5,
            "sem_tecnico": 2,
            "atraso": 1,
            "dentro_do_prazo": 3,
            "sem_prazo": 1,
        },
        {
            "client_id": 10,
            "chamado_count": 2,
            "sem_tecnico": 0,
            "atraso": 0,
            "dentro_do_prazo": 2,
            "sem_prazo": 0,
        },
    ]
    status_rows = [
        {"client_id": 27, "status": "PENDING", "quantity": 2},
        {"client_id": 27, "status": "ON ROUTE", "quantity": 1},
    ]

    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=status_rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={27: "CIELO", 10: "OUTRO"}),
    ):
        result = await service.get_by_client(db=db)

    assert result.total == 7
    assert result.vision == "LASTMILE"
    assert [item.client_id for item in result.items] == [27, 10]
    first = result.items[0]
    assert first.cliente == "CIELO"
    assert first.chamado_count == 5
    assert first.sem_tecnico_count == 2
    assert first.atraso_count == 1
    assert first.dentro_do_prazo_count == 3
    assert first.sem_prazo_count == 1
    assert first.chamado_count == (
        first.atraso_count + first.dentro_do_prazo_count + first.sem_prazo_count
    )
    assert [item.status for item in first.by_status_viagem] == ["PENDING", "ON ROUTE"]


@pytest.mark.asyncio
async def test_sem_viagem_conta_sem_tecnico():
    service = LastMileOsClientService()
    db = AsyncMock()
    rows = [
        {
            "client_id": 27,
            "chamado_count": 4,
            "sem_tecnico": 4,
            "atraso": 0,
            "dentro_do_prazo": 0,
            "sem_prazo": 4,
        }
    ]
    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={27: "CIELO"}),
    ):
        result = await service.get_by_client(db=db)

    item = result.items[0]
    assert item.sem_tecnico_count == 4
    assert item.by_status_viagem == []


@pytest.mark.asyncio
async def test_driver_preenchido_nao_entra_em_sem_tecnico():
    service = LastMileOsClientService()
    db = AsyncMock()
    rows = [
        {
            "client_id": 27,
            "chamado_count": 3,
            "sem_tecnico": 0,
            "atraso": 1,
            "dentro_do_prazo": 2,
            "sem_prazo": 0,
        }
    ]
    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={27: "CIELO"}),
    ):
        result = await service.get_by_client(db=db)

    assert result.items[0].sem_tecnico_count == 0


@pytest.mark.asyncio
async def test_prazo_zero_entra_em_sem_prazo():
    service = LastMileOsClientService()
    db = AsyncMock()
    rows = [
        {
            "client_id": 27,
            "chamado_count": 2,
            "sem_tecnico": 0,
            "atraso": 0,
            "dentro_do_prazo": 0,
            "sem_prazo": 2,
        }
    ]
    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={27: "CIELO"}),
    ):
        result = await service.get_by_client(db=db)

    item = result.items[0]
    assert item.sem_prazo_count == 2
    assert item.atraso_count == 0
    assert item.dentro_do_prazo_count == 0


@pytest.mark.asyncio
async def test_aberto_vencido_atraso_e_atendido_no_limite_no_prazo():
    service = LastMileOsClientService()
    db = AsyncMock()
    rows = [
        {
            "client_id": 27,
            "chamado_count": 2,
            "sem_tecnico": 0,
            "atraso": 1,
            "dentro_do_prazo": 1,
            "sem_prazo": 0,
        }
    ]
    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={27: "CIELO"}),
    ):
        result = await service.get_by_client(db=db)

    item = result.items[0]
    assert item.atraso_count == 1
    assert item.dentro_do_prazo_count == 1
    assert item.chamado_count == (
        item.atraso_count + item.dentro_do_prazo_count + item.sem_prazo_count
    )


@pytest.mark.asyncio
async def test_encaminha_filtros_de_visao():
    service = LastMileOsClientService()
    db = AsyncMock()
    captured = {}
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 18, tzinfo=timezone.utc)

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=fake_agg,
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value={}),
    ):
        await service.get_by_client(
            db=db,
            cliente_id=9,
            designation_id=24,
            data_inicial=inicio,
            data_final=fim,
        )

    assert captured["filters"].cliente_id == 9
    assert captured["filters"].designation_id == 24
    assert captured["filters"].data_inicial == inicio
    assert captured["filters"].data_final == fim
    assert captured["filters"].type_mode == "ilike"
    assert "LASTMILE_DELIVERY" not in captured["filters"].type_values


def _row(
    client_id: int,
    *,
    chamado: int = 1,
    atraso: int = 0,
    dentro: int = 0,
    sem_tecnico: int = 0,
    sem_prazo: int = 0,
) -> dict:
    return {
        "client_id": client_id,
        "chamado_count": chamado,
        "sem_tecnico": sem_tecnico,
        "atraso": atraso,
        "dentro_do_prazo": dentro,
        "sem_prazo": sem_prazo,
    }


async def _get_by_client(rows):
    service = LastMileOsClientService()
    names = {row["client_id"]: f"Cliente {row['client_id']}" for row in rows}
    with patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_by_client",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_os_client_metrics.aggregate_travel_status_by_client",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_client_service.crud_lastmile_metrics.get_location_names",
        new=AsyncMock(return_value=names),
    ):
        return await service.get_by_client(db=AsyncMock())


@pytest.mark.asyncio
async def test_cliente_ofensor_e_o_max_de_atraso_nao_o_total():
    result = await _get_by_client(
        [
            _row(1, chamado=5, atraso=2, dentro=3),
            _row(2, chamado=8, atraso=5, dentro=1),
            _row(3, chamado=4, atraso=1, dentro=2),
        ]
    )
    assert result.cliente_ofensor is not None
    assert result.cliente_ofensor.client_id == 2
    assert result.cliente_ofensor.atraso_count == 5
    assert result.cliente_ofensor.atraso_count != sum(
        item.atraso_count for item in result.items
    )


@pytest.mark.asyncio
async def test_ofensores_top_10_corta_e_ignora_atraso_zero():
    rows = [_row(i, chamado=i, atraso=i, dentro=1) for i in range(0, 12)]
    result = await _get_by_client(rows)
    assert [item.client_id for item in result.ofensores] == list(range(11, 1, -1))
    assert len(result.ofensores) == 10
    assert result.cliente_ofensor is not None
    assert result.cliente_ofensor.client_id == 11
    assert all(item.atraso_count > 0 for item in result.ofensores)


@pytest.mark.asyncio
async def test_melhor_cliente_e_o_max_dentro_do_prazo():
    result = await _get_by_client(
        [
            _row(1, chamado=5, atraso=2, dentro=3),
            _row(4, chamado=9, atraso=1, dentro=8),
            _row(2, chamado=4, atraso=1, dentro=2),
        ]
    )
    assert result.melhor_cliente is not None
    assert result.melhor_cliente.client_id == 4
    assert result.melhor_cliente.dentro_do_prazo_count == 8
    assert [item.client_id for item in result.melhores] == [4, 1, 2]


@pytest.mark.asyncio
async def test_empate_de_ranking_usa_client_id_maior():
    result = await _get_by_client(
        [
            _row(5, chamado=10, atraso=7, dentro=7),
            _row(8, chamado=10, atraso=7, dentro=7),
        ]
    )
    assert result.cliente_ofensor is not None
    assert result.cliente_ofensor.client_id == 8
    assert result.melhor_cliente is not None
    assert result.melhor_cliente.client_id == 8
    assert [item.client_id for item in result.ofensores] == [8, 5]
    assert [item.client_id for item in result.melhores] == [8, 5]


@pytest.mark.asyncio
async def test_zero_nao_entra_no_ranking():
    result = await _get_by_client(
        [
            _row(1, chamado=4, atraso=0, dentro=4),
            _row(2, chamado=3, atraso=3, dentro=0),
        ]
    )
    assert [item.client_id for item in result.ofensores] == [2]
    assert [item.client_id for item in result.melhores] == [1]
    assert result.cliente_ofensor is not None
    assert result.cliente_ofensor.client_id == 2
    assert result.melhor_cliente is not None
    assert result.melhor_cliente.client_id == 1


@pytest.mark.asyncio
async def test_filtro_cliente_id_ranking_com_no_maximo_um_item():
    result = await _get_by_client(
        [_row(27, chamado=12, atraso=5, dentro=7)],
    )
    assert len(result.items) == 1
    assert result.items[0].client_id == 27
    assert len(result.ofensores) == 1
    assert len(result.melhores) == 1
    assert result.cliente_ofensor is not None
    assert result.cliente_ofensor.client_id == 27
    assert result.melhor_cliente is not None
    assert result.melhor_cliente.client_id == 27
