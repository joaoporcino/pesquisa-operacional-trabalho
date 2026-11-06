#!/usr/bin/env python
"""Resolve a escolha de equipes e o escalonamento do recorte usando SciPy/HiGHS."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


THREAD_DIR = Path(__file__).resolve().parent
DATA_DIR = THREAD_DIR / "dados_modelo"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=columns,
            delimiter=";",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def num(value: float, places: int = 8) -> float:
    return round(float(value), places)


def solve_model(
    data_dir: Path = DATA_DIR,
    ci_day_override: float | None = None,
    ci_person_day_override: float | None = None,
    write_outputs: bool = True,
):
    activities = read_csv(data_dir / "atividades.csv")
    edges = read_csv(data_dir / "precedencias.csv")
    teams = read_csv(data_dir / "equipes.csv")
    resources = read_csv(data_dir / "recursos_compartilhados.csv")
    alternatives = read_csv(data_dir / "habilitacoes_alternativas.csv")
    fixed_costs = read_csv(data_dir / "custos_fixos.csv")
    assumptions = {row["PARAMETRO"]: row["VALOR"] for row in read_csv(data_dir / "premissas.csv")}

    activity_ids = [row["ID_ATIVIDADE"] for row in activities]
    activity_by_id = {row["ID_ATIVIDADE"]: row for row in activities}
    executable_ids = [row["ID_ATIVIDADE"] for row in activities if row["TIPO"] == "EXECUCAO"]
    alternative_by_key = {
        (row["ID_ATIVIDADE"], row["ID_EQUIPE"]): row
        for row in alternatives
    }
    alternatives_by_activity: dict[str, list[dict]] = defaultdict(list)
    team_pool = {row["ID_EQUIPE"]: row["ID_POOL_RECURSO"] for row in teams}
    pool_capacity = {row["ID_POOL_RECURSO"]: int(row["DISPONIBILIDADE"]) for row in resources}
    if set(team_pool.values()) - set(pool_capacity):
        raise ValueError("Há um perfil de equipe sem pool de recurso cadastrado.")
    if any(capacity != 1 for capacity in pool_capacity.values()):
        raise ValueError("Este piloto implementa capacidade unitária por pool compartilhado.")
    eligible_by_pool: dict[str, set[str]] = defaultdict(set)
    for row in alternatives:
        alternatives_by_activity[row["ID_ATIVIDADE"]].append(row)
        eligible_by_pool[team_pool[row["ID_EQUIPE"]]].add(row["ID_ATIVIDADE"])

    for activity_id in executable_ids:
        if len(alternatives_by_activity[activity_id]) == 0:
            raise ValueError(f"Atividade sem equipe habilitada: {activity_id}")

    # Variáveis: seleção x(i,e), início S(i), makespan Cmax e ordem binária por par/equipe.
    x_index = {}
    cursor = 0
    for row in alternatives:
        x_index[(row["ID_ATIVIDADE"], row["ID_EQUIPE"])] = cursor
        cursor += 1

    s_index = {}
    for activity_id in activity_ids:
        s_index[activity_id] = cursor
        cursor += 1
    cmax_index = cursor
    cursor += 1

    order_index = {}
    pair_rows = []
    for pool_id, ids in eligible_by_pool.items():
        unique_ids = sorted(set(ids), key=activity_ids.index)
        for i_pos in range(len(unique_ids)):
            for j_pos in range(i_pos + 1, len(unique_ids)):
                i, j = unique_ids[i_pos], unique_ids[j_pos]
                order_index[(i, j, pool_id)] = cursor
                pair_rows.append((i, j, pool_id, cursor))
                cursor += 1

    n_variables = cursor
    max_duration_sum = sum(
        max(float(row["DURACAO_DIAS"]) for row in alternatives_by_activity[activity_id])
        for activity_id in executable_ids
    )
    big_m = max_duration_sum + 1.0

    objective = [0.0] * n_variables
    lower_bounds = [0.0] * n_variables
    upper_bounds = [big_m] * n_variables
    integrality = [0] * n_variables

    ci_day = float(ci_day_override) if ci_day_override is not None else float(assumptions["Custo indireto por prazo"])
    # Premissa de custo indireto por pessoa-dia, lida da tabela e usada fora dos salários/equipamentos.
    ci_person_day = float(ci_person_day_override) if ci_person_day_override is not None else float(assumptions["Custo indireto por efetivo"])

    for row in alternatives:
        key = (row["ID_ATIVIDADE"], row["ID_EQUIPE"])
        variable = x_index[key]
        direct_cost = float(row["CUSTO_DIRETO_TOTAL_INDICE"])
        duration = float(row["DURACAO_DIAS"])
        people = float(row["PESSOAS_EQUIPE"])
        objective[variable] = direct_cost + people * duration * ci_person_day
        upper_bounds[variable] = 1.0
        integrality[variable] = 1
    objective[cmax_index] = ci_day
    upper_bounds[cmax_index] = big_m
    for _, _, _, variable in pair_rows:
        upper_bounds[variable] = 1.0
        integrality[variable] = 1

    # O marco OP00 tem início fixo em zero; duração zero e nenhum uso de equipe.
    lower_bounds[s_index["OP00"]] = 0.0
    upper_bounds[s_index["OP00"]] = 0.0

    row_data = []
    col_data = []
    coefficients = []
    row_lb = []
    row_ub = []

    def add_constraint(coefs: dict[int, float], lower: float, upper: float) -> None:
        row_number = len(row_lb)
        for col, value in coefs.items():
            if abs(value) > 1e-12:
                row_data.append(row_number)
                col_data.append(col)
                coefficients.append(value)
        row_lb.append(lower)
        row_ub.append(upper)

    # Cada atividade de execução escolhe exatamente uma equipe habilitada.
    for activity_id in executable_ids:
        coefs = {
            x_index[(activity_id, row["ID_EQUIPE"])]: 1.0
            for row in alternatives_by_activity[activity_id]
        }
        add_constraint(coefs, 1.0, 1.0)

    # Precedências FS e término do projeto; duração é selecionada pela equipe.
    for edge in edges:
        predecessor, successor = edge["PREDECESSORA"], edge["SUCESSORA"]
        coefs = {s_index[predecessor]: 1.0, s_index[successor]: -1.0}
        for row in alternatives_by_activity.get(predecessor, []):
            coefs[x_index[(predecessor, row["ID_EQUIPE"])]] = float(row["DURACAO_DIAS"])
        add_constraint(coefs, -float("inf"), 0.0)

    for activity_id in executable_ids:
        coefs = {s_index[activity_id]: 1.0, cmax_index: -1.0}
        for row in alternatives_by_activity[activity_id]:
            coefs[x_index[(activity_id, row["ID_EQUIPE"])]] = float(row["DURACAO_DIAS"])
        add_constraint(coefs, -float("inf"), 0.0)

    # Para cada par que pode usar o mesmo pool unitário, uma disjunção
    # impede a sobreposição independentemente do perfil/modo escolhido.
    for i, j, pool_id, order_var in pair_rows:
        i_pool_modes = [
            row for row in alternatives_by_activity[i]
            if team_pool[row["ID_EQUIPE"]] == pool_id
        ]
        j_pool_modes = [
            row for row in alternatives_by_activity[j]
            if team_pool[row["ID_EQUIPE"]] == pool_id
        ]
        total_duration_i = {
            x_index[(i, a["ID_EQUIPE"])]: float(a["DURACAO_DIAS"])
            for a in alternatives_by_activity[i]
        }
        total_duration_j = {
            x_index[(j, a["ID_EQUIPE"])]: float(a["DURACAO_DIAS"])
            for a in alternatives_by_activity[j]
        }

        # y=1 força i antes de j quando ambos usam o mesmo pool.
        first = {s_index[i]: 1.0, s_index[j]: -1.0, order_var: big_m}
        for variable, duration in total_duration_i.items():
            first[variable] = first.get(variable, 0.0) + duration
        for row in i_pool_modes + j_pool_modes:
            variable = x_index[(row["ID_ATIVIDADE"], row["ID_EQUIPE"])]
            first[variable] = first.get(variable, 0.0) + big_m
        add_constraint(first, -float("inf"), 3.0 * big_m)

        # y=0 força j antes de i quando ambos usam o mesmo pool.
        second = {s_index[j]: 1.0, s_index[i]: -1.0, order_var: -big_m}
        for variable, duration in total_duration_j.items():
            second[variable] = second.get(variable, 0.0) + duration
        for row in i_pool_modes + j_pool_modes:
            variable = x_index[(row["ID_ATIVIDADE"], row["ID_EQUIPE"])]
            second[variable] = second.get(variable, 0.0) + big_m
        add_constraint(second, -float("inf"), 2.0 * big_m)

    matrix = coo_matrix((coefficients, (row_data, col_data)), shape=(len(row_lb), n_variables)).tocsr()
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(lower_bounds, upper_bounds),
        constraints=LinearConstraint(matrix, row_lb, row_ub),
        options={"time_limit": 60.0, "mip_rel_gap": 1e-9},
    )
    if result.x is None:
        raise SystemExit(f"O solver não encontrou solução viável. status={result.status}; {result.message}")

    choices = {}
    for activity_id in executable_ids:
        selected = [
            row for row in alternatives_by_activity[activity_id]
            if result.x[x_index[(activity_id, row["ID_EQUIPE"])]] > 0.5
        ]
        if len(selected) != 1:
            raise AssertionError(f"A escolha de equipe não é única para {activity_id}: {len(selected)}")
        choices[activity_id] = selected[0]

    starts = {activity_id: float(result.x[s_index[activity_id]]) for activity_id in activity_ids}
    schedule_rows = []
    for activity_id in activity_ids:
        activity = activity_by_id[activity_id]
        selected = choices.get(activity_id)
        duration = float(selected["DURACAO_DIAS"]) if selected else 0.0
        start = starts[activity_id]
        finish = start + duration
        schedule_rows.append(
            {
                "ID_ATIVIDADE": activity_id,
                "DESCRICAO": activity["DESCRICAO"],
                "ID_EQUIPE": selected["ID_EQUIPE"] if selected else "NAO_APLICA",
                "ID_POOL_RECURSO": selected["ID_POOL_RECURSO"] if selected else "NAO_APLICA",
                "PERFIL_EQUIPE": selected["PERFIL_EQUIPE"] if selected else "MARCO",
                "INICIO_DIA": num(start),
                "FIM_DIA": num(finish),
                "DURACAO_DIAS": num(duration),
                "QUANTIDADE": activity["QUANTIDADE"],
                "UNIDADE": activity["UNIDADE"],
                "PRODUTIVIDADE_UNID_DIA": selected["PRODUTIVIDADE_UNID_DIA"] if selected else 0,
                "PESSOAS_EQUIPE": selected["PESSOAS_EQUIPE"] if selected else 0,
                "CUSTO_EQUIPE_DIA_PONTOS_INDICE": selected["CUSTO_EQUIPE_DIA_PONTOS_INDICE"] if selected else 0,
                "CUSTO_MATERIAL_TOTAL_PONTOS_INDICE": selected["CUSTO_MATERIAL_TOTAL_PONTOS_INDICE"] if selected else 0,
                "CUSTO_DIRETO_INDICE": selected["CUSTO_DIRETO_TOTAL_INDICE"] if selected else 0,
                "CUSTO_INDIRETO_EFETIVO_INDICE": (
                    float(selected["PESSOAS_EQUIPE"])
                    * duration
                    * ci_person_day
                    if selected else 0
                ),
            }
        )

    # Verificação independente de precedência e disponibilidade dos pools.
    schedule_by_id = {row["ID_ATIVIDADE"]: row for row in schedule_rows}
    for edge in edges:
        pred = schedule_by_id[edge["PREDECESSORA"]]
        succ = schedule_by_id[edge["SUCESSORA"]]
        if float(pred["FIM_DIA"]) > float(succ["INICIO_DIA"]) + 1e-6:
            raise AssertionError(f"Precedência violada após solução: {edge}")
    by_pool: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    for row in schedule_rows:
        if row["ID_POOL_RECURSO"] != "NAO_APLICA":
            by_pool[row["ID_POOL_RECURSO"]].append(
                (float(row["INICIO_DIA"]), float(row["FIM_DIA"]), row["ID_ATIVIDADE"])
            )
    for pool_id, intervals in by_pool.items():
        intervals.sort()
        for left, right in zip(intervals, intervals[1:]):
            if left[1] > right[0] + 1e-6:
                raise AssertionError(f"Sobreposição no pool {pool_id}: {left[2]} e {right[2]}")

    fixed = sum(float(row["CUSTO_FIXO_PONTOS_INDICE"]) for row in fixed_costs)
    direct = sum(float(row["CUSTO_DIRETO_TOTAL_INDICE"]) for row in choices.values())
    person_days = sum(
        float(row["PESSOAS_EQUIPE"]) * float(row["DURACAO_DIAS"])
        for row in choices.values()
    )
    headcount_indirect = person_days * ci_person_day
    cmax = max(float(row["FIM_DIA"]) for row in schedule_rows)
    time_indirect = cmax * ci_day
    total = fixed + direct + headcount_indirect + time_indirect
    optimized = result.status == 0
    summary = {
        "status_solver": int(result.status),
        "status_texto": str(result.message),
        "otimo_comprovado": optimized,
        "gap_mip": getattr(result, "mip_gap", None),
        "variaveis": n_variables,
        "restricoes": len(row_lb),
        "big_m_dias": num(big_m),
        "prazo_dias_uteis": num(cmax),
        "custo_fixo_uma_vez_indice": num(fixed),
        "custo_direto_equipes_e_materiais_indice": num(direct),
        "custo_indireto_por_prazo_indice": num(time_indirect),
        "custo_indireto_por_efetivo_indice": num(headcount_indirect),
        "efetivo_pessoa_dias": num(person_days),
        "custo_total_indice": num(total),
        "funcao_objetivo_sem_fixo_indice": num(float(result.fun)),
        "restricoes_precedencia": "APROVADAS",
        "restricoes_capacidade": "APROVADAS",
        "unidade_custo": "Pontos de índice sintéticos, sem moeda",
        "metodo": "MRCPSP determinístico com modos alternativos, pools unitários compartilhados e MILP contínuo no tempo (SciPy/HiGHS).",
        "pools_recursos_compartilhados": len(pool_capacity),
        "premissa_capacidade": "Um recurso renovável por família; todos os perfis da família compartilham a capacidade.",
    }
    base = json.loads((data_dir / "resumo_cenario_base.json").read_text(encoding="utf-8"))
    comparison = [
        {
            "CENARIO": "PERT/CPM padrão sem capacidade de recursos",
            "PRAZO_DIAS_UTEIS": base["prazo_cpm_sem_restricao_dias"],
            "CUSTO_FIXO_INDICE": base["custo_fixo_uma_vez"],
            "CUSTO_DIRETO_INDICE": base["custo_direto_equipes_e_materiais"],
            "CUSTO_INDIRETO_PRAZO_INDICE": num(base["prazo_cpm_sem_restricao_dias"] * ci_day),
            "CUSTO_INDIRETO_EFETIVO_INDICE": base["custo_indireto_por_efetivo"],
            "CUSTO_TOTAL_INDICE": num(
                base["custo_fixo_uma_vez"]
                + base["custo_direto_equipes_e_materiais"]
                + base["prazo_cpm_sem_restricao_dias"] * ci_day
                + base["custo_indireto_por_efetivo"]
            ),
            "OBSERVACAO": "Referência lógica sem capacidade; pode sobrepor atividades que usam o mesmo pool.",
        },
        {
            "CENARIO": "Base factível, equipe padrão com capacidade",
            "PRAZO_DIAS_UTEIS": base["prazo_cenario_base_com_equipes_dias"],
            "CUSTO_FIXO_INDICE": base["custo_fixo_uma_vez"],
            "CUSTO_DIRETO_INDICE": base["custo_direto_equipes_e_materiais"],
            "CUSTO_INDIRETO_PRAZO_INDICE": base["custo_indireto_por_prazo"],
            "CUSTO_INDIRETO_EFETIVO_INDICE": base["custo_indireto_por_efetivo"],
            "CUSTO_TOTAL_INDICE": base["custo_total_indice"],
            "OBSERVACAO": "Referência serial factível; modos padrão e pools unitários compartilhados; não é ótima.",
        },
        {
            "CENARIO": "MRCPSP/MILP com escolha de modo e capacidade",
            "PRAZO_DIAS_UTEIS": summary["prazo_dias_uteis"],
            "CUSTO_FIXO_INDICE": summary["custo_fixo_uma_vez_indice"],
            "CUSTO_DIRETO_INDICE": summary["custo_direto_equipes_e_materiais_indice"],
            "CUSTO_INDIRETO_PRAZO_INDICE": summary["custo_indireto_por_prazo_indice"],
            "CUSTO_INDIRETO_EFETIVO_INDICE": summary["custo_indireto_por_efetivo_indice"],
            "CUSTO_TOTAL_INDICE": summary["custo_total_indice"],
            "OBSERVACAO": "Escolha de modo e início otimizados em conjunto; inclui precedências, pools compartilhados e custos indiretos.",
        },
    ]
    if write_outputs:
        write_csv(
            data_dir / "cenario_otimizado.csv",
            schedule_rows,
            [
                "ID_ATIVIDADE", "DESCRICAO", "ID_EQUIPE", "ID_POOL_RECURSO",
                "PERFIL_EQUIPE", "INICIO_DIA", "FIM_DIA", "DURACAO_DIAS",
                "QUANTIDADE", "UNIDADE", "PRODUTIVIDADE_UNID_DIA",
                "PESSOAS_EQUIPE", "CUSTO_EQUIPE_DIA_PONTOS_INDICE",
                "CUSTO_MATERIAL_TOTAL_PONTOS_INDICE", "CUSTO_DIRETO_INDICE",
                "CUSTO_INDIRETO_EFETIVO_INDICE",
            ],
        )
        (data_dir / "resumo_cenario_otimizado.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_csv(
            data_dir / "comparacao_cenarios.csv",
            comparison,
            [
                "CENARIO", "PRAZO_DIAS_UTEIS", "CUSTO_FIXO_INDICE", "CUSTO_DIRETO_INDICE",
                "CUSTO_INDIRETO_PRAZO_INDICE", "CUSTO_INDIRETO_EFETIVO_INDICE",
                "CUSTO_TOTAL_INDICE", "OBSERVACAO",
            ],
        )
        checks_path = data_dir / "verificacoes.json"
        checks = json.loads(checks_path.read_text(encoding="utf-8"))
        checks.update(
            {
                "solver_milp_status": int(result.status),
                "solver_milp_otimo_comprovado": optimized,
                "restricoes_precedencia_cenario_otimizado": "APROVADAS",
                "restricoes_capacidade_cenario_otimizado": "APROVADAS",
                "pools_compartilhados_cenario_otimizado": len(pool_capacity),
                "custo_total_otimizado_indice": num(total),
                "prazo_otimizado_dias": num(cmax),
                "gap_mip": getattr(result, "mip_gap", None),
            }
        )
        checks_path.write_text(
            json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return summary, schedule_rows, {k: v["ID_EQUIPE"] for k, v in choices.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve o piloto MRCPSP/MILP.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    summary, _, choices = solve_model(data_dir=args.data_dir.resolve())
    print(json.dumps({"summary": summary, "choices": choices}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
