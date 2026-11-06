"""Gera uma cópia sintética das tabelas para uso acadêmico.

Uso: python scripts/criar_base_sintetica_pesquisa.py [--input pasta] [--output pasta]

A entrada nunca é alterada. A saída usa valores financeiros em pontos de índice
(raiz EAP = 1.000), quantidades normalizadas por unidade e chaves genéricas.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "dados_anonimizados/dados_anonimizados_orcamento_atualizado"
DEFAULT_OUTPUT = ROOT / "dados_simulados/dados_sinteticos_pesquisa_operacional"
TABLES = (
    "MPRJ", "MTAREFA", "MCMP", "MRECCMP", "MISM", "MGIS", "MTRFPLAN",
    "MTRFBASE", "MTRFPDO", "MPERIODO", "MTRFMED", "MTRFMEDIDO",
)
NULLS = {"", "NULL", "NONE", "NAN"}
MONEY_TOKENS = ("VALOR", "CUSTO", "PRECO", "SALDO")
UNIT_FIELDS = {"CODUND", "CODUNDREF", "CODUNDDEFAULT"}
PRICE_FIELDS = {
    "VALORUNIT", "CUSTOUNIT", "VALORUNITINDIRETO", "CUSTOUNITINDIRETO",
    "VALORUNITARIO", "PRECOUNITARIO", "CUSTOUNITARIO", "PRECOIMPRODUTIVO",
}
FREE_PREFIXES = ("CAMPOLIVRE", "CLIVRE", "FORMULA", "RECCREATED", "RECMODIFIED")
FREE_TOKENS = (
    "COMENT", "OBSERV", "JUSTIFIC", "CLIENT", "RESPONSAVEL", "ENDERECO",
    "MUNICIPIO", "CIDADE", "TELEFONE", "EMAIL", "CONTATO", "BAIRRO", "RUA",
)
AUDIT_DATES = {"RECCREATEDON", "RECMODIFIEDON", "ULTIMOCALCULO"}
SENSITIVE = re.compile(r"\b(?:S11D|S11-D|VALE|BARBOSA\s+MELLO|COMPOR|PROTHEUS)\b", re.I)
PRECISION = Decimal("0.00000001")
TOLERANCE = Decimal("0.0001")
INDEX_TOTAL = Decimal("1000")
SYNTHETIC_START = datetime(2025, 1, 1)


def null(value: str | None) -> bool:
    return value is None or str(value).strip().upper() in NULLS


def dec(value: str | None) -> Decimal | None:
    if null(value):
        return None
    text = str(value).strip()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def fmt(value: Decimal) -> str:
    return format(value.quantize(PRECISION, rounding=ROUND_HALF_UP), "f")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        headers = list(reader.fieldnames or [])
        if not headers:
            raise ValueError(f"CSV sem cabeçalho: {path.name}")
        rows = list(reader)
    for line, row in enumerate(rows, 2):
        if None in row:
            raise ValueError(f"Quantidade de campos inválida em {path.name}, linha {line}")
    return headers, rows


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, delimiter=";", lineterminator="\r\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def values(rows: list[dict[str, str]], field: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = (row.get(field) or "").strip()
        if not null(value) and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def sequential_map(items: list[str], prefix: str) -> dict[str, str]:
    return {item: f"{prefix}{i:06d}" for i, item in enumerate(items, 1)}


def random_id_map(items: list[str], low: int, high: int) -> dict[str, str]:
    if len(items) > high - low + 1:
        raise ValueError("Faixa insuficiente para gerar IDs sintéticos únicos.")
    used: set[int] = set()
    mapped: dict[str, str] = {}
    for item in items:
        while True:
            candidate = low + secrets.randbelow(high - low + 1)
            if candidate not in used:
                used.add(candidate)
                mapped[item] = str(candidate)
                break
    return mapped


def parse_date(value: str | None) -> datetime | None:
    if null(value):
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        for pattern in ("%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, pattern)
            except ValueError:
                pass
    return None


def date_string(original: str, shifted: datetime) -> str:
    if " " not in original and "T" not in original:
        return shifted.strftime("%Y-%m-%d")
    if "." in original:
        return shifted.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
    return shifted.strftime("%Y-%m-%d %H:%M:%S")


def money_columns(headers: list[str]) -> list[str]:
    result = []
    for field in headers:
        upper = field.upper()
        if upper.startswith(("ID", "PERC", "CAMPOLIVRE", "CLIVRE")) or upper in {"BDI", "FIC", "FIT"}:
            continue
        if any(token in upper for token in MONEY_TOKENS):
            result.append(field)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Cria uma base transformada, coerente e sem identificadores do projeto.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Entrada CSV; permanece intacta.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Pasta nova para a cópia sintética.")
    args = parser.parse_args()
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Pasta de entrada não encontrada: {source}")
    if output.exists():
        raise FileExistsError(f"A pasta de saída já existe; escolha outro destino: {output}")
    if source == output:
        raise ValueError("Entrada e saída precisam ser diferentes.")

    tables: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for name in TABLES:
        path = source / f"{name}.csv"
        if path.is_file():
            tables[name] = read_csv(path)
    for name in ("MTAREFA", "MCMP", "MRECCMP", "MISM", "MPERIODO"):
        if name not in tables:
            raise FileNotFoundError(f"Tabela obrigatória ausente: {name}.csv")

    task_rows = tables["MTAREFA"][1]
    comp_rows = tables["MCMP"][1]
    insum_rows = tables["MISM"][1]
    group_rows = tables.get("MGIS", ([], []))[1]
    period_rows = tables["MPERIODO"][1]
    task_ids = random_id_map(values(task_rows, "IDTRF"), 1_000_000, 1_999_999)
    comp_ids = random_id_map(values(comp_rows, "IDCMP"), 2_000_000, 2_999_999)
    insum_ids = random_id_map(values(insum_rows, "IDISM"), 3_000_000, 3_999_999)
    group_ids = random_id_map(values(group_rows, "IDGIS"), 4_000_000, 4_999_999)
    period_ids = random_id_map(values(period_rows, "IDPERIODO"), 5_000_000, 5_999_999)
    base_ids = random_id_map(values(tables.get("MTRFBASE", ([], []))[1], "IDLINHABASE"), 6_000_000, 6_999_999)
    resource_ids = random_id_map(values(tables["MRECCMP"][1], "IDREC"), 7_000_000, 7_999_999)
    local_ids = {
        (name, "ID"): random_id_map(values(rows, "ID"), 8_000_000, 8_999_999)
        for name, (headers, rows) in tables.items() if "ID" in headers
    }
    task_codes = sequential_map(values(task_rows, "IDTRF"), "ATV-")
    comp_codes = sequential_map(values(comp_rows, "IDCMP"), "CMP-")
    insum_codes = sequential_map(values(insum_rows, "IDISM"), "INS-")
    group_codes = sequential_map(values(group_rows, "IDGIS"), "GRP-")
    comp_by_id = {(r.get("IDCMP") or "").strip(): r for r in comp_rows}
    task_by_id = {(r.get("IDTRF") or "").strip(): r for r in task_rows}
    insum_by_id = {(r.get("IDISM") or "").strip(): r for r in insum_rows}

    # Normaliza cada categoria para que sua maior quantidade de atividade seja 1.000.
    units: list[str] = []
    for _name, (headers, rows) in tables.items():
        for field in UNIT_FIELDS.intersection(headers):
            for unit in values(rows, field):
                if unit not in units:
                    units.append(unit)
    unit_codes = sequential_map(units, "UN-")
    max_quantity: dict[str, Decimal] = defaultdict(Decimal)
    for row in task_rows:
        raw_unit = (row.get("CODUND") or "").strip()
        key = raw_unit if not null(raw_unit) else "__SEM_UNIDADE__"
        quantity = dec(row.get("QUANTIDADE"))
        if quantity is not None and quantity > max_quantity[key]:
            max_quantity[key] = quantity
    unit_scales: dict[str, Decimal] = {
        unit: INDEX_TOTAL / max_quantity[unit] if max_quantity[unit] > 0 else Decimal("1")
        for unit in units
    }
    missing_unit_max = max_quantity["__SEM_UNIDADE__"]
    unit_scales["__SEM_UNIDADE__"] = INDEX_TOTAL / missing_unit_max if missing_unit_max > 0 else Decimal("1")

    def scale_unit(unit: str | None) -> Decimal:
        key = (unit or "").strip()
        if null(key):
            key = "__SEM_UNIDADE__"
        return unit_scales.get(key, Decimal("1"))

    def task_unit(row: dict[str, str]) -> str:
        comp = comp_by_id.get((row.get("IDCMP") or "").strip())
        if comp is not None and not null(comp.get("CODUND")):
            return (comp.get("CODUND") or "").strip()
        return (row.get("CODUND") or "").strip()

    def task_scale(task_id: str | None) -> Decimal:
        task = task_by_id.get((task_id or "").strip())
        return scale_unit(task_unit(task)) if task else Decimal("1")

    def comp_scale(comp_id: str | None) -> Decimal:
        comp = comp_by_id.get((comp_id or "").strip())
        return scale_unit((comp or {}).get("CODUND"))

    def insum_scale(insum_id: str | None) -> Decimal:
        insum = insum_by_id.get((insum_id or "").strip())
        return scale_unit((insum or {}).get("CODUND"))

    root_rows = [r for r in task_rows if not null(r.get("IDTRF")) and (r.get("IDPAI") or "").strip() == (r.get("IDTRF") or "").strip()]
    if not root_rows:
        raise ValueError("Não foi possível localizar a raiz da EAP.")
    root_total = sum((dec(r.get("VALORTOTAL")) or Decimal("0") for r in root_rows), Decimal("0"))
    if root_total <= 0:
        raise ValueError("Total da raiz da EAP vazio ou não positivo.")
    money_scale = INDEX_TOTAL / root_total

    earliest: datetime | None = None
    for _name, (headers, rows) in tables.items():
        for field in headers:
            upper = field.upper()
            if upper in AUDIT_DATES or not (upper.startswith("DATA") or upper.startswith("DT")):
                continue
            for row in rows:
                found = parse_date(row.get(field))
                if found and (earliest is None or found < earliest):
                    earliest = found
    date_shift = SYNTHETIC_START - earliest if earliest else timedelta(0)

    categorical = {
        "TIPO", "TIPOCOMPOSICAO", "TIPOISMDERIVADO", "FLAGTIPOCMP", "TIPOPLANILHA",
        "TIPOTAREFA", "TIPODESMEMBRAMENTO", "TIPOCALENDARIO", "PRODUTIVO", "IMPRODUTIVO",
    }
    category_maps: dict[tuple[str, str], dict[str, str]] = {}
    for name, (headers, rows) in tables.items():
        for field in headers:
            if field in categorical:
                category_maps[(name, field)] = sequential_map(values(rows, field), "CAT-")

    transformed: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for name, (headers, source_rows) in tables.items():
        dest_rows: list[dict[str, str]] = []
        for source_row in source_rows:
            row = dict(source_row)

            # Quantidades em atividade, cronograma e recursos de composição.
            for field in headers:
                amount = dec(source_row.get(field))
                if amount is None or not field.upper().startswith(("QUANT", "QTD")):
                    continue
                factor = Decimal("1")
                if name == "MTAREFA":
                    factor = task_scale(source_row.get("IDTRF"))
                elif name == "MRECCMP":
                    parent_factor = comp_scale(source_row.get("IDCMP"))
                    child_id, insum_id = source_row.get("IDCMPFILHA"), source_row.get("IDISM")
                    resource_factor = comp_scale(child_id) if not null(child_id) else insum_scale(insum_id)
                    factor = resource_factor / parent_factor if parent_factor else Decimal("1")
                elif name in {"MTRFPLAN", "MTRFBASE", "MTRFPDO", "MTRFMEDIDO"}:
                    factor = task_scale(source_row.get("IDTRF"))
                row[field] = fmt(amount * factor)

            # Valores unitários absorvem a escala da quantidade; totais recebem o índice.
            for field in money_columns(headers):
                amount = dec(source_row.get(field))
                if amount is None:
                    continue
                factor = money_scale
                upper = field.upper()
                if name == "MISM":
                    factor /= scale_unit(source_row.get("CODUND"))
                elif name == "MCMP":
                    factor /= comp_scale(source_row.get("IDCMP"))
                elif name == "MRECCMP":
                    if upper == "VALORTOTAL":
                        factor /= comp_scale(source_row.get("IDCMP"))
                    elif upper in PRICE_FIELDS:
                        child_id, insum_id = source_row.get("IDCMPFILHA"), source_row.get("IDISM")
                        resource_factor = comp_scale(child_id) if not null(child_id) else insum_scale(insum_id)
                        factor /= resource_factor
                elif name == "MTAREFA" and upper in PRICE_FIELDS:
                    factor /= task_scale(source_row.get("IDTRF"))
                row[field] = fmt(amount * factor)

            # Calendário sintético e retirada de metadados de autoria.
            for field in headers:
                upper = field.upper()
                if upper in AUDIT_DATES:
                    row[field] = "NULL"
                elif upper.startswith("DATA") or upper.startswith("DT"):
                    found = parse_date(source_row.get(field))
                    if found is not None:
                        row[field] = date_string(source_row.get(field, ""), found + date_shift)

            # Campos livres, comentários, fórmulas, auditoria e referências pessoais.
            for field in headers:
                upper = field.upper()
                if upper.startswith(FREE_PREFIXES) or any(token in upper for token in FREE_TOKENS):
                    row[field] = "NULL"
                if upper in {"CODCLIENTE", "CLIENTE"}:
                    row[field] = "NULL"
                elif upper == "ORIGEM":
                    row[field] = "SINTETICO"
                elif upper in {"IDPRJ", "CODCOLIGADA"}:
                    row[field] = "1"

            # Chaves relacionais são substituídas com mapas em memória; outros IDs são apagados.
            for field in headers:
                upper, original = field.upper(), (source_row.get(field) or "").strip()
                if not upper.startswith("ID") or null(original):
                    continue
                replacement = None
                if upper == "IDPRJ":
                    replacement = "1"
                elif upper.startswith("IDTRF") or (upper == "IDPAI" and name == "MTAREFA"):
                    replacement = task_ids.get(original)
                elif upper.startswith("IDCMP"):
                    replacement = comp_ids.get(original)
                elif upper.startswith("IDISM"):
                    replacement = insum_ids.get(original)
                elif upper.startswith("IDGIS"):
                    replacement = group_ids.get(original)
                elif upper.startswith("IDPERIODO"):
                    replacement = period_ids.get(original)
                elif upper == "IDLINHABASE":
                    replacement = base_ids.get(original)
                elif upper == "IDREC":
                    replacement = resource_ids.get(original)
                elif upper == "ID":
                    replacement = local_ids.get((name, "ID"), {}).get(original)
                row[field] = replacement or "NULL"

            # Códigos de cadastro e unidades viram rótulos genéricos.
            for field in headers:
                upper, original = field.upper(), (source_row.get(field) or "").strip()
                if null(original):
                    continue
                if upper == "CODTRF":
                    row[field] = task_codes.get((source_row.get("IDTRF") or "").strip(), "ATV-SINTETICA")
                elif upper == "CODCMP":
                    row[field] = comp_codes.get((source_row.get("IDCMP") or "").strip(), "CMP-SINTETICA")
                elif upper == "CODISM":
                    row[field] = insum_codes.get((source_row.get("IDISM") or "").strip(), "INS-SINTETICO")
                elif upper == "CODGIS":
                    row[field] = group_codes.get((source_row.get("IDGIS") or "").strip(), "GRP-SINTETICO")
                elif upper == "CODPRJ":
                    row[field] = "PROJ-SINTETICO-001"
                elif upper in UNIT_FIELDS:
                    unit_value = original
                    if name == "MTAREFA" and upper == "CODUND":
                        linked_comp = comp_by_id.get((source_row.get("IDCMP") or "").strip())
                        if linked_comp is not None and not null(linked_comp.get("CODUND")):
                            unit_value = (linked_comp.get("CODUND") or "").strip()
                    row[field] = unit_codes.get(unit_value, "UN-GENERICA")
                elif upper == "CODMOEDATAREFA":
                    row[field] = "IDX"
                elif upper.startswith("COD") and upper != "CODCOLIGADA":
                    unique_codes = values(source_rows, field)
                    cmap = sequential_map(unique_codes, "CAT-")
                    row[field] = cmap.get(original, "CAT-NULL")

            # Substitui texto livre por descrições genéricas sem apagar as categorias de análise.
            if name == "MTAREFA":
                label = task_codes.get((source_row.get("IDTRF") or "").strip(), "SINTETICA")
                if "NOME" in row:
                    row["NOME"] = f"Atividade {label}"
                if "DESCRICAO" in row:
                    row["DESCRICAO"] = f"Registro sintético {label}"
            elif name == "MCMP" and "DESCCMP" in row:
                row["DESCCMP"] = f"Composição {comp_codes.get((source_row.get('IDCMP') or '').strip(), 'SINTETICA')}"
            elif name == "MISM" and "DESCISM" in row:
                row["DESCISM"] = f"Insumo {insum_codes.get((source_row.get('IDISM') or '').strip(), 'SINTETICO')}"
            elif name == "MGIS" and "DESCGIS" in row:
                row["DESCGIS"] = f"Grupo de custo {group_codes.get((source_row.get('IDGIS') or '').strip(), 'SINTETICO')}"
            elif name == "MPRJ":
                if "DESCRICAO" in row:
                    row["DESCRICAO"] = "Projeto sintético para pesquisa"
                if "DESCRICAOREVISAO" in row:
                    row["DESCRICAOREVISAO"] = "NULL"

            for field in headers:
                if field in categorical:
                    original = (source_row.get(field) or "").strip()
                    if not null(original):
                        row[field] = category_maps[(name, field)].get(original, "CAT-NULL")
            dest_rows.append(row)
        transformed[name] = (headers, dest_rows)

    # Conferências incorporadas à execução: composição, atividade, EAP e total indexado.
    out_tasks = transformed["MTAREFA"][1]
    out_comps = transformed["MCMP"][1]
    out_resources = transformed["MRECCMP"][1]
    task_index = {(r.get("IDTRF") or "").strip(): r for r in out_tasks}
    comp_index = {(r.get("IDCMP") or "").strip(): r for r in out_comps}
    resources_by_comp: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in out_resources:
        if not null(row.get("IDCMP")):
            resources_by_comp[(row.get("IDCMP") or "").strip()].append(row)
    comp_mismatches = 0
    for comp_id, comp in comp_index.items():
        detail = resources_by_comp.get(comp_id, [])
        if not detail:
            continue
        total = dec(comp.get("VALORTOTAL"))
        detail_total = sum((dec(r.get("VALORTOTAL")) or Decimal("0") for r in detail), Decimal("0"))
        if total is not None and abs(total - detail_total) > TOLERANCE:
            comp_mismatches += 1
    task_mismatches = 0
    for row in out_tasks:
        if null(row.get("IDCMP")):
            continue
        q, price, total = dec(row.get("QUANTIDADE")), dec(row.get("VALORUNIT")), dec(row.get("VALORTOTAL"))
        if q is not None and price is not None and total is not None and abs(q * price - total) > TOLERANCE:
            task_mismatches += 1
    children: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in out_tasks:
        parent, task_id = (row.get("IDPAI") or "").strip(), (row.get("IDTRF") or "").strip()
        if not null(parent) and parent != task_id:
            children[parent].append(row)
    hierarchy_mismatches = 0
    for parent_id, rows in children.items():
        parent = task_index.get(parent_id)
        if not parent:
            continue
        parent_total = dec(parent.get("VALORTOTAL"))
        child_total = sum((dec(r.get("VALORTOTAL")) or Decimal("0") for r in rows), Decimal("0"))
        if parent_total is not None and abs(parent_total - child_total) > TOLERANCE:
            hierarchy_mismatches += 1
    output_roots = [r for r in out_tasks if (r.get("IDPAI") or "").strip() == (r.get("IDTRF") or "").strip()]
    output_total = sum((dec(r.get("VALORTOTAL")) or Decimal("0") for r in output_roots), Decimal("0"))
    mentions = []
    for name, (headers, rows) in transformed.items():
        for row in rows:
            for field in headers:
                if SENSITIVE.search(row.get(field, "") or ""):
                    mentions.append(f"{name}.{field}")
    if comp_mismatches or task_mismatches or hierarchy_mismatches:
        raise ValueError(f"Divergências: composições={comp_mismatches}, atividades={task_mismatches}, EAP={hierarchy_mismatches}.")
    if mentions:
        raise ValueError("Menção explícita não removida: " + ", ".join(sorted(set(mentions))))
    if abs(output_total - INDEX_TOTAL) > TOLERANCE:
        raise ValueError(f"Total sintético da raiz fora do alvo: {output_total}")

    output.mkdir(parents=True, exist_ok=False)
    counts: dict[str, int] = {}
    dictionary: list[dict[str, str]] = []
    for name, (headers, rows) in transformed.items():
        write_csv(output / f"{name}.csv", headers, rows)
        counts[name] = len(rows)
        dictionary.extend({"TABELA": name, "COLUNA": col, "ORDEM": str(i)} for i, col in enumerate(headers, 1))
    write_csv(output / "dicionario_colunas.csv", ["TABELA", "COLUNA", "ORDEM"], dictionary)

    report: dict[str, Any] = {
        "status": "base_sintetica_gerada",
        "unidade_financeira": "pontos de índice; raiz da EAP = 1.000",
        "normalizacao_de_quantidades": "a maior quantidade positiva de atividade por categoria de unidade = 1.000; demais mantêm proporção; valores não são unidades físicas",
        "calendario_sintetico": {
            "primeira_data": SYNTHETIC_START.strftime("%Y-%m-%d"),
            "deslocamento_em_dias": date_shift.days,
            "duracoes_e_intervalos_preservados": True,
        },
        "linhas_por_tabela": counts,
        "categorias_de_unidade": len(units),
        "conferencias": {
            "total_raiz_indice": fmt(output_total),
            "divergencias_composicao_vs_recursos": comp_mismatches,
            "divergencias_atividade_quantidade_vezes_valor_unitario": task_mismatches,
            "divergencias_agrupadores_eap_vs_filhos": hierarchy_mismatches,
            "menções_explicitas_cliente_projeto_sistema": len(mentions),
        },
        "pendencias_herdadas_do_recalculo": {
            "linhas_de_recurso_com_formula_improdutiva_ou_nao_confirmada": 102,
            "composicoes_sem_linhas_de_recurso": 3,
            "atividades_sem_composicao_preservadas": 47,
        },
        "observacoes": [
            "IDs e códigos foram substituídos; o mapa temporário não foi gravado.",
            "Descrições, comentários, fórmulas, campos livres, autoria e unidades originais foram removidos ou generalizados.",
            "Hierarquia EAP, ligações entre tabelas, classificações direta/indireta/em dúvida e durações foram preservadas.",
            "A saída mantém parte das proporções e da estrutura do orçamento; a transformação reduz exposição, mas não garante anonimização absoluta nem autorização de divulgação.",
            "A base herdou pendências de fórmula da etapa anterior. A hierarquia EAP não representa predecessoras PERT/CPM.",
        ],
    }
    (output / "relatorio_base_sintetica.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = """BASE SINTÉTICA PARA PESQUISA OPERACIONAL

Valores financeiros estão em pontos de índice; o total da raiz da EAP é 1.000.
Quantidades foram normalizadas por categoria de unidade e não representam medidas físicas.
IDs, códigos, nomes, descrições, comentários, fórmulas, campos livres, autoria e unidades foram substituídos ou removidos. Datas foram transladadas para calendário sintético; durações e intervalos relativos foram preservados.

A hierarquia EAP, os relacionamentos de composição e as classificações DIRETA/INDIRETA/DUVIDA foram mantidos. Não foram encontradas predecessoras explícitas na extração; IDPAI é hierarquia, não dependência PERT/CPM.

Esta cópia serve para análise acadêmica. Não usar para orçamento ou execução da obra. Ela preserva parte da estrutura e das proporções do orçamento, portanto reduz a exposição, mas não garante anonimização absoluta nem substitui autorização da empresa para divulgação.

As exceções herdadas de fórmula estão em relatorio_base_sintetica.json. dicionario_colunas.csv lista a ordem das colunas.
"""
    (output / "LEIA-ME.txt").write_text(readme, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Saída: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
