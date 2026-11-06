#!/usr/bin/env python
"""Gera um recorte sintético e reproduzível para otimização tempo-custo."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict, deque
from pathlib import Path


THREAD_DIR = Path(__file__).resolve().parent
WORKSPACE = THREAD_DIR.parents[1]
SOURCE_DIR = WORKSPACE / "dados_simulados/eap_academica_sintetica_escala_exemplo"
DATA_DIR = THREAD_DIR / "dados_modelo"

HOURS_PER_DAY = 8.0
HOURS_PER_MONTH = 180.0
WORKDAYS_PER_MONTH = HOURS_PER_MONTH / HOURS_PER_DAY
INDIRECT_PER_DAY = 0.20
INDIRECT_PER_PERSON_DAY = 0.005
PERT_LOW_FACTOR = 0.80
PERT_HIGH_FACTOR = 1.20

PROFILE = {
    "BAIXA": {
        "label": "Baixa produtividade",
        "productivity_factor": 0.75,
        "daily_cost_factor": 0.80,
        "headcount_rank": 0,
    },
    "PADRAO": {
        "label": "Padrão",
        "productivity_factor": 1.00,
        "daily_cost_factor": 1.00,
        "headcount_rank": 1,
    },
    "RAPIDA": {
        "label": "Alta produtividade",
        "productivity_factor": 1.50,
        "daily_cost_factor": 1.80,
        "headcount_rank": 2,
    },
}

FAMILY = {
    "TERR": {
        "name": "Terraplenagem e escavação",
        "headcounts": [4, 6, 8],
    },
    "DREN": {
        "name": "Drenagem e estruturas hidráulicas",
        "headcounts": [3, 5, 7],
    },
    "BASE": {
        "name": "Base granular",
        "headcounts": [4, 6, 8],
    },
    "ASF": {
        "name": "Pavimentação asfáltica",
        "headcounts": [6, 9, 12],
    },
    "FIN": {
        "name": "Acabamentos e sinalização",
        "headcounts": [3, 5, 7],
    },
    "QA": {
        "name": "Inspeção e ensaios",
        "headcounts": [2, 3, 4],
    },
}

# As quantidades e produtividades do recorte são premissas acadêmicas novas.
# Os IDs de origem servem apenas para rastrear os pacotes e pontos de índice.
TASKS = [
    {
        "id": "OP01",
        "name": "Limpar e remover material superficial",
        "unit": "m2",
        "quantity": 12000.0,
        "family": "TERR",
        "std_productivity": 6000.0,
        "material_share": 0.10,
        "source_ids": ["AT-00213"],
    },
    {
        "id": "OP02",
        "name": "Escavar travessia de drenagem",
        "unit": "m",
        "quantity": 120.0,
        "family": "TERR",
        "std_productivity": 30.0,
        "material_share": 0.25,
        "source_ids": ["AT-00313"],
    },
    {
        "id": "OP03",
        "name": "Preparar berço de assentamento",
        "unit": "m",
        "quantity": 120.0,
        "family": "DREN",
        "std_productivity": 40.0,
        "material_share": 0.35,
        "source_ids": ["AT-00314"],
    },
    {
        "id": "OP04",
        "name": "Assentar tubo transversal",
        "unit": "m",
        "quantity": 120.0,
        "family": "DREN",
        "std_productivity": 30.0,
        "material_share": 0.45,
        "source_ids": ["AT-00315"],
    },
    {
        "id": "OP05",
        "name": "Executar proteção da saída",
        "unit": "m",
        "quantity": 120.0,
        "family": "DREN",
        "std_productivity": 60.0,
        "material_share": 0.55,
        "source_ids": ["AT-00316"],
    },
    {
        "id": "OP06",
        "name": "Executar corte e transporte de solo",
        "unit": "m3",
        "quantity": 6000.0,
        "family": "TERR",
        "std_productivity": 1000.0,
        "material_share": 0.20,
        "source_ids": ["AT-00413", "AT-00433"],
    },
    {
        "id": "OP07",
        "name": "Distribuir material de aterro",
        "unit": "m3",
        "quantity": 5000.0,
        "family": "TERR",
        "std_productivity": 1250.0,
        "material_share": 0.40,
        "source_ids": ["AT-00434"],
    },
    {
        "id": "OP08",
        "name": "Regularizar e compactar o subleito",
        "unit": "m2",
        "quantity": 12000.0,
        "family": "TERR",
        "std_productivity": 4000.0,
        "material_share": 0.15,
        "source_ids": ["AT-00647", "AT-00649"],
    },
    {
        "id": "OP09",
        "name": "Produzir, transportar e executar base granular",
        "unit": "m3",
        "quantity": 1800.0,
        "family": "BASE",
        "std_productivity": 450.0,
        "material_share": 0.60,
        "source_ids": ["AT-01056", "AT-01057", "AT-01058", "AT-01002"],
    },
    {
        "id": "OP10",
        "name": "Produzir, transportar e aplicar revestimento asfáltico",
        "unit": "t",
        "quantity": 900.0,
        "family": "ASF",
        "std_productivity": 225.0,
        "material_share": 0.68,
        "source_ids": ["AT-01176", "AT-01146", "AT-01147", "AT-01122"],
    },
    {
        "id": "OP11",
        "name": "Implantar defensa e sinalização",
        "unit": "m",
        "quantity": 1200.0,
        "family": "FIN",
        "std_productivity": 240.0,
        "material_share": 0.75,
        "source_ids": ["AT-01277", "AT-01278", "AT-01279"],
    },
    {
        "id": "OP12",
        "name": "Inspecionar e executar ensaios de recebimento",
        "unit": "lote",
        "quantity": 1.0,
        "family": "QA",
        "std_productivity": 0.5,
        "material_share": 0.20,
        "source_ids": ["AT-01338", "AT-01339"],
    },
]

PRECEDENCES = [
    ("OP00", "OP01"),
    ("OP01", "OP02"),
    ("OP01", "OP06"),
    ("OP02", "OP03"),
    ("OP03", "OP04"),
    ("OP04", "OP05"),
    ("OP06", "OP07"),
    ("OP07", "OP08"),
    ("OP05", "OP09"),
    ("OP08", "OP09"),
    ("OP09", "OP10"),
    ("OP10", "OP11"),
    ("OP11", "OP12"),
]

FIXED_SOURCE_IDS = ["AT-00001", "AT-00002"]


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


def topological_sort(activity_ids: list[str], edges: list[tuple[str, str]]) -> list[str]:
    incoming = {activity_id: 0 for activity_id in activity_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for predecessor, successor in edges:
        if predecessor not in incoming or successor not in incoming:
            raise ValueError(f"Precedência com atividade desconhecida: {predecessor}->{successor}")
        outgoing[predecessor].append(successor)
        incoming[successor] += 1
    ready = deque(activity_id for activity_id in activity_ids if incoming[activity_id] == 0)
    order = []
    while ready:
        activity_id = ready.popleft()
        order.append(activity_id)
        for successor in outgoing[activity_id]:
            incoming[successor] -= 1
            if incoming[successor] == 0:
                ready.append(successor)
    if len(order) != len(activity_ids):
        raise ValueError("A rede de precedências possui ciclo.")
    return order


def compute_cpm(activity_rows: list[dict], edges: list[tuple[str, str]]) -> list[dict]:
    activities = {row["ID_ATIVIDADE"]: row for row in activity_rows}
    ids = list(activities)
    order = topological_sort(ids, edges)
    preds: dict[str, list[str]] = defaultdict(list)
    succs: dict[str, list[str]] = defaultdict(list)
    for predecessor, successor in edges:
        preds[successor].append(predecessor)
        succs[predecessor].append(successor)
    es, ef = {}, {}
    for activity_id in order:
        es[activity_id] = max((ef[p] for p in preds[activity_id]), default=0.0)
        duration = float(activities[activity_id]["DURACAO_PADRAO_DIAS"])
        ef[activity_id] = es[activity_id] + duration
    finish = max(ef.values(), default=0.0)
    lf, ls = {}, {}
    for activity_id in reversed(order):
        lf[activity_id] = min((ls[s] for s in succs[activity_id]), default=finish)
        duration = float(activities[activity_id]["DURACAO_PADRAO_DIAS"])
        ls[activity_id] = lf[activity_id] - duration
    rows = []
    for activity_id in order:
        activity = activities[activity_id]
        duration = float(activity["DURACAO_PADRAO_DIAS"])
        slack = max(0.0, ls[activity_id] - es[activity_id])
        rows.append(
            {
                "ID_ATIVIDADE": activity_id,
                "DESCRICAO": activity["DESCRICAO"],
                "EQUIPE_FIXADA": "SEM_RESTRICAO_DE_RECURSO" if activity["TIPO"] == "EXECUCAO" else "MARCO",
                "DURACAO_DIAS": num(duration),
                "O_DIAS": num(duration * PERT_LOW_FACTOR),
                "M_DIAS": num(duration),
                "P_DIAS": num(duration * PERT_HIGH_FACTOR),
                "TE_PERT_DIAS": num((duration * PERT_LOW_FACTOR + 4 * duration + duration * PERT_HIGH_FACTOR) / 6),
                "ES_DIAS": num(es[activity_id]),
                "EF_DIAS": num(ef[activity_id]),
                "LS_DIAS": num(ls[activity_id]),
                "LF_DIAS": num(lf[activity_id]),
                "FOLGA_DIAS": num(slack),
                "CRITICA": "SIM" if slack <= 1e-7 else "NAO",
                "OBSERVACAO": "CPM lógico sem capacidade de recursos; não é cronograma executável.",
            }
        )
    return rows


def schedule_fixed_assignment(
    activity_rows: list[dict],
    edges: list[tuple[str, str]],
    alternatives: list[dict],
    teams: list[dict],
    resources: list[dict],
) -> list[dict]:
    activities = {row["ID_ATIVIDADE"]: row for row in activity_rows}
    standard = {
        row["ID_ATIVIDADE"]: row
        for row in alternatives
        if row["PERFIL_EQUIPE"] == "PADRAO"
    }
    pool_by_team = {row["ID_EQUIPE"]: row["ID_POOL_RECURSO"] for row in teams}
    capacity = {row["ID_POOL_RECURSO"]: int(row["DISPONIBILIDADE"]) for row in resources}
    preds: dict[str, list[str]] = defaultdict(list)
    for predecessor, successor in edges:
        preds[successor].append(predecessor)
    order = topological_sort(list(activities), edges)
    booked: dict[str, list[tuple[float, float, int]]] = defaultdict(list)
    schedule = []
    for activity_id in order:
        activity = activities[activity_id]
        if activity["TIPO"] == "MARCO":
            start = 0.0
            duration = 0.0
            finish = 0.0
            selected = None
        else:
            selected = standard[activity_id]
            start = max((next(r["FIM_DIA"] for r in schedule if r["ID_ATIVIDADE"] == p) for p in preds[activity_id]), default=0.0)
            duration = float(selected["DURACAO_DIAS"])
            team_id = selected["ID_EQUIPE"]
            pool_id = pool_by_team[team_id]
            cap = capacity[pool_id]
            if cap != 1:
                raise ValueError("O gerador do cenário base requer disponibilidade unitária por pool.")
            intervals = booked[pool_id]
            while True:
                conflicts = [
                    (begin, end, count)
                    for begin, end, count in intervals
                    if start < end - 1e-9 and start + duration > begin + 1e-9
                ]
                if not conflicts:
                    break
                start = min(end for _, end, _ in conflicts)
            finish = start + duration
            intervals.append((start, finish, 1))
        schedule.append(
            {
                "ID_ATIVIDADE": activity_id,
                "DESCRICAO": activity["DESCRICAO"],
                "ID_EQUIPE": selected["ID_EQUIPE"] if selected else "NAO_APLICA",
                "ID_POOL_RECURSO": pool_by_team[selected["ID_EQUIPE"]] if selected else "NAO_APLICA",
                "PERFIL_EQUIPE": selected["PERFIL_EQUIPE"] if selected else "MARCO",
                "INICIO_DIA": num(start),
                "FIM_DIA": num(finish),
                "DURACAO_DIAS": num(duration),
                "QUANTIDADE": activity["QUANTIDADE"],
                "UNIDADE": activity["UNIDADE"],
                "PRODUTIVIDADE_UNID_DIA": selected["PRODUTIVIDADE_UNID_DIA"] if selected else 0,
                "PESSOAS_EQUIPE": selected["PESSOAS_EQUIPE"] if selected else 0,
                "CUSTO_DIRETO_INDICE": selected["CUSTO_DIRETO_TOTAL_INDICE"] if selected else 0,
                "CUSTO_INDIRETO_EFETIVO_INDICE": selected["CUSTO_INDIRETO_EFETIVO_INDICE"] if selected else 0,
            }
        )
    return schedule


def assert_schedule_feasible(
    schedule: list[dict], edges: list[tuple[str, str]], resources: list[dict]
) -> None:
    rows = {row["ID_ATIVIDADE"]: row for row in schedule}
    for predecessor, successor in edges:
        if float(rows[predecessor]["FIM_DIA"]) > float(rows[successor]["INICIO_DIA"]) + 1e-7:
            raise AssertionError(f"Precedência violada: {predecessor}->{successor}")
    caps = {row["ID_POOL_RECURSO"]: int(row["DISPONIBILIDADE"]) for row in resources}
    by_pool: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in schedule:
        pool_id = row["ID_POOL_RECURSO"]
        if pool_id not in caps:
            continue
        by_pool[pool_id].append((float(row["INICIO_DIA"]), float(row["FIM_DIA"])))
    for pool_id, intervals in by_pool.items():
        for i, (start_i, end_i) in enumerate(intervals):
            overlaps = sum(
                1
                for j, (start_j, end_j) in enumerate(intervals)
                if i != j and start_i < end_j - 1e-7 and end_i > start_j + 1e-7
            )
            if overlaps >= caps[pool_id]:
                raise AssertionError(f"Capacidade violada para o pool {pool_id}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=DATA_DIR)
    parser.add_argument("--force", action="store_true", help="Permite substituir os arquivos gerados nesta pasta.")
    args = parser.parse_args()
    outdir = args.outdir.resolve()
    if outdir.exists() and any(outdir.iterdir()) and not args.force:
        raise SystemExit(f"A pasta já contém arquivos; use --force para regenerar: {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)

    if not SOURCE_DIR.exists():
        raise SystemExit(f"Não encontrei a EAP sintética de referência: {SOURCE_DIR}")
    eap_rows = read_csv(SOURCE_DIR / "EAP_sintetica.csv")
    pert_rows = read_csv(SOURCE_DIR / "PERT_CPM_sintetico.csv")
    eap_by_code = {row["COD_EAP"]: row for row in eap_rows}
    pert_by_id = {row["ID_ATIVIDADE"]: row for row in pert_rows}

    source_lookup = {}
    for source_id, pert in pert_by_id.items():
        eap = eap_by_code.get(pert["COD_EAP"])
        if eap:
            source_lookup[source_id] = {
                "COD_EAP": pert["COD_EAP"],
                "DESCRICAO_ORIGEM": pert["ATIVIDADE_SINTETICA"],
                "CLASSIFICACAO": pert["CLASSIFICACAO"],
                "PONTOS": float(eap["PONTOS_CUSTO_INDICE"]),
                "UNIDADE": eap["UNIDADE_MODELO"],
                "QUANTIDADE": eap["QUANTIDADE_MODELO"],
            }
            if abs(float(pert["PONTOS_CUSTO_INDICE"]) - source_lookup[source_id]["PONTOS"]) > 0.011:
                raise AssertionError(f"Custo EAP/PERT divergente em {source_id}.")

    missing = sorted(
        source_id
        for source_id in FIXED_SOURCE_IDS + [sid for task in TASKS for sid in task["source_ids"]]
        if source_id not in source_lookup
    )
    if missing:
        raise SystemExit(f"Atividades de origem ausentes na EAP: {missing}")

    activity_rows = [
        {
            "ID_ATIVIDADE": "OP00",
            "DESCRICAO": "Marco de mobilização concluída",
            "TIPO": "MARCO",
            "CLASSIFICACAO": "INDIRETA",
            "UNIDADE": "marco",
            "QUANTIDADE": 0,
            "FAMILIA_EQUIPE": "NAO_APLICA",
            "IDS_ATIVIDADE_EAP_ORIGEM": ",".join(FIXED_SOURCE_IDS),
            "CODIGOS_EAP_ORIGEM": ",".join(source_lookup[s]["COD_EAP"] for s in FIXED_SOURCE_IDS),
            "DESCRICOES_EAP_ORIGEM": " | ".join(source_lookup[s]["DESCRICAO_ORIGEM"] for s in FIXED_SOURCE_IDS),
            "PONTOS_CUSTO_EAP_ORIGEM": num(sum(source_lookup[s]["PONTOS"] for s in FIXED_SOURCE_IDS)),
            "PARTICIPACAO_MATERIAL_PREMISSA": 0,
            "PRODUTIVIDADE_PADRAO_UNID_DIA": 0,
            "DURACAO_PADRAO_DIAS": 0,
            "O_PADRAO_DIAS": 0,
            "M_PADRAO_DIAS": 0,
            "P_PADRAO_DIAS": 0,
            "TE_PERT_PADRAO_DIAS": 0,
            "OBSERVACAO": "Marco sem duração; os pontos de origem estão em custos_fixos.csv e são somados uma vez.",
        }
    ]

    alternatives = []
    teams = []
    fixed_cost_rows = []
    for idx, source_id in enumerate(FIXED_SOURCE_IDS, start=1):
        source = source_lookup[source_id]
        fixed_cost_rows.append(
            {
                "ID_CUSTO_FIXO": f"FIX{idx:02d}",
                "DESCRICAO": source["DESCRICAO_ORIGEM"],
                "ID_ATIVIDADE_EAP_ORIGEM": source_id,
                "COD_EAP_ORIGEM": source["COD_EAP"],
                "CLASSIFICACAO_ORIGEM": source["CLASSIFICACAO"],
                "CUSTO_FIXO_PONTOS_INDICE": num(source["PONTOS"]),
                "REPETICAO": "UMA_VEZ",
                "TRATAMENTO": "Incluído uma única vez; excluído dos custos de equipe e da taxa diária.",
            }
        )

    for task in TASKS:
        source_cost = sum(source_lookup[s]["PONTOS"] for s in task["source_ids"])
        source_classes = {source_lookup[s]["CLASSIFICACAO"] for s in task["source_ids"]}
        if task["id"] != "OP12" and source_classes != {"DIRETA"}:
            raise AssertionError(f"Classificação inesperada em {task['id']}: {source_classes}")
        if task["id"] == "OP12" and source_classes != {"DUVIDA"}:
            raise AssertionError(f"A inspeção deveria conservar a classificação em dúvida: {source_classes}")
        std_duration = task["quantity"] / task["std_productivity"]
        eap_codes = [source_lookup[s]["COD_EAP"] for s in task["source_ids"]]
        activity_rows.append(
            {
                "ID_ATIVIDADE": task["id"],
                "DESCRICAO": task["name"],
                "TIPO": "EXECUCAO",
                "CLASSIFICACAO": "DUVIDA" if task["id"] == "OP12" else "DIRETA",
                "UNIDADE": task["unit"],
                "QUANTIDADE": num(task["quantity"]),
                "FAMILIA_EQUIPE": task["family"],
                "IDS_ATIVIDADE_EAP_ORIGEM": ",".join(task["source_ids"]),
                "CODIGOS_EAP_ORIGEM": ",".join(eap_codes),
                "DESCRICOES_EAP_ORIGEM": " | ".join(
                    source_lookup[s]["DESCRICAO_ORIGEM"] for s in task["source_ids"]
                ),
                "PONTOS_CUSTO_EAP_ORIGEM": num(source_cost),
                "PARTICIPACAO_MATERIAL_PREMISSA": task["material_share"],
                "PRODUTIVIDADE_PADRAO_UNID_DIA": num(task["std_productivity"]),
                "DURACAO_PADRAO_DIAS": num(std_duration),
                "O_PADRAO_DIAS": num(std_duration * PERT_LOW_FACTOR),
                "M_PADRAO_DIAS": num(std_duration),
                "P_PADRAO_DIAS": num(std_duration * PERT_HIGH_FACTOR),
                "TE_PERT_PADRAO_DIAS": num(
                    (std_duration * PERT_LOW_FACTOR + 4 * std_duration + std_duration * PERT_HIGH_FACTOR) / 6
                ),
                "OBSERVACAO": "Quantidade, produtividade e participação material são premissas sintéticas do recorte.",
            }
        )
        material_total = source_cost * task["material_share"]
        crew_equipment_total_std = source_cost - material_total
        crew_equipment_day_std = crew_equipment_total_std / std_duration

        for profile_key, profile in PROFILE.items():
            family_meta = FAMILY[task["family"]]
            rank = profile["headcount_rank"]
            team_id = f"{task['family']}_{profile_key}"
            if not any(row["ID_EQUIPE"] == team_id for row in teams):
                teams.append(
                    {
                        "ID_EQUIPE": team_id,
                        "ID_POOL_RECURSO": task["family"],
                        "FAMILIA": task["family"],
                        "DESCRICAO_FAMILIA": family_meta["name"],
                        "PERFIL": profile["label"],
                        "MULTIPLICADOR_PRODUTIVIDADE": profile["productivity_factor"],
                        "MULTIPLICADOR_CUSTO_DIARIO": profile["daily_cost_factor"],
                        "PESSOAS_POR_EQUIPE": family_meta["headcounts"][rank],
                        "HORAS_POR_DIA": HOURS_PER_DAY,
                        "REGRA_MODO": "Alternativa de formação/produtividade; usa o pool compartilhado da família.",
                    }
                )
            productivity = task["std_productivity"] * profile["productivity_factor"]
            duration = task["quantity"] / productivity
            crew_day_cost = crew_equipment_day_std * profile["daily_cost_factor"]
            crew_equipment_cost = crew_day_cost * duration
            direct_cost = material_total + crew_equipment_cost
            headcount = family_meta["headcounts"][rank]
            headcount_cost = headcount * duration * INDIRECT_PER_PERSON_DAY
            o = duration * PERT_LOW_FACTOR
            m = duration
            p = duration * PERT_HIGH_FACTOR
            alternatives.append(
                {
                    "ID_ATIVIDADE": task["id"],
                    "ID_EQUIPE": team_id,
                    "ID_POOL_RECURSO": task["family"],
                    "FAMILIA": task["family"],
                    "PERFIL_EQUIPE": profile_key,
                    "HABILITADA": "SIM",
                    "QUANTIDADE": num(task["quantity"]),
                    "UNIDADE": task["unit"],
                    "PRODUTIVIDADE_UNID_DIA": num(productivity),
                    "DURACAO_DIAS": num(duration),
                    "O_DIAS": num(o),
                    "M_DIAS": num(m),
                    "P_DIAS": num(p),
                    "TE_PERT_DIAS": num((o + 4 * m + p) / 6),
                    "PESSOAS_EQUIPE": headcount,
                    "CUSTO_EQUIPE_DIA_PONTOS_INDICE": num(crew_day_cost),
                    "CUSTO_EQUIPE_HORA_PONTOS_INDICE": num(crew_day_cost / HOURS_PER_DAY),
                    "CUSTO_MATERIAL_UNITARIO_PONTOS_INDICE": num(material_total / task["quantity"]),
                    "CUSTO_MATERIAL_TOTAL_PONTOS_INDICE": num(material_total),
                    "CUSTO_DIRETO_TOTAL_INDICE": num(direct_cost),
                    "CUSTO_DIRETO_FONTE_EAP_INDICE": num(source_cost),
                    "DIF_DIRETO_VS_EAP_INDICE": num(direct_cost - source_cost),
                    "CUSTO_INDIRETO_EFETIVO_INDICE": num(headcount_cost),
                    "PREMISSA_DE_CUSTO": "Equipe = mão de obra + equipamento por dia; material variável separado.",
                }
            )

    activity_columns = list(activity_rows[0])
    edge_rows = [
        {
            "PREDECESSORA": predecessor,
            "SUCESSORA": successor,
            "RELACAO": "FS",
            "LAG_DIAS": 0,
            "PREMISSA": "Precedência acadêmica definida para este recorte; não copiada da EAP como vínculo hierárquico.",
        }
        for predecessor, successor in PRECEDENCES
    ]
    team_columns = list(teams[0])
    alternative_columns = list(alternatives[0])
    fixed_columns = list(fixed_cost_rows[0])

    resource_rows = [
        {
            "ID_POOL_RECURSO": family_id,
            "FAMILIA": family_id,
            "DESCRICAO_RECURSO": FAMILY[family_id]["name"],
            "DISPONIBILIDADE": 1,
            "UNIDADE_CAPACIDADE": "equipe",
            "REGRA_CAPACIDADE": "Capacidade unitária compartilhada entre todos os perfis/modos desta família.",
            "PREMISSA": "Um conjunto de equipe e equipamento disponível por família no piloto sintético.",
        }
        for family_id in sorted({row["FAMILIA"] for row in teams})
    ]

    premise_rows = [
        {"PARAMETRO": "Fonte estrutural", "VALOR": "EAP acadêmica sintética ampliada", "UNIDADE": "referência", "TIPO": "origem", "NOTA": "Usada apenas para mapear IDs/códigos e pontos de índice; não contém dados identificáveis da obra."},
        {"PARAMETRO": "Escopo", "VALOR": "Um segmento hipotético de infraestrutura linear associado ao setor 04 da EAP de referência.", "UNIDADE": "descrição", "TIPO": "fronteira", "NOTA": "12 atividades discretas de limpeza, drenagem, terraplenagem, base, revestimento, sinalização e inspeção, mais um marco de mobilização. Não representa o S11D nem o cronograma integral."},
        {"PARAMETRO": "Horas por dia útil", "VALOR": HOURS_PER_DAY, "UNIDADE": "h/dia", "TIPO": "calendário", "NOTA": "Jornada de referência para converter custo diário em custo horário."},
        {"PARAMETRO": "Horas por mês", "VALOR": HOURS_PER_MONTH, "UNIDADE": "h/mês", "TIPO": "calendário", "NOTA": "Mantém a premissa usada no histograma anterior."},
        {"PARAMETRO": "Dias úteis equivalentes por mês", "VALOR": WORKDAYS_PER_MONTH, "UNIDADE": "dia útil/mês", "TIPO": "calendário", "NOTA": "180 horas divididas por 8 horas/dia; não define datas civis ou feriados."},
        {"PARAMETRO": "Quantidade por atividade", "VALOR": "Premissa por pacote", "UNIDADE": "unidades listadas em atividades.csv", "TIPO": "quantidade", "NOTA": "As quantidades do recorte são novas e hipotéticas; a quantidade 1 dos nós-folha da EAP de escala não é tratada como medição."},
        {"PARAMETRO": "Duração alternativa", "VALOR": "quantidade / produtividade da habilitação", "UNIDADE": "dias úteis", "TIPO": "cálculo", "NOTA": "Duração contínua; sem arredondamento para dia inteiro."},
        {"PARAMETRO": "Pontos O/M/P", "VALOR": "O=0,80×d; M=d; P=1,20×d", "UNIDADE": "dias úteis", "TIPO": "PERT", "NOTA": "Faixa simétrica hipotética; TE=(O+4M+P)/6=d. A matriz usa TE de cada equipe."},
        {"PARAMETRO": "Multiplicadores produtividade", "VALOR": "Baixa=0,75; Padrão=1,00; Alta=1,50", "UNIDADE": "× padrão", "TIPO": "equipe", "NOTA": "Hipóteses didáticas, não produtividades SINAPI nem produtividade da obra."},
        {"PARAMETRO": "Multiplicadores custo de equipe/dia", "VALOR": "Baixa=0,80; Padrão=1,00; Alta=1,80", "UNIDADE": "× padrão", "TIPO": "custo direto", "NOTA": "Custo da equipe por dia inclui mão de obra e equipamento; escala sintética para criar trade-off tempo-custo."},
        {"PARAMETRO": "Alocação material", "VALOR": "Participação por atividade registrada em atividades.csv", "UNIDADE": "% do custo-base", "TIPO": "custo direto", "NOTA": "Premissa sintética. O material varia com quantidade e é separado do custo diário de equipe."},
        {"PARAMETRO": "Custo indireto por prazo", "VALOR": INDIRECT_PER_DAY, "UNIDADE": "pontos de índice/dia útil", "TIPO": "indireto por prazo", "NOTA": "Administração/canteiro por dia; não contém salário e equipamento da equipe de execução."},
        {"PARAMETRO": "Custo indireto por efetivo", "VALOR": INDIRECT_PER_PERSON_DAY, "UNIDADE": "pontos de índice/pessoa-dia", "TIPO": "indireto por efetivo", "NOTA": "Apoio individual (ex.: alimentação e itens pessoais); calculado como pessoas/equipe × duração. Não repete salários."},
        {"PARAMETRO": "Pool de recurso compartilhado", "VALOR": 1, "UNIDADE": "equipe por família", "TIPO": "capacidade", "NOTA": "Os modos/perfis de uma família consomem o mesmo pool renovável; no máximo uma atividade dessa família por vez."},
        {"PARAMETRO": "Formação de equipe", "VALOR": "Um modo por atividade", "UNIDADE": "modo", "TIPO": "decisão", "NOTA": "Cada atividade escolhe exatamente uma formação/produtividade habilitada. Múltiplas equipes simultâneas na mesma atividade não são modeladas."},
        {"PARAMETRO": "Recursos compartilhados", "VALOR": "Pools TERR, DREN, BASE, ASF, FIN e QA", "UNIDADE": "pool", "TIPO": "recurso renovável", "NOTA": "Cada perfil selecionado ocupa uma unidade do pool da família durante toda a atividade; todos os perfis da família compartilham a mesma capacidade."},
        {"PARAMETRO": "Custo fixo", "VALOR": "Soma de FIX01 e FIX02", "UNIDADE": "pontos de índice/projeto", "TIPO": "fixo", "NOTA": "Mobilização de apoio ancorada nos pontos sintéticos da EAP; adicionada uma vez e fora da taxa por dia."},
        {"PARAMETRO": "Unidade de custo", "VALOR": "Pontos de índice sintéticos", "UNIDADE": "sem moeda", "TIPO": "restrição de uso", "NOTA": "Não são reais, valores SINAPI ou custos de obra; não monetizar sem calibração separada."},
        {"PARAMETRO": "Precedências", "VALOR": "Relações FS listadas em precedencias.csv", "UNIDADE": "rede lógica", "TIPO": "rede", "NOTA": "A hierarquia EAP é estrutura de custos, não predecessora. As relações do piloto são premissas próprias."},
        {"PARAMETRO": "Cenário CPM", "VALOR": "Equipe padrão e precedências, sem restrição de disponibilidade", "UNIDADE": "dias úteis", "TIPO": "referência", "NOTA": "Serve como baseline de rede; não é cronograma executável sob limite de equipes."},
        {"PARAMETRO": "Cenário RCPSP", "VALOR": "Alocação e início sujeitos às capacidades de equipes", "UNIDADE": "dias úteis", "TIPO": "referência", "NOTA": "O cenário padrão usa uma heurística factível; o arquivo otimizado é calculado separadamente pelo solver."},
    ]

    cpm = compute_cpm(activity_rows, PRECEDENCES)
    base_schedule = schedule_fixed_assignment(activity_rows, PRECEDENCES, alternatives, teams, resource_rows)
    assert_schedule_feasible(base_schedule, PRECEDENCES, resource_rows)
    alternatives_by_key = {(r["ID_ATIVIDADE"], r["PERFIL_EQUIPE"]): r for r in alternatives}
    for row in alternatives:
        if row["PERFIL_EQUIPE"] == "PADRAO":
            if abs(float(row["CUSTO_DIRETO_TOTAL_INDICE"]) - float(row["CUSTO_DIRETO_FONTE_EAP_INDICE"])) > 1e-7:
                raise AssertionError(f"Custo padrão não concilia com EAP em {row['ID_ATIVIDADE']}.")

    source_direct = sum(float(row["PONTOS_CUSTO_EAP_ORIGEM"]) for row in activity_rows if row["TIPO"] == "EXECUCAO")
    standard_direct = sum(
        float(alternatives_by_key[(row["ID_ATIVIDADE"], "PADRAO")]["CUSTO_DIRETO_TOTAL_INDICE"])
        for row in activity_rows
        if row["TIPO"] == "EXECUCAO"
    )
    fixed_total = sum(float(row["CUSTO_FIXO_PONTOS_INDICE"]) for row in fixed_cost_rows)
    cpm_finish = max(float(row["EF_DIAS"]) for row in cpm)
    base_finish = max(float(row["FIM_DIA"]) for row in base_schedule)
    base_direct = sum(float(row["CUSTO_DIRETO_INDICE"]) for row in base_schedule)
    base_headcount_indirect = sum(float(row["CUSTO_INDIRETO_EFETIVO_INDICE"]) for row in base_schedule)
    base_time_indirect = base_finish * INDIRECT_PER_DAY

    conciliation = []
    for activity in activity_rows:
        if activity["TIPO"] != "EXECUCAO":
            continue
        standard = alternatives_by_key[(activity["ID_ATIVIDADE"], "PADRAO")]
        conciliation.append(
            {
                "ID_ATIVIDADE": activity["ID_ATIVIDADE"],
                "IDS_ATIVIDADE_EAP_ORIGEM": activity["IDS_ATIVIDADE_EAP_ORIGEM"],
                "CUSTO_PONTOS_EAP_ORIGEM": activity["PONTOS_CUSTO_EAP_ORIGEM"],
                "CUSTO_DIRETO_EQUIPE_PADRAO": standard["CUSTO_DIRETO_TOTAL_INDICE"],
                "DIFERENCA": num(float(standard["CUSTO_DIRETO_TOTAL_INDICE"]) - float(activity["PONTOS_CUSTO_EAP_ORIGEM"])),
                "STATUS": "RECONCILIADO" if abs(float(standard["CUSTO_DIRETO_TOTAL_INDICE"]) - float(activity["PONTOS_CUSTO_EAP_ORIGEM"])) <= 1e-7 else "PENDENTE",
            }
        )

    checks = {
        "status": "APROVADO",
        "atividades_execucao": len(TASKS),
        "marcos": 1,
        "precedencias_fs": len(PRECEDENCES),
        "habilitacoes": len(alternatives),
        "equipes_perfil": len(teams),
        "pools_recursos_compartilhados": len(resource_rows),
        "capacidade_unitaria_por_pool": all(int(row["DISPONIBILIDADE"]) == 1 for row in resource_rows),
        "rede_acyclic": True,
        "fonte_ids_presentes": len(FIXED_SOURCE_IDS) + sum(len(t["source_ids"]) for t in TASKS),
        "conflitos_de_capacidade_cenario_base": 0,
        "violacoes_precedencia_cenario_base": 0,
        "duracoes_q_div_p_reconciliadas": all(
            abs(
                float(row["DURACAO_DIAS"])
                - float(row["QUANTIDADE"]) / float(row["PRODUTIVIDADE_UNID_DIA"])
            )
            <= 1e-7
            for row in alternatives
        ),
        "direto_padrao_reconciliado_com_eap": abs(standard_direct - source_direct) <= 1e-7,
        "custo_fixo_anclado_eap_pontos_indice": num(fixed_total),
        "direto_eap_pontos_indice_atividades": num(source_direct),
        "cpm_sem_recursos_dias": num(cpm_finish),
        "cen_base_com_recursos_dias": num(base_finish),
        "prazo_rc_maior_ou_igual_cpm": base_finish + 1e-7 >= cpm_finish,
        "custo_faixa_e_moeda": "Pontos de índice sintéticos; sem R$.",
    }

    base_rows = base_schedule
    summary = {
        "tipo": "cenário-base factível; não é ótimo",
        "regra": "Equipe padrão em todas as atividades; início mais cedo respeitando precedências e um pool unitário compartilhado por família.",
        "prazo_cpm_sem_restricao_dias": num(cpm_finish),
        "prazo_cenario_base_com_equipes_dias": num(base_finish),
        "custo_fixo_uma_vez": num(fixed_total),
        "custo_direto_equipes_e_materiais": num(base_direct),
        "custo_indireto_por_prazo": num(base_time_indirect),
        "custo_indireto_por_efetivo": num(base_headcount_indirect),
        "custo_total_indice": num(fixed_total + base_direct + base_time_indirect + base_headcount_indirect),
        "unidade": "pontos de índice sintéticos, sem moeda",
    }

    write_csv(outdir / "atividades.csv", activity_rows, activity_columns)
    write_csv(
        outdir / "precedencias.csv",
        edge_rows,
        ["PREDECESSORA", "SUCESSORA", "RELACAO", "LAG_DIAS", "PREMISSA"],
    )
    write_csv(outdir / "equipes.csv", teams, team_columns)
    write_csv(outdir / "recursos_compartilhados.csv", resource_rows, list(resource_rows[0]))
    write_csv(outdir / "habilitacoes_alternativas.csv", alternatives, alternative_columns)
    write_csv(outdir / "custos_fixos.csv", fixed_cost_rows, fixed_columns)
    write_csv(
        outdir / "premissas.csv",
        premise_rows,
        ["PARAMETRO", "VALOR", "UNIDADE", "TIPO", "NOTA"],
    )
    write_csv(
        outdir / "PERT_CPM_sem_recursos.csv",
        cpm,
        [
            "ID_ATIVIDADE", "DESCRICAO", "EQUIPE_FIXADA", "DURACAO_DIAS", "O_DIAS", "M_DIAS", "P_DIAS",
            "TE_PERT_DIAS", "ES_DIAS", "EF_DIAS", "LS_DIAS", "LF_DIAS", "FOLGA_DIAS", "CRITICA", "OBSERVACAO",
        ],
    )
    write_csv(
        outdir / "cenario_base_com_equipes.csv",
        base_rows,
        [
            "ID_ATIVIDADE", "DESCRICAO", "ID_EQUIPE", "ID_POOL_RECURSO", "PERFIL_EQUIPE", "INICIO_DIA", "FIM_DIA",
            "DURACAO_DIAS", "QUANTIDADE", "UNIDADE", "PRODUTIVIDADE_UNID_DIA", "PESSOAS_EQUIPE",
            "CUSTO_DIRETO_INDICE", "CUSTO_INDIRETO_EFETIVO_INDICE",
        ],
    )
    write_csv(
        outdir / "conciliacao_custos.csv",
        conciliation,
        [
            "ID_ATIVIDADE", "IDS_ATIVIDADE_EAP_ORIGEM", "CUSTO_PONTOS_EAP_ORIGEM",
            "CUSTO_DIRETO_EQUIPE_PADRAO", "DIFERENCA", "STATUS",
        ],
    )
    (outdir / "verificacoes.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (outdir / "resumo_cenario_base.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"data_dir": str(outdir), "checks": checks, "scenario": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
