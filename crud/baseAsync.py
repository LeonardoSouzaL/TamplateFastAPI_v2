import logging
from typing import Any, Dict, Generic, Iterable, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from asyncpg.exceptions import UniqueViolationError
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, asc, cast, desc, false, func, not_, or_, select, true
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.types import Numeric

from db.base_class import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD abstrato assíncrono para modelos SQLAlchemy.

    Recursos consolidados:
    - CRUD básico: get, create, update, remove.
    - Consultas com filtros simples e múltiplos.
    - Filtros agrupados com AND / OR / NOT.
    - Suporte a relacionamento usando campo pontilhado: ``cliente.nome``.
    - Suporte a JSON/JSONB usando campo pontilhado: ``extra_information.chave.subchave``.
    - Ordenação dinâmica, paginação, distinct por id e desempate por id.
    - Agregações: sum, count, avg, min, max.
    - Commit com tratamento de IntegrityError/UniqueViolationError.

    Exemplo de uso:
        crud_order = CRUDBase(ServiceOrder)

        obj = await crud_order.get(db, id=1)

        orders = await crud_order.get_multi_filters(
            db,
            filters=[
                {"field": "status", "operator": "=", "value": "PENDENTE"},
                {"field": "cliente.nome", "operator": "ilike", "value": "CIELO"},
            ],
            order_by="id",
            order_desc=True,
            limit=100,
        )
    """

    _OP = {
        "=": lambda f, v: f == v,
        "==": lambda f, v: f == v,
        "!=": lambda f, v: f != v,
        "<": lambda f, v: f < v,
        "<=": lambda f, v: f <= v,
        ">": lambda f, v: f > v,
        ">=": lambda f, v: f >= v,
        "like": lambda f, v: f.like(v),
        "not_like": lambda f, v: ~f.like(v),
        "ilike": lambda f, v: f.ilike(v),
        "not_ilike": lambda f, v: ~f.ilike(v),
        "contains": lambda f, v: f.contains(v),
        "startswith": lambda f, v: f.startswith(v),
        "endswith": lambda f, v: f.endswith(v),
        "in": lambda f, v: f.in_(v),
        "notin": lambda f, v: ~f.in_(v),
        "between": lambda f, v: f.between(v[0], v[1]),
        "not_between": lambda f, v: ~f.between(v[0], v[1]),
        "is_null": lambda f, _: f.is_(None),
        "is_not_null": lambda f, _: f.is_not(None),
        "is_true": lambda f, _: f.is_(True),
        "is_false": lambda f, _: f.is_(False),
    }

    _AGG_OP = {
        "sum": func.sum,
        "count": func.count,
        "avg": func.avg,
        "min": func.min,
        "max": func.max,
    }

    def __init__(self, model: Type[ModelType]):
        """
        Inicializa o CRUD para um model SQLAlchemy.

        Exemplo:
            crud_service_order = CRUDBase(ServiceOrder)
        """
        self.model = model

    # ---------------------------------------------------------------------
    # Helpers internos
    # ---------------------------------------------------------------------

    @staticmethod
    def _schema_to_dict(
        obj_in: Union[BaseModel, Dict[str, Any]],
        *,
        exclude_unset: bool = False,
    ) -> Dict[str, Any]:
        """
        Converte Pydantic v2, Pydantic v1 ou dict para dict Python.

        Exemplo:
            data = self._schema_to_dict(payload, exclude_unset=True)
        """
        if isinstance(obj_in, dict):
            return obj_in

        if hasattr(obj_in, "model_dump"):
            return obj_in.model_dump(exclude_unset=exclude_unset)

        if hasattr(obj_in, "dict"):
            return obj_in.dict(exclude_unset=exclude_unset)

        raise TypeError("obj_in deve ser um dict ou um schema Pydantic.")

    async def _commit_with_retry(
        self,
        db: AsyncSession,
        *,
        max_retries: int = 1,
    ) -> None:
        """
        Executa commit com tratamento para IntegrityError.

        Observação:
            Retry em violação UNIQUE só faz sentido em cenários bem específicos,
            como geração concorrente de códigos únicos. Caso o mesmo objeto continue
            violando a constraint, o erro será relançado.

        Exemplo:
            db.add(db_obj)
            await self._commit_with_retry(db, max_retries=3)
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                await db.commit()
                return
            except IntegrityError as exc:
                await db.rollback()
                last_error = exc

                is_unique_violation = isinstance(
                    getattr(exc, "orig", None), UniqueViolationError)

                if not is_unique_violation or attempt >= max_retries:
                    raise

                logger.warning(
                    "UniqueViolationError no commit. Tentativa %s/%s.",
                    attempt,
                    max_retries,
                )

        if last_error:
            raise last_error

    @staticmethod
    def _normalize_like(op: str, value: Any) -> Any:
        """
        Adiciona '%' automaticamente em operadores LIKE/ILIKE quando necessário.

        Exemplo:
            self._normalize_like("ilike", "cielo")
            # retorna "%cielo%"
        """
        if op in ("like", "ilike", "not_like", "not_ilike") and isinstance(value, str):
            if "%" not in value and "_" not in value:
                return f"%{value}%"
        return value

    @staticmethod
    def _is_json_column(attr: Any) -> bool:
        """
        Verifica se um atributo SQLAlchemy representa coluna JSON/JSONB.

        Exemplo:
            if self._is_json_column(Model.extra_information):
                ...
        """
        column_type = getattr(attr, "type", None)
        return isinstance(column_type, (JSON, JSONB))

    @staticmethod
    def _json_as_text(expr: ColumnElement) -> ColumnElement:
        """
        Converte expressão JSON para texto, compatível com SQLAlchemy 1.4/2.x.

        Exemplo:
            text_expr = self._json_as_text(Model.extra_information["status"])
        """
        if hasattr(expr, "astext"):
            return expr.astext
        if hasattr(expr, "as_string"):
            return expr.as_string()
        return cast(expr, Numeric) if False else expr

    def _resolve_and_join(
        self,
        stmt,
        dotted_field: str,
        join_tracker: Dict[str, bool],
    ):
        """
        Resolve campo simples, relacionamento ou caminho JSON/JSONB.

        Suporta:
            - "id"
            - "cliente.nome"
            - "travel.quote.carrier_name"
            - "extra_information.delivery_id"
            - "extra_information.end_customer.federal_tax_payer_id"

        Exemplo:
            stmt, attr = self._resolve_and_join(stmt, "cliente.nome", {})
            stmt = stmt.where(attr.ilike("%CIELO%"))
        """
        if not dotted_field or not isinstance(dotted_field, str):
            raise ValueError("Campo inválido para resolução.")

        parts = dotted_field.split(".")
        current_model = self.model
        path_accum: List[str] = []

        if len(parts) == 1:
            attr = getattr(current_model, parts[0], None)
            if attr is None:
                raise ValueError(
                    f"Campo '{parts[0]}' não existe em {current_model.__name__}.")
            return stmt, attr

        for idx, part in enumerate(parts):
            attr = getattr(current_model, part, None)

            # JSON/JSONB encontrado no caminho.
            if attr is not None and self._is_json_column(attr):
                json_expr: ColumnElement = attr
                for json_key in parts[idx + 1:]:
                    json_expr = json_expr[json_key]
                return stmt, self._json_as_text(json_expr)

            # Último item precisa ser coluna/atributo do modelo atual.
            if idx == len(parts) - 1:
                if attr is None:
                    raise ValueError(
                        f"Coluna '{part}' não existe em {current_model.__name__}.")
                return stmt, attr

            # Caso contrário, precisa ser relacionamento.
            rel = current_model.__mapper__.relationships.get(part)
            if rel is None:
                raise ValueError(
                    f"Campo ou relacionamento '{part}' não existe em {current_model.__name__}."
                )

            path_accum.append(part)
            path_key = ".".join(path_accum)

            if not join_tracker.get(path_key):
                stmt = stmt.join(getattr(current_model, part))
                join_tracker[path_key] = True

            current_model = rel.mapper.class_

        raise ValueError(f"Caminho inválido: {dotted_field}")

    def _validate_operator_value(self, op: str, value: Any) -> Any:
        """
        Valida valores especiais de operadores como IN e BETWEEN.

        Exemplo:
            value = self._validate_operator_value("in", [1, 2, 3])
        """
        if op in ("in", "notin"):
            if not isinstance(value, (list, tuple, set)):
                raise ValueError(f"Operador '{op}' exige lista/tupla/set.")
            return list(value)

        if op in ("between", "not_between"):
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(
                    f"Operador '{op}' exige lista/tupla com 2 valores.")
            return value

        return value

    def _build_simple_condition(
        self,
        stmt,
        *,
        field: str,
        operator: str = "=",
        value: Any = None,
        join_tracker: Dict[str, bool],
    ):
        """
        Monta uma condição simples.

        Exemplo:
            stmt, condition = self._build_simple_condition(
                stmt,
                field="status",
                operator="=",
                value="PENDENTE",
                join_tracker={},
            )
        """
        op = "=" if operator == "==" else operator

        if op not in self._OP:
            raise ValueError(f"Operador '{operator}' não suportado.")

        value = self._normalize_like(op, value)
        value = self._validate_operator_value(op, value)

        stmt, attr = self._resolve_and_join(stmt, field, join_tracker)

        # IN vazio precisa ser tratado, senão pode gerar SQL ruim ou resultado confuso.
        if op == "in" and isinstance(value, list) and len(value) == 0:
            return stmt, false()

        if op == "notin" and isinstance(value, list) and len(value) == 0:
            return stmt, true()

        return stmt, self._OP[op](attr, value)

    def _build_dynamic_condition(
        self,
        stmt,
        filter_item: Dict[str, Any],
        join_tracker: Dict[str, bool],
    ):
        """
        Monta filtros simples ou agrupados.

        Filtro simples:
            {"field": "is_active", "operator": "=", "value": True}

        Filtro agrupado:
            {
                "logic": "or",
                "conditions": [
                    {"field": "target_type", "operator": "=", "value": "all"},
                    {"field": "id", "operator": "in", "value": [1, 2, 3]},
                ],
            }

        Exemplo:
            stmt, condition = self._build_dynamic_condition(stmt, filtro, {})
        """
        if "logic" in filter_item:
            logic = str(filter_item.get("logic", "and")).lower()
            conditions_data = filter_item.get("conditions", []) or []

            built_conditions = []
            for condition_data in conditions_data:
                stmt, condition = self._build_dynamic_condition(
                    stmt, condition_data, join_tracker)
                if condition is not None:
                    built_conditions.append(condition)

            if not built_conditions:
                return stmt, None

            if logic == "and":
                return stmt, and_(*built_conditions)
            if logic == "or":
                return stmt, or_(*built_conditions)
            if logic == "not":
                return stmt, not_(and_(*built_conditions))

            raise ValueError(
                f"Lógica '{logic}' não suportada. Use: and, or ou not.")

        return self._build_simple_condition(
            stmt,
            field=filter_item["field"],
            operator=filter_item.get("operator", "="),
            value=filter_item.get("value"),
            join_tracker=join_tracker,
        )

    @staticmethod
    def _dict_filters_to_list(
        filters: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Converte formato antigo de filtros em lista de filtros.

        Entrada:
            {
                "status": {"operator": "=", "value": "PENDENTE"},
                "cliente.nome": {"operator": "ilike", "value": "CIELO"},
            }

        Saída:
            [
                {"field": "status", "operator": "=", "value": "PENDENTE"},
                {"field": "cliente.nome", "operator": "ilike", "value": "CIELO"},
            ]

        Exemplo:
            filters_list = self._dict_filters_to_list(filters)
        """
        return [
            {
                "field": field,
                "operator": condition.get("operator", "="),
                "value": condition.get("value"),
            }
            for field, condition in filters.items()
        ]

    def _apply_filters(
        self,
        stmt,
        filters: Optional[Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]],
        join_tracker: Dict[str, bool],
    ):
        """
        Aplica filtros simples, múltiplos ou agrupados no statement.

        Exemplo:
            stmt = self._apply_filters(
                stmt,
                [{"field": "status", "operator": "=", "value": "PENDENTE"}],
                {},
            )
        """
        if not filters:
            return stmt

        filters_list: List[Dict[str, Any]]
        if isinstance(filters, dict):
            filters_list = self._dict_filters_to_list(filters)
        else:
            filters_list = filters

        final_conditions = []
        for filter_item in filters_list:
            stmt, condition = self._build_dynamic_condition(
                stmt, filter_item, join_tracker)
            if condition is not None:
                final_conditions.append(condition)

        if final_conditions:
            stmt = stmt.where(and_(*final_conditions))

        return stmt

    def _apply_order(
        self,
        stmt,
        *,
        order_by: Optional[str],
        order_desc: bool = False,
        order_direction: Optional[str] = None,
        force_order_id: bool = False,
        join_tracker: Dict[str, bool],
    ):
        """
        Aplica ordenação dinâmica no statement.

        Exemplo:
            stmt = self._apply_order(
                stmt,
                order_by="created_at",
                order_desc=True,
                force_order_id=True,
                join_tracker={},
            )
        """
        if not order_by:
            return stmt

        stmt, order_attr = self._resolve_and_join(stmt, order_by, join_tracker)

        if order_direction:
            direction = order_direction.lower()
            use_desc = direction == "desc"
        else:
            use_desc = order_desc

        order_clause = desc(order_attr) if use_desc else asc(order_attr)
        stmt = stmt.order_by(order_clause)

        if force_order_id and order_by != "id":
            id_clause = desc(self.model.id) if use_desc else asc(self.model.id)
            stmt = stmt.order_by(id_clause)

        return stmt

    # ---------------------------------------------------------------------
    # Consultas básicas
    # ---------------------------------------------------------------------

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Busca um registro pelo campo ``id``.

        Exemplo:
            order = await crud_order.get(db, id=10)
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalars().unique().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False,
    ) -> List[ModelType]:
        """
        Lista registros com paginação simples.

        Exemplo:
            rows = await crud_order.get_multi(
                db,
                skip=0,
                limit=50,
                order_by="created_at",
                order_desc=True,
            )
        """
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)
        stmt = self._apply_order(
            stmt,
            order_by=order_by,
            order_desc=order_desc,
            join_tracker=join_tracker,
        )
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    async def get_first_by_filter(
        self,
        db: AsyncSession,
        *,
        order_by: str = "id",
        filterby: str = "enviado",
        filter: Any,
    ) -> Optional[ModelType]:
        """
        Busca o primeiro registro por um filtro simples.

        Exemplo:
            obj = await crud_order.get_first_by_filter(
                db,
                filterby="status",
                filter="PENDENTE",
                order_by="id",
            )
        """
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)
        stmt, where_attr = self._resolve_and_join(stmt, filterby, join_tracker)
        stmt = stmt.where(where_attr == filter)
        stmt = self._apply_order(
            stmt, order_by=order_by, join_tracker=join_tracker)

        result = await db.execute(stmt)
        return result.scalars().unique().first()

    async def get_multi_filter(
        self,
        db: AsyncSession,
        *,
        order_by: str = "id",
        filterby: str = "enviado",
        filter: Any,
        order_desc: bool = False,
    ) -> List[ModelType]:
        """
        Lista registros usando um único filtro simples.

        Exemplo:
            rows = await crud_order.get_multi_filter(
                db,
                filterby="cliente.nome",
                filter="CIELO",
                order_by="id",
                order_desc=True,
            )
        """
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)
        stmt, where_attr = self._resolve_and_join(stmt, filterby, join_tracker)
        stmt = stmt.where(where_attr == filter)
        stmt = self._apply_order(
            stmt,
            order_by=order_by,
            order_desc=order_desc,
            join_tracker=join_tracker,
        )

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    async def get_multi_filters(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Union[List[Dict[str, Any]],
                                Dict[str, Dict[str, Any]]]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        order_direction: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        distinct_on_id: bool = False,
        force_order_id: bool = False,
    ) -> List[ModelType]:
        """
        Consulta genérica com múltiplos filtros.

        Aceita filtros no formato lista:
            [
                {"field": "status", "operator": "=", "value": "PENDENTE"},
                {"field": "cliente.nome", "operator": "ilike", "value": "cielo"},
            ]

        Também aceita formato dict legado:
            {
                "status": {"operator": "=", "value": "PENDENTE"},
                "cliente.nome": {"operator": "ilike", "value": "cielo"},
            }

        Exemplo com paginação:
            rows = await crud_order.get_multi_filters(
                db,
                filters=[{"field": "status", "operator": "in", "value": ["PENDENTE", "EM_ROTA"]}],
                order_by="created_at",
                order_desc=True,
                limit=50,
                offset=0,
            )
        """
        join_tracker: Dict[str, bool] = {}
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, filters, join_tracker)

        if distinct_on_id:
            stmt = stmt.distinct(self.model.id)
            if order_by:
                stmt, order_attr = self._resolve_and_join(
                    stmt, order_by, join_tracker)
                use_desc = (
                    order_direction or "desc" if order_desc else "asc").lower() == "desc"
                order_clause = desc(
                    order_attr) if use_desc else asc(order_attr)
                stmt = stmt.order_by(self.model.id, order_clause)
            else:
                stmt = stmt.order_by(self.model.id)
        else:
            stmt = self._apply_order(
                stmt,
                order_by=order_by,
                order_desc=order_desc,
                order_direction=order_direction,
                force_order_id=force_order_id,
                join_tracker=join_tracker,
            )

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    async def get_multi_dynamic_filters(
        self,
        db: AsyncSession,
        *,
        filters: Optional[List[Dict[str, Any]]] = None,
        order_by: str = "id",
        order_direction: str = "asc",
        force_order_id: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Consulta com filtros dinâmicos agrupados por AND/OR/NOT.

        Exemplo:
            rows = await crud_mural.get_multi_dynamic_filters(
                db,
                filters=[
                    {"field": "is_active", "operator": "=", "value": True},
                    {
                        "logic": "or",
                        "conditions": [
                            {"field": "target_type", "operator": "=", "value": "all"},
                            {"field": "id", "operator": "in", "value": [1, 2, 3]},
                        ],
                    },
                ],
                order_by="is_pinned",
                order_direction="desc",
                force_order_id=True,
                limit=100,
            )
        """
        return await self.get_multi_filters(
            db,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            force_order_id=force_order_id,
            offset=offset,
            limit=limit,
        )

    async def get_last_by_filters(
        self,
        db: AsyncSession,
        *,
        filters: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]],
        order_by: str = "id",
    ) -> Optional[ModelType]:
        """
        Busca o último registro conforme filtros informados.

        Por padrão, considera o maior ``id``.

        Exemplo:
            obj = await crud_order.get_last_by_filters(
                db,
                filters={
                    "status": {"operator": "=", "value": "PENDENTE"},
                    "cliente.nome": {"operator": "ilike", "value": "CIELO"},
                },
            )
        """
        rows = await self.get_multi_filters(
            db,
            filters=filters,
            order_by=order_by,
            order_desc=True,
            limit=1,
        )
        obj = rows[0] if rows else None
        if obj:
            await db.refresh(obj)
        return obj

    async def get_first_by_filters(
        self,
        db: AsyncSession,
        *,
        filters: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]],
        order_by: str = "id",
    ) -> Optional[ModelType]:
        """
        Busca o primeiro registro conforme filtros informados.

        Por padrão, considera o menor ``id``.

        Exemplo:
            obj = await crud_order.get_first_by_filters(
                db,
                filters=[
                    {"field": "status", "operator": "=", "value": "PENDENTE"},
                ],
            )
        """
        rows = await self.get_multi_filters(
            db,
            filters=filters,
            order_by=order_by,
            order_desc=False,
            limit=1,
        )
        obj = rows[0] if rows else None
        if obj:
            await db.refresh(obj)
        return obj

    async def get_aggregates(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Union[List[Dict[str, Any]],
                                Dict[str, Dict[str, Any]]]] = None,
        aggregations: List[Dict[str, Any]],
        group_by: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executa agregações dinâmicas com filtros e agrupamentos.

        Agregações suportadas:
            - sum
            - count
            - avg
            - min
            - max

        Exemplo sem group_by:
            result = await crud_order.get_aggregates(
                db,
                filters=[{"field": "status", "operator": "=", "value": "FINALIZADO"}],
                aggregations=[{"op": "count", "field": "id", "alias": "total"}],
            )

        Exemplo com group_by:
            result = await crud_order.get_aggregates(
                db,
                aggregations=[{"op": "sum", "field": "valor", "alias": "total_valor"}],
                group_by=["cliente.nome"],
            )

        Exemplo com JSON numérico:
            result = await crud_order.get_aggregates(
                db,
                aggregations=[
                    {
                        "op": "sum",
                        "field": "extra_information.valor_frete",
                        "alias": "total_frete",
                        "is_json": True,
                    }
                ],
            )
        """
        if not aggregations:
            raise ValueError("Informe pelo menos uma agregação.")

        join_tracker: Dict[str, bool] = {}
        stmt = select().select_from(self.model)
        select_columns = []
        group_columns = []

        for agg in aggregations:
            op = agg["op"]
            field = agg["field"]
            alias = agg.get("alias", f"{op}_{field.replace('.', '_')}")
            is_json = agg.get("is_json", False)

            if op not in self._AGG_OP:
                raise ValueError(f"Agregação '{op}' não suportada.")

            stmt, attr = self._resolve_and_join(stmt, field, join_tracker)

            if is_json:
                attr = cast(attr, Numeric)

            select_columns.append(self._AGG_OP[op](attr).label(alias))

        if group_by:
            for gb in group_by:
                stmt, gb_attr = self._resolve_and_join(stmt, gb, join_tracker)
                label = gb.split(".")[-1]
                group_columns.append(gb_attr)
                select_columns.append(gb_attr.label(label))

            stmt = stmt.group_by(*group_columns)

        stmt = stmt.with_only_columns(*select_columns)
        stmt = self._apply_filters(stmt, filters, join_tracker)

        result = await db.execute(stmt)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def count(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Union[List[Dict[str, Any]],
                                Dict[str, Dict[str, Any]]]] = None,
    ) -> int:
        """
        Conta registros com filtros opcionais.

        Exemplo:
            total = await crud_order.count(
                db,
                filters=[{"field": "status", "operator": "=", "value": "PENDENTE"}],
            )
        """
        join_tracker: Dict[str, bool] = {}
        stmt = select(func.count(self.model.id)).select_from(self.model)
        stmt = self._apply_filters(stmt, filters, join_tracker)
        result = await db.execute(stmt)
        return int(result.scalar() or 0)

    # ---------------------------------------------------------------------
    # Escrita
    # ---------------------------------------------------------------------

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        max_retries: int = 1,
    ) -> ModelType:
        """
        Cria um registro.

        Exemplo:
            order = await crud_order.create(db, obj_in=payload)
        """
        obj_data = self._schema_to_dict(obj_in)
        db_obj = self.model(**obj_data)  # type: ignore[arg-type]
        db.add(db_obj)
        await self._commit_with_retry(db, max_retries=max_retries)
        await db.refresh(db_obj)
        return db_obj

    async def create_multi(
        self,
        db: AsyncSession,
        *,
        obj_in: List[CreateSchemaType],
        max_retries: int = 1,
        refresh: bool = False,
    ) -> Union[Dict[str, Any], List[ModelType]]:
        """
        Cria vários registros de uma vez.

        Correção importante:
            Usa ``await db.commit()`` de fato, não ``await db.commit``.

        Exemplo retornando mensagem:
            result = await crud_order.create_multi(db, obj_in=payloads)

        Exemplo retornando objetos criados:
            objs = await crud_order.create_multi(db, obj_in=payloads, refresh=True)
        """
        db_objs = [self.model(**jsonable_encoder(obj)) for obj in obj_in]
        db.add_all(db_objs)
        await self._commit_with_retry(db, max_retries=max_retries)

        if refresh:
            for obj in db_objs:
                await db.refresh(obj)
            return db_objs

        return {"msg": "Objetos criados com sucesso", "count": len(db_objs)}

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        max_retries: int = 1,
    ) -> ModelType:
        """
        Atualiza um objeto já carregado.

        Aceita schema Pydantic ou dict.

        Exemplo com schema:
            order = await crud_order.update(db, db_obj=order, obj_in=payload)

        Exemplo com dict:
            order = await crud_order.update(
                db,
                db_obj=order,
                obj_in={"status": "FINALIZADO"},
            )
        """
        update_data = self._schema_to_dict(obj_in, exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await self._commit_with_retry(db, max_retries=max_retries)
        await db.refresh(db_obj)
        return db_obj

    async def update_multi(
        self,
        db: AsyncSession,
        *,
        objs_in: List[Union[UpdateSchemaType, Dict[str, Any]]],
        filtro: str,
        max_retries: int = 1,
    ) -> List[ModelType]:
        """
        Atualiza vários registros buscando cada um por um campo filtro.

        Exemplo:
            updated = await crud_order.update_multi(
                db,
                objs_in=[
                    {"external_order_number": "OS001", "status": "FINALIZADO"},
                    {"external_order_number": "OS002", "status": "CANCELADO"},
                ],
                filtro="external_order_number",
            )
        """
        updated_objs: List[ModelType] = []

        for obj_in in objs_in:
            data = self._schema_to_dict(obj_in, exclude_unset=True)

            if filtro not in data:
                raise ValueError(
                    f"Campo filtro '{filtro}' não encontrado no payload.")

            filtro_valor = data[filtro]
            filter_attr = getattr(self.model, filtro, None)

            if filter_attr is None:
                raise ValueError(
                    f"Campo filtro '{filtro}' não existe em {self.model.__name__}.")

            stmt = select(self.model).where(filter_attr == filtro_valor)
            result = await db.execute(stmt)
            db_obj = result.scalars().first()

            if db_obj:
                for key, value in data.items():
                    setattr(db_obj, key, value)
                db.add(db_obj)
                updated_objs.append(db_obj)

        if updated_objs:
            await self._commit_with_retry(db, max_retries=max_retries)
            for obj in updated_objs:
                await db.refresh(obj)

        return updated_objs

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        Remove um registro pelo id.

        Exemplo:
            deleted = await crud_order.remove(db, id=10)
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        obj = result.scalars().first()

        if obj:
            await db.delete(obj)
            await db.commit()

        return obj
