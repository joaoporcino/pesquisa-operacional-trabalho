#!/usr/bin/env python
"""Otimização tempo-custo do piloto acadêmico com a API nativa do Gurobi."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

ROOT = Path(__file__).resolve().parent


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def number(value, label):
    try:
        n = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{label}: valor numérico inválido: {value!r}") from exc
    if not math.isfinite(n) or n < 0:
        raise ValueError(f"{label}: esperado número finito não negativo")
    return n


def solve(data_dir, output_dir, deadline=None, time_limit=60, gap=1e-9):
    activities = read(data_dir / "atividades.csv")
    edges = read(data_dir / "precedencias.csv")
    teams = read(data_dir / "equipes.csv")
    resources = read(data_dir / "recursos_compartilhados.csv")
    modes = read(data_dir / "habilitacoes_alternativas.csv")
    fixed = read(data_dir / "custos_fixos.csv")
    assumptions = {r["PARAMETRO"]: r["VALOR"] for r in read(data_dir / "premissas.csv")}
    ct = number(assumptions["Custo indireto por prazo"], "custo indireto por prazo")
    ch = number(assumptions["Custo indireto por efetivo"], "custo indireto por efetivo")
    cf = sum(number(r["CUSTO_FIXO_PONTOS_INDICE"], "custo fixo") for r in fixed)
    ids = [r["ID_ATIVIDADE"] for r in activities]
    if len(set(ids)) != len(ids) or "OP00" not in ids:
        raise ValueError("IDs de atividades duplicados ou marco OP00 ausente")
    if any(r["TIPO"] not in {"EXECUCAO", "MARCO"} for r in activities):
        raise ValueError("Tipo de atividade desconhecido")
    executable = [r["ID_ATIVIDADE"] for r in activities if r["TIPO"] == "EXECUCAO"]
    pool = {r["ID_EQUIPE"]: r["ID_POOL_RECURSO"] for r in teams}
    capacities = {r["ID_POOL_RECURSO"]: number(r["DISPONIBILIDADE"], "capacidade") for r in resources}
    if len(pool) != len(teams) or len(capacities) != len(resources) or any(v != 1 for v in capacities.values()):
        raise ValueError("Equipes/pools duplicados ou capacidade diferente de 1")
    by_activity = defaultdict(list)
    indexed = {}
    for row in modes:
        i, e = row["ID_ATIVIDADE"], row["ID_EQUIPE"]
        if row["HABILITADA"].upper() != "SIM":
            continue
        if i not in executable or e not in pool or pool[e] not in capacities or row["ID_POOL_RECURSO"] != pool[e] or (i, e) in indexed:
            raise ValueError(f"Alternativa inválida ou duplicada: {i}, {e}")
        for field in ("DURACAO_DIAS", "PESSOAS_EQUIPE", "CUSTO_DIRETO_TOTAL_INDICE"):
            number(row[field], f"{i}/{e}/{field}")
        if float(row["DURACAO_DIAS"]) <= 0:
            raise ValueError(f"Duração deve ser positiva: {i}/{e}")
        indexed[i, e] = row
        by_activity[i].append(e)
    if any(not by_activity[i] for i in executable):
        raise ValueError("Existe atividade sem alternativa habilitada")
    for edge in edges:
        if edge["PREDECESSORA"] not in ids or edge["SUCESSORA"] not in ids or edge["PREDECESSORA"] == edge["SUCESSORA"]:
            raise ValueError(f"Precedência inválida: {edge}")

    # A soma das durações máximas limita um cronograma serial viável para rede acíclica.
    horizon = sum(max(float(indexed[i, e]["DURACAO_DIAS"]) for e in by_activity[i]) for i in executable) + 1
    model = gp.Model("menor_custo_obra_piloto")
    model.Params.TimeLimit = time_limit
    model.Params.MIPGap = gap
    x = model.addVars(list(indexed), vtype=GRB.BINARY, name="modo")
    start = model.addVars(ids, lb=0, ub=horizon, name="inicio")
    end = model.addVar(lb=0, ub=horizon, name="prazo")
    model.addConstr(start["OP00"] == 0, name="marco_inicial")
    duration = {i: gp.quicksum(float(indexed[i, e]["DURACAO_DIAS"]) * x[i, e] for e in by_activity[i]) for i in ids}
    for i in executable:
        model.addConstr(gp.quicksum(x[i, e] for e in by_activity[i]) == 1, name=f"escolha_{i}")
    for k, edge in enumerate(edges):
        i, j = edge["PREDECESSORA"], edge["SUCESSORA"]
        model.addConstr(start[i] + duration[i] <= start[j], name=f"precedencia_{k}")
    for i in ids:
        model.addConstr(start[i] + duration[i] <= end, name=f"termino_{i}")
    for r in capacities:
        eligible = [i for i in executable if any(pool[e] == r for e in by_activity[i])]
        for i, j in combinations(eligible, 2):
            zi = gp.quicksum(x[i, e] for e in by_activity[i] if pool[e] == r)
            zj = gp.quicksum(x[j, e] for e in by_activity[j] if pool[e] == r)
            order = model.addVar(vtype=GRB.BINARY, name=f"ordem_{r}_{i}_{j}")
            model.addConstr(start[i] + duration[i] <= start[j] + horizon * (3 - zi - zj - order))
            model.addConstr(start[j] + duration[j] <= start[i] + horizon * (2 - zi - zj + order))
    if deadline is not None:
        model.addConstr(end <= deadline, name="prazo_limite")
    direct = gp.quicksum(float(row["CUSTO_DIRETO_TOTAL_INDICE"]) * x[i, e] for (i, e), row in indexed.items())
    person_days = gp.quicksum(float(row["PESSOAS_EQUIPE"]) * float(row["DURACAO_DIAS"]) * x[i, e] for (i, e), row in indexed.items())
    model.setObjective(cf + direct + ch * person_days + ct * end, GRB.MINIMIZE)
    model.optimize()
    if model.SolCount == 0:
        raise RuntimeError(f"Gurobi não encontrou solução viável; status={model.Status}. Verifique prazo e dados.")
    chosen = {i: indexed[i, next(e for e in by_activity[i] if x[i, e].X > .5)] for i in executable}
    schedule = []
    for row in activities:
        i = row["ID_ATIVIDADE"]
        choice = chosen.get(i)
        d = float(choice["DURACAO_DIAS"]) if choice else 0.0
        schedule.append({"ID_ATIVIDADE": i, "DESCRICAO": row["DESCRICAO"], "ID_EQUIPE": choice["ID_EQUIPE"] if choice else "NAO_APLICA", "ID_POOL_RECURSO": choice["ID_POOL_RECURSO"] if choice else "NAO_APLICA", "INICIO_DIA": start[i].X, "FIM_DIA": start[i].X + d, "DURACAO_DIAS": d, "CUSTO_DIRETO_INDICE": float(choice["CUSTO_DIRETO_TOTAL_INDICE"]) if choice else 0, "CUSTO_INDIRETO_EFETIVO_INDICE": float(choice["PESSOAS_EQUIPE"]) * d * ch if choice else 0})
    lookup = {r["ID_ATIVIDADE"]: r for r in schedule}
    for edge in edges:
        if lookup[edge["PREDECESSORA"]]["FIM_DIA"] > lookup[edge["SUCESSORA"]]["INICIO_DIA"] + 1e-6:
            raise AssertionError(f"Precedência violada: {edge}")
    for r in capacities:
        intervals = sorted((v["INICIO_DIA"], v["FIM_DIA"], v["ID_ATIVIDADE"]) for v in schedule if v["ID_POOL_RECURSO"] == r)
        if any(a[1] > b[0] + 1e-6 for a, b in zip(intervals, intervals[1:])):
            raise AssertionError(f"Sobreposição no pool {r}")
    actual_end = max(v["FIM_DIA"] for v in schedule)
    if deadline is not None and actual_end > deadline + 1e-6:
        raise AssertionError("Prazo limite violado")
    summary = {"status_gurobi": model.Status, "otimo_comprovado": model.Status == GRB.OPTIMAL, "gap_mip": model.MIPGap, "limite_inferior_objetivo": model.ObjBound, "variaveis": model.NumVars, "restricoes": model.NumConstrs, "prazo_dias_uteis": actual_end, "custo_fixo_indice": cf, "custo_direto_indice": direct.getValue(), "custo_indireto_prazo_indice": ct * actual_end, "custo_indireto_efetivo_indice": ch * person_days.getValue(), "custo_total_indice": cf + direct.getValue() + ct * actual_end + ch * person_days.getValue(), "objetivo_solver_indice": model.ObjVal, "prazo_limite_dias": deadline, "verificacao_precedencias_e_capacidade": "APROVADA", "unidade": "pontos de índice sintéticos, sem moeda"}
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "cronograma_gurobi.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=schedule[0].keys(), delimiter=";")
        writer.writeheader()
        writer.writerows(schedule)
    (output_dir / "resumo_gurobi.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "dados_modelo")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "resultados_gurobi")
    parser.add_argument("--prazo-maximo", type=float, help="Prazo máximo em dias úteis")
    parser.add_argument("--tempo-limite", type=float, default=60, help="Tempo máximo do solver em segundos")
    parser.add_argument("--gap", type=float, default=1e-9, help="Tolerância relativa de otimalidade")
    args = parser.parse_args()
    for name, value in (("prazo máximo", args.prazo_maximo), ("tempo limite", args.tempo_limite), ("gap", args.gap)):
        if value is not None:
            number(value, name)
    if args.tempo_limite == 0:
        parser.error("O tempo limite deve ser positivo")
    try:
        result = solve(args.data_dir, args.output_dir, args.prazo_maximo, args.tempo_limite, args.gap)
    except (ValueError, RuntimeError, gp.GurobiError) as exc:
        parser.exit(1, f"Erro: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
