from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.lastmile_os_driver_service import (
    LastMileOsDriverService,
    compute_driver_idle,
)
from services.lastmile_os_status_service import resolve_type_filter

NOW = datetime(2026, 9, 18, 12, 8, tzinfo=timezone.utc)


def test_resolve_type_filter_default_nao_usa_delivery():
    mode, values = resolve_type_filter(None)
    assert mode == "ilike"
    assert "LASTMILE_DELIVERY" not in values


def test_ociosidade_53_min_vira_180_segundos():
    ocioso, segundos = compute_driver_idle(
        last_opening=NOW - timedelta(minutes=53),
        rota_atribuida=True,
        now=NOW,
        grace_minutes=50,
    )
    assert ocioso is True
    assert segundos == 180


def test_ociosidade_4_min_nao_conta():
    ocioso, segundos = compute_driver_idle(
        last_opening=NOW - timedelta(minutes=4),
        rota_atribuida=True,
        now=NOW,
        grace_minutes=50,
    )
    assert ocioso is False
    assert segundos == 0


def test_ociosidade_last_opening_nulo_nao_ocioso():
    ocioso, segundos = compute_driver_idle(
        last_opening=None,
        rota_atribuida=True,
        now=NOW,
        grace_minutes=50,
    )
    assert ocioso is False
    assert segundos == 0


def test_ociosidade_sem_rota_nao_ocioso():
    ocioso, segundos = compute_driver_idle(
        last_opening=NOW - timedelta(minutes=30),
        rota_atribuida=False,
        now=NOW,
        grace_minutes=50,
    )
    assert ocioso is False
    assert segundos == 0


def _row(
    driver_id,
    *,
    chamado: int = 1,
    atraso: int = 0,
    dentro: int = 0,
    sem_prazo: int = 0,
) -> dict:
    return {
        "driver_id": driver_id,
        "chamado_count": chamado,
        "atraso": atraso,
        "dentro_do_prazo": dentro,
        "sem_prazo": sem_prazo,
    }


def _profile(uid: int, **kwargs) -> dict:
    data = {
        "name": f"Tecnico {uid}",
        "cod_base": "SP01",
        "nome_unidade": "SAO PAULO",
        "last_opening": None,
    }
    data.update(kwargs)
    return data


async def _get_by_driver(
    rows,
    *,
    profiles=None,
    with_route=None,
    status_rows=None,
    **kwargs,
):
    service = LastMileOsDriverService()
    default_profiles = {}
    for row in rows:
        uid = row.get("driver_id")
        if uid is not None:
            default_profiles[uid] = _profile(uid)
    if profiles:
        default_profiles.update(profiles)
    with patch(
        "services.lastmile_os_driver_service.datetime"
    ) as mock_datetime, patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.aggregate_by_driver",
        new=AsyncMock(return_value=rows),
    ), patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.aggregate_travel_status_by_driver",
        new=AsyncMock(return_value=status_rows or []),
    ), patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.get_driver_profiles",
        new=AsyncMock(return_value=default_profiles),
    ), patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.list_drivers_with_route_today",
        new=AsyncMock(return_value=set(with_route or [])),
    ):
        mock_datetime.now.return_value = NOW
        return await service.get_by_driver(db=AsyncMock(), **kwargs)


@pytest.mark.asyncio
async def test_order_type_csv_vazio_nao_consulta_banco():
    service = LastMileOsDriverService()
    db = AsyncMock()
    with patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.aggregate_by_driver",
        new=AsyncMock(),
    ) as mock_agg, patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.aggregate_travel_status_by_driver",
        new=AsyncMock(),
    ) as mock_status, patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.get_driver_profiles",
        new=AsyncMock(),
    ) as mock_profiles, patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.list_drivers_with_route_today",
        new=AsyncMock(),
    ) as mock_route:
        result = await service.get_by_driver(db=db, order_type="")

    mock_agg.assert_not_awaited()
    mock_status.assert_not_awaited()
    mock_profiles.assert_not_awaited()
    mock_route.assert_not_awaited()
    assert result.total == 0
    assert result.sem_tecnico_count == 0
    assert result.items == []
    assert result.tecnico_ofensor is None
    assert result.ofensores == []
    assert result.melhor_tecnico is None
    assert result.melhores == []
    assert result.tecnico_ocioso is None
    assert result.ociosos == []


@pytest.mark.asyncio
async def test_mapeia_metricas_por_tecnico_e_status_viagem():
    result = await _get_by_driver(
        [
            _row(1588, chamado=5, atraso=1, dentro=3, sem_prazo=1),
            _row(2001, chamado=2, atraso=0, dentro=2),
        ],
        status_rows=[
            {"driver_id": 1588, "status": "PENDING", "quantity": 2},
            {"driver_id": 1588, "status": "ON ROUTE", "quantity": 1},
        ],
        with_route={1588},
        profiles={
            1588: _profile(1588, name="JOAO SILVA"),
            2001: _profile(2001, name="MARIA"),
        },
    )
    assert result.total == 7
    assert result.vision == "LASTMILE"
    assert result.sem_tecnico_count == 0
    assert [item.driver_uid for item in result.items] == [1588, 2001]
    first = result.items[0]
    assert first.tecnico == "JOAO SILVA"
    assert first.chamado_count == 5
    assert first.atraso_count == 1
    assert first.dentro_do_prazo_count == 3
    assert first.sem_prazo_count == 1
    assert first.chamado_count == (
        first.atraso_count + first.dentro_do_prazo_count + first.sem_prazo_count
    )
    assert [item.status for item in first.by_status_viagem] == ["PENDING", "ON ROUTE"]


@pytest.mark.asyncio
async def test_os_sem_tecnico_fora_de_items():
    result = await _get_by_driver(
        [
            _row(None, chamado=4, sem_prazo=4),
            _row(1588, chamado=3, atraso=1, dentro=2),
        ]
    )
    assert result.sem_tecnico_count == 4
    assert result.total == 7
    assert [item.driver_uid for item in result.items] == [1588]
    assert all(item.driver_uid is not None for item in result.items)


@pytest.mark.asyncio
async def test_tecnico_so_com_rota_e_zero_os_nao_aparece():
    result = await _get_by_driver(
        [_row(None, chamado=2, sem_prazo=2)],
        with_route={9999},
        profiles={9999: _profile(9999)},
    )
    assert result.items == []
    assert result.sem_tecnico_count == 2
    assert result.total == 2
    assert result.tecnico_ocioso is None


@pytest.mark.asyncio
async def test_sem_rota_hoje_nao_ocioso():
    result = await _get_by_driver(
        [_row(1588, chamado=3, dentro=3)],
        profiles={
            1588: _profile(1588, last_opening=NOW - timedelta(minutes=30)),
        },
        with_route=set(),
    )
    item = result.items[0]
    assert item.rota_atribuida is False
    assert item.ocioso is False
    assert item.ociosidade_segundos == 0


@pytest.mark.asyncio
async def test_last_opening_nulo_nao_ocioso():
    result = await _get_by_driver(
        [_row(1588, chamado=3, dentro=3)],
        profiles={1588: _profile(1588, last_opening=None)},
        with_route={1588},
    )
    item = result.items[0]
    assert item.rota_atribuida is True
    assert item.ocioso is False
    assert item.ociosidade_segundos == 0


@pytest.mark.asyncio
async def test_cinquenta_e_tres_minutos_parado_vira_180_segundos():
    result = await _get_by_driver(
        [_row(1588, chamado=3, dentro=3)],
        profiles={
            1588: _profile(1588, last_opening=NOW - timedelta(minutes=53)),
        },
        with_route={1588},
    )
    item = result.items[0]
    assert item.ocioso is True
    assert item.ociosidade_segundos == 180


@pytest.mark.asyncio
async def test_oito_minutos_parado_nao_ocioso():
    result = await _get_by_driver(
        [_row(1588, chamado=3, dentro=3)],
        profiles={
            1588: _profile(1588, last_opening=NOW - timedelta(minutes=8)),
        },
        with_route={1588},
    )
    item = result.items[0]
    assert item.ocioso is False
    assert item.ociosidade_segundos == 0


@pytest.mark.asyncio
async def test_quatro_minutos_parado_nao_ocioso():
    result = await _get_by_driver(
        [_row(1588, chamado=3, dentro=3)],
        profiles={
            1588: _profile(1588, last_opening=NOW - timedelta(minutes=4)),
        },
        with_route={1588},
    )
    item = result.items[0]
    assert item.ocioso is False
    assert item.ociosidade_segundos == 0


@pytest.mark.asyncio
async def test_encaminha_filtros_de_visao():
    service = LastMileOsDriverService()
    db = AsyncMock()
    captured = {}
    inicio = datetime(2026, 9, 1, tzinfo=timezone.utc)
    fim = datetime(2026, 9, 18, tzinfo=timezone.utc)

    async def fake_agg(*, db, filters):
        captured["filters"] = filters
        return []

    with patch(
        "services.lastmile_os_driver_service.datetime"
    ) as mock_datetime, patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.aggregate_by_driver",
        new=fake_agg,
    ), patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.aggregate_travel_status_by_driver",
        new=AsyncMock(return_value=[]),
    ), patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.get_driver_profiles",
        new=AsyncMock(return_value={}),
    ), patch(
        "services.lastmile_os_driver_service.crud_lastmile_os_driver_metrics.list_drivers_with_route_today",
        new=AsyncMock(return_value=set()),
    ):
        mock_datetime.now.return_value = NOW
        await service.get_by_driver(
            db=db,
            cliente_id=9,
            designation_id=24,
            driver_id=1588,
            data_inicial=inicio,
            data_final=fim,
        )

    assert captured["filters"].cliente_id == 9
    assert captured["filters"].designation_id == 24
    assert captured["filters"].driver_id == 1588
    assert captured["filters"].data_inicial == inicio
    assert captured["filters"].data_final == fim
    assert captured["filters"].type_mode == "ilike"
    assert "LASTMILE_DELIVERY" not in captured["filters"].type_values


@pytest.mark.asyncio
async def test_tecnico_ofensor_e_o_max_de_atraso_nao_o_total():
    result = await _get_by_driver(
        [
            _row(1, chamado=5, atraso=2, dentro=3),
            _row(2, chamado=8, atraso=5, dentro=1),
            _row(3, chamado=4, atraso=1, dentro=2),
        ]
    )
    assert result.tecnico_ofensor is not None
    assert result.tecnico_ofensor.driver_uid == 2
    assert result.tecnico_ofensor.atraso_count == 5
    assert result.tecnico_ofensor.atraso_count != sum(
        item.atraso_count for item in result.items
    )


@pytest.mark.asyncio
async def test_ofensores_top_10_corta_e_ignora_atraso_zero():
    rows = [_row(i, chamado=i, atraso=i, dentro=1) for i in range(0, 12)]
    result = await _get_by_driver(rows)
    assert [item.driver_uid for item in result.ofensores] == list(range(11, 1, -1))
    assert len(result.ofensores) == 10
    assert result.tecnico_ofensor is not None
    assert result.tecnico_ofensor.driver_uid == 11
    assert all(item.atraso_count > 0 for item in result.ofensores)


@pytest.mark.asyncio
async def test_melhor_tecnico_e_o_max_dentro_do_prazo():
    result = await _get_by_driver(
        [
            _row(1, chamado=5, atraso=2, dentro=3),
            _row(4, chamado=9, atraso=1, dentro=8),
            _row(2, chamado=4, atraso=1, dentro=2),
        ]
    )
    assert result.melhor_tecnico is not None
    assert result.melhor_tecnico.driver_uid == 4
    assert result.melhor_tecnico.dentro_do_prazo_count == 8
    assert [item.driver_uid for item in result.melhores] == [4, 1, 2]


@pytest.mark.asyncio
async def test_empate_de_ranking_usa_driver_uid_maior():
    result = await _get_by_driver(
        [
            _row(5, chamado=10, atraso=7, dentro=7),
            _row(8, chamado=10, atraso=7, dentro=7),
        ]
    )
    assert result.tecnico_ofensor is not None
    assert result.tecnico_ofensor.driver_uid == 8
    assert result.melhor_tecnico is not None
    assert result.melhor_tecnico.driver_uid == 8
    assert [item.driver_uid for item in result.ofensores] == [8, 5]
    assert [item.driver_uid for item in result.melhores] == [8, 5]


@pytest.mark.asyncio
async def test_zero_nao_entra_no_ranking():
    result = await _get_by_driver(
        [
            _row(1, chamado=4, atraso=0, dentro=4),
            _row(2, chamado=3, atraso=3, dentro=0),
        ]
    )
    assert [item.driver_uid for item in result.ofensores] == [2]
    assert [item.driver_uid for item in result.melhores] == [1]


@pytest.mark.asyncio
async def test_filtro_driver_id_ranking_com_no_maximo_um_item():
    result = await _get_by_driver(
        [_row(1588, chamado=12, atraso=5, dentro=7)],
        with_route={1588},
        profiles={
            1588: _profile(
                1588,
                last_opening=NOW - timedelta(minutes=53),
            )
        },
    )
    assert len(result.items) == 1
    assert result.items[0].driver_uid == 1588
    assert len(result.ofensores) == 1
    assert len(result.melhores) == 1
    assert result.tecnico_ofensor is not None
    assert result.tecnico_ofensor.driver_uid == 1588
    assert result.melhor_tecnico is not None
    assert result.melhor_tecnico.driver_uid == 1588
    assert result.tecnico_ocioso is not None
    assert result.tecnico_ocioso.driver_uid == 1588
    assert len(result.ociosos) == 1


@pytest.mark.asyncio
async def test_ranking_ociosos_top_e_empate_uid():
    result = await _get_by_driver(
        [
            _row(10, chamado=1, dentro=1),
            _row(20, chamado=1, dentro=1),
            _row(30, chamado=1, dentro=1),
        ],
        with_route={10, 20, 30},
        profiles={
            10: _profile(10, last_opening=NOW - timedelta(minutes=65)),
            20: _profile(20, last_opening=NOW - timedelta(minutes=65)),
            30: _profile(30, last_opening=NOW - timedelta(minutes=53)),
        },
    )
    assert result.tecnico_ocioso is not None
    assert result.tecnico_ocioso.driver_uid == 20
    assert [item.driver_uid for item in result.ociosos] == [20, 10, 30]
    assert result.ociosos[0].ociosidade_segundos == 900
    assert result.ociosos[2].ociosidade_segundos == 180
