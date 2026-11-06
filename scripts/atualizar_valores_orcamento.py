"""Propaga valores anonimizados da composição até a EAP em uma cópia da base.

Uso:
    python scripts/atualizar_valores_orcamento.py
    python scripts/atualizar_valores_orcamento.py --input dados_anonimizados/dados_anonimizados_base_completa --output dados_anonimizados/dados_anonimizados_orcamento_atualizado
    python scripts/atualizar_valores_orcamento.py --strict

O script não altera a pasta de entrada. Ele recalcula linhas de recurso para as
quais a regra foi identificada, recalcula as composições de baixo para cima,
atualiza atividades associadas e seus agrupadores da EAP e redistribui os
valores monetários do cronograma pelo novo total da tarefa. Casos com fórmulas
improdutivas ou sem coeficiente produtivo são preservados e contabilizados como
pendências, em vez de receberem uma fórmula presumida.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "dados_anonimizados/dados_anonimizados_base_completa"
DEFAULT_OUTPUT = ROOT / "dados_anonimizados/dados_anonimizados_orcamento_atualizado"
NULLS = {"", "NULL", "NONE", "NAN"}
MONEY_TOKENS = ("VALOR", "CUSTO", "PRECO")
PRECISION = Decimal("0.0001")


def is_null(value: str | None) -> bool:
    return value is None or value.strip().upper() in NULLS


def to_decimal(value: str | None) -> Decimal | None:
    if is_null(value):
        return None
    text = str(value).strip()
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def round_rm(value: Decimal) -> Decimal:
    return value.quantize(PRECISION, rounding=ROUND_HALF_UP)


def format_rm(value: Decimal) -> str:
    return format(round_rm(value), ".4f")


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        headers = list(reader.fieldnames or [])
        if not headers:
            raise ValueError(f"CSV sem cabeçalho: {path.name}")
        rows = list(reader)
    for row_number, row in enumerate(rows, 2):
        if None in row:
            raise ValueError(f"Número de colunas inválido em {path.name}, linha {row_number}")
    return headers, rows


def write_table(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=headers,
            delimiter=";",
            lineterminator="\r\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def require_fields(table: str, headers: list[str], required: tuple[str, ...]) -> None:
    missing = [field for field in required if field not in headers]
    if missing:
        raise ValueError(f"{table}.csv sem as colunas necessárias: {', '.join(missing)}")


def unique_index(table: str, rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        value = (row.get(key) or "").strip()
        if is_null(value):
            continue
        if value in index:
            raise ValueError(f"Chave duplicada em {table}.{key}: não é seguro recalcular a árvore")
        index[value] = row
    return index


def monetary_fields(headers: list[str]) -> list[str]:
    result = []
    for field in headers:
        name = field.upper()
        if name.startswith("ID") or name.startswith("PERC") or name in {"BDI", "FIC", "FIT"}:
            continue
        if any(token in name for token in MONEY_TOKENS):
            result.append(field)
    return result


def scale_money_fields(
    row: dict[str, str],
    fields: list[str],
    ratio: Decimal | None,
    exclude: set[str] | None = None,
) -> int:
    if ratio is None:
        return 0
    exclude = exclude or set()
    count = 0
    for field in fields:
        if field in exclude:
            continue
        number = to_decimal(row.get(field))
        if number is None:
            continue
        row[field] = format_rm(number * ratio)
        count += 1
    return count


def safe_ratio(new_value: Decimal, old_value: Decimal | None) -> Decimal | None:
    if old_value is None or old_value == 0:
        return None
    return new_value / old_value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recalcula a cadeia de custos de insumos/recursos até composições e atividades."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Pasta CSV de entrada; permanece intacta.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Nova pasta de saída; não pode existir.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Cancela sem gerar a cópia se houver linhas de recurso com fórmula especial/sem coeficiente resolvido.",
    )
    args = parser.parse_args()

    input_root = args.input.expanduser().resolve()
    output_root = args.output.expanduser().resolve()
    if not input_root.is_dir():
        raise FileNotFoundError(f"Pasta de entrada não encontrada: {input_root}")
    if output_root.exists():
        raise FileExistsError(f"A pasta de saída já existe: {output_root}")
    if input_root == output_root:
        raise ValueError("Entrada e saída precisam ser pastas diferentes.")

    tables: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    required_tables = ("MISM", "MCMP", "MRECCMP", "MTAREFA")
    for table in required_tables:
        path = input_root / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Tabela obrigatória ausente: {path.name}")
        tables[table] = read_table(path)

    for table, required in {
        "MISM": ("IDISM", "VALOR"),
        "MCMP": ("IDCMP", "VALORTOTAL"),
        "MRECCMP": ("IDCMP", "IDCMPFILHA", "IDISM", "QUANTIDADE", "COEFICIENTEPRODUTIVO", "COEFICIENTEIMPRODUTIVO", "VALORUNIT", "VALORTOTAL"),
        "MTAREFA": ("IDTRF", "IDPAI", "IDCMP", "QUANTIDADE", "VALORUNIT", "VALORTOTAL"),
    }.items():
        require_fields(table, tables[table][0], required)

    mism_headers, mism_rows = tables["MISM"]
    mcmp_headers, mcmp_rows = tables["MCMP"]
    mreccmp_headers, mreccmp_rows = tables["MRECCMP"]
    mtarefa_headers, mtarefa_rows = tables["MTAREFA"]

    insums = unique_index("MISM", mism_rows, "IDISM")
    compositions = unique_index("MCMP", mcmp_rows, "IDCMP")
    tasks = unique_index("MTAREFA", mtarefa_rows, "IDTRF")

    resources_by_composition: dict[str, list[dict[str, str]]] = defaultdict(list)
    for resource in mreccmp_rows:
        parent = (resource.get("IDCMP") or "").strip()
        if not is_null(parent):
            resources_by_composition[parent].append(resource)

    report: dict[str, Any] = {
        "status": "calculando",
        "valores_recalculados": {
            "linhas_recurso_por_coeficiente_produtivo": 0,
            "valores_unitarios_de_recurso_atualizados": 0,
            "composicoes_recalculadas": 0,
            "atividades_associadas_a_composicao_recalculadas": 0,
            "agrupadores_eap_recalculados": 0,
            "linhas_de_cronograma_atualizadas": 0,
        },
        "pendencias": {
            "recursos_com_coeficiente_improdutivo_ou_sem_formula_confirmada": 0,
            "recursos_sem_coeficiente_produtivo_valido": 0,
            "referencias_de_recurso_sem_cadastro_local": 0,
            "composicoes_sem_linhas_de_recurso": 0,
            "atividades_sem_composicao_preservadas": 0,
            "valores_sem_base_para_proporcao": 0,
        },
        "observacoes": [
            "O cálculo de linha validado na extração para recursos sem coeficiente improdutivo é QUANTIDADE × VALORUNIT ÷ COEFICIENTEPRODUTIVO.",
            "Linhas com coeficiente improdutivo ou coeficiente produtivo inválido mantêm o VALORTOTAL de entrada e aparecem como pendência; não foi presumida uma fórmula para elas.",
            "As decomposições monetárias de composição/atividade são ajustadas proporcionalmente ao novo total para preservar suas proporções existentes.",
            "Composições são recalculadas de baixo para cima. Atividades associadas usam o total unitário da composição; o total da atividade é quantidade × valor unitário.",
            "Atividades sem composição e sem filhos mantêm os valores existentes; são contabilizadas para revisão manual.",
            "Os valores do projeto em MPRJ não são recalculados porque a extração não permite separar todas as parcelas de BDI e custos indiretos com segurança.",
        ],
    }

    state: dict[str, int] = {}

    def recalculate_composition(composition_id: str) -> Decimal:
        if composition_id not in compositions:
            raise KeyError(composition_id)
        if state.get(composition_id) == 1:
            raise ValueError("Ciclo encontrado entre composições; recálculo cancelado.")
        if state.get(composition_id) == 2:
            value = to_decimal(compositions[composition_id].get("VALORTOTAL"))
            if value is None:
                raise ValueError("Composição calculada sem VALORTOTAL.")
            return value

        state[composition_id] = 1
        component_rows = resources_by_composition.get(composition_id, [])
        if not component_rows:
            report["pendencias"]["composicoes_sem_linhas_de_recurso"] += 1
            current = to_decimal(compositions[composition_id].get("VALORTOTAL"))
            if current is None:
                raise ValueError("Composição sem recursos e sem valor total cadastrado.")
            state[composition_id] = 2
            return current

        subtotal = Decimal("0")
        for resource in component_rows:
            child_id = (resource.get("IDCMPFILHA") or "").strip()
            insum_id = (resource.get("IDISM") or "").strip()
            has_child = not is_null(child_id)
            has_insum = not is_null(insum_id)
            if has_child and has_insum:
                report["pendencias"]["referencias_de_recurso_sem_cadastro_local"] += 1

            unit_value: Decimal | None = None
            if has_child and child_id in compositions:
                unit_value = recalculate_composition(child_id)
            elif has_insum and insum_id in insums:
                # VALOR é o preço unitário base; se ausente, tenta VALORSEMLEIS.
                unit_value = to_decimal(insums[insum_id].get("VALOR"))
                if unit_value is None:
                    unit_value = to_decimal(insums[insum_id].get("VALORSEMLEIS"))
            elif has_child or has_insum:
                report["pendencias"]["referencias_de_recurso_sem_cadastro_local"] += 1
                unit_value = to_decimal(resource.get("VALORUNIT"))
            else:
                unit_value = to_decimal(resource.get("VALORUNIT"))

            if unit_value is not None:
                resource["VALORUNIT"] = format_rm(unit_value)
                report["valores_recalculados"]["valores_unitarios_de_recurso_atualizados"] += 1

            quantity = to_decimal(resource.get("QUANTIDADE"))
            productive_coefficient = to_decimal(resource.get("COEFICIENTEPRODUTIVO"))
            unproductive_coefficient = to_decimal(resource.get("COEFICIENTEIMPRODUTIVO"))
            can_calculate = (
                quantity is not None
                and unit_value is not None
                and productive_coefficient is not None
                and productive_coefficient > 0
                and (unproductive_coefficient is None or unproductive_coefficient == 0)
                and not (has_child and has_insum)
            )

            if can_calculate:
                line_total = round_rm(quantity * unit_value / productive_coefficient)
                resource["VALORTOTAL"] = format_rm(line_total)
                subtotal += line_total
                report["valores_recalculados"]["linhas_recurso_por_coeficiente_produtivo"] += 1
            else:
                line_total = to_decimal(resource.get("VALORTOTAL"))
                if line_total is None:
                    line_total = Decimal("0")
                subtotal += line_total
                if unproductive_coefficient not in (None, Decimal("0")) or (has_child and has_insum):
                    report["pendencias"]["recursos_com_coeficiente_improdutivo_ou_sem_formula_confirmada"] += 1
                elif productive_coefficient is None or productive_coefficient <= 0:
                    report["pendencias"]["recursos_sem_coeficiente_produtivo_valido"] += 1
                else:
                    report["pendencias"]["recursos_com_coeficiente_improdutivo_ou_sem_formula_confirmada"] += 1

        new_total = round_rm(subtotal)
        composition = compositions[composition_id]
        old_total = to_decimal(composition.get("VALORTOTAL"))
        ratio = safe_ratio(new_total, old_total)
        if ratio is None and old_total != new_total:
            report["pendencias"]["valores_sem_base_para_proporcao"] += 1
        scale_money_fields(
            composition,
            monetary_fields(mcmp_headers),
            ratio,
            exclude={"VALORTOTAL"},
        )
        composition["VALORTOTAL"] = format_rm(new_total)
        report["valores_recalculados"]["composicoes_recalculadas"] += 1
        state[composition_id] = 2
        return new_total

    for composition_id in compositions:
        recalculate_composition(composition_id)

    # Snapshot current task totals after composition updates but before activity roll-up.
    old_task_totals = {key: to_decimal(row.get("VALORTOTAL")) for key, row in tasks.items()}
    children_by_task: dict[str, list[str]] = defaultdict(list)
    for task_id, row in tasks.items():
        parent_id = (row.get("IDPAI") or "").strip()
        if not is_null(parent_id) and parent_id != task_id and parent_id in tasks:
            children_by_task[parent_id].append(task_id)

    task_state: dict[str, int] = {}
    new_task_totals: dict[str, Decimal] = {}
    money_fields_task = monetary_fields(mtarefa_headers)

    def recalculate_task(task_id: str) -> Decimal:
        if task_state.get(task_id) == 1:
            raise ValueError("Ciclo encontrado na hierarquia de tarefas; recálculo cancelado.")
        if task_state.get(task_id) == 2:
            return new_task_totals[task_id]
        task_state[task_id] = 1
        task = tasks[task_id]
        composition_id = (task.get("IDCMP") or "").strip()
        child_ids = children_by_task.get(task_id, [])
        old_total = to_decimal(task.get("VALORTOTAL"))

        if not is_null(composition_id) and composition_id in compositions:
            unit_value = recalculate_composition(composition_id)
            quantity = to_decimal(task.get("QUANTIDADE"))
            if quantity is None:
                new_total = old_total if old_total is not None else Decimal("0")
                report["pendencias"]["valores_sem_base_para_proporcao"] += 1
            else:
                new_total = round_rm(quantity * unit_value)
            ratio = safe_ratio(new_total, old_total)
            if ratio is None and old_total != new_total:
                report["pendencias"]["valores_sem_base_para_proporcao"] += 1
            scale_money_fields(task, money_fields_task, ratio, exclude={"VALORUNIT", "VALORTOTAL"})
            task["VALORUNIT"] = format_rm(unit_value)
            task["VALORTOTAL"] = format_rm(new_total)
            report["valores_recalculados"]["atividades_associadas_a_composicao_recalculadas"] += 1
        elif child_ids:
            new_total = round_rm(sum((recalculate_task(child_id) for child_id in child_ids), Decimal("0")))
            ratio = safe_ratio(new_total, old_total)
            if ratio is None and old_total != new_total:
                report["pendencias"]["valores_sem_base_para_proporcao"] += 1
            scale_money_fields(task, money_fields_task, ratio, exclude={"VALORTOTAL"})
            task["VALORTOTAL"] = format_rm(new_total)
            report["valores_recalculados"]["agrupadores_eap_recalculados"] += 1
        else:
            new_total = old_total if old_total is not None else Decimal("0")
            report["pendencias"]["atividades_sem_composicao_preservadas"] += 1

        task_state[task_id] = 2
        new_task_totals[task_id] = new_total
        return new_total

    for task_id in tasks:
        recalculate_task(task_id)

    # Valores de cronograma vinculados às tarefas mantêm as participações por período.
    schedule_tables = ("MTRFPLAN", "MTRFBASE", "MTRFPDO")
    for table in schedule_tables:
        path = input_root / f"{table}.csv"
        if not path.is_file():
            continue
        headers, rows = read_table(path)
        if "IDTRF" not in headers:
            continue
        value_fields = monetary_fields(headers)
        for row in rows:
            task_id = (row.get("IDTRF") or "").strip()
            old_total = old_task_totals.get(task_id)
            new_total = new_task_totals.get(task_id)
            if old_total is None or new_total is None:
                continue
            ratio = safe_ratio(new_total, old_total)
            if ratio is not None:
                report["valores_recalculados"]["linhas_de_cronograma_atualizadas"] += bool(
                    scale_money_fields(row, value_fields, ratio)
                )
        tables[table] = (headers, rows)

    pending_count = sum(report["pendencias"].values())
    report["status"] = "recalculado_com_pendencias" if pending_count else "recalculado"
    if args.strict and pending_count:
        raise RuntimeError(
            f"Modo estrito: há {pending_count} pendência(s); nenhuma cópia foi gravada. "
            "Consulte a documentação do script e valide as fórmulas especiais do RM."
        )

    output_root.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(tempfile.mkdtemp(prefix=f"{output_root.name}_", dir=output_root.parent))
    work_root = temp_parent / "resultado"
    try:
        shutil.copytree(input_root, work_root)
        for table, (headers, rows) in tables.items():
            write_table(work_root / f"{table}.csv", headers, rows)

        report_path = work_root / "relatorio_recalculo.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest_path = work_root / "manifesto_anonimizacao.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["recalculo_orcamento"] = report
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        readme_path = work_root / "LEIA-ME.txt"
        if readme_path.is_file():
            readme = readme_path.read_text(encoding="utf-8")
            readme += (
                "\nValores recalculados: ver relatorio_recalculo.json. "
                "Linhas com coeficiente improdutivo ou fórmula não confirmada foram preservadas "
                "e devem ser revisadas antes de tratar o orçamento como totalmente reconciliado.\n"
            )
            readme_path.write_text(readme, encoding="utf-8")
        work_root.rename(output_root)
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    else:
        shutil.rmtree(temp_parent, ignore_errors=True)

    print(f"Status: {report['status']}")
    print(f"Composições recalculadas: {report['valores_recalculados']['composicoes_recalculadas']}")
    print(f"Atividades com composição recalculadas: {report['valores_recalculados']['atividades_associadas_a_composicao_recalculadas']}")
    print(f"Linhas de recurso com fórmula produtiva recalculadas: {report['valores_recalculados']['linhas_recurso_por_coeficiente_produtivo']}")
    print(f"Pendências: {pending_count}; veja relatorio_recalculo.json")
    print(f"Saída: {output_root}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
