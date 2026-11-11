#!/usr/bin/env python
"""Gera recorte independente com tarefas-folha e precedências por setor."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import sys

import gerar_base_otimizacao_piloto as base

DESTINO = Path(__file__).resolve().parent / "dados_modelo_ampliado"

# Precedências de trabalho hipotéticas aplicadas entre tarefas de um mesmo setor.
ANTECESSORAS = {
    "A01": [], "A02": ["A01"], "A03": ["A02"], "A04": ["A02"],
    "A05": ["A04"], "A06": ["A01", "A03"], "A07": ["A06"],
    "A08": ["A06"], "A09": ["A08"], "A10": ["A07", "A08"],
    "A11": ["A06", "A05"], "A12": ["A11"], "A13": ["A09", "A10", "A12"],
    "A14": ["A13", "A05"], "A15": ["A14"], "A16": ["A15"], "A17": ["A16"],
}
POOL = {"A01": "FIN", "A02": "QA", "A03": "QA", "A04": "QA", "A05": "FIN",
        "A06": "TERR", "A07": "DREN", "A08": "TERR", "A09": "TERR",
        "A10": "DREN", "A11": "DREN", "A12": "DREN", "A13": "BASE",
        "A14": "ASF", "A15": "FIN", "A16": "QA", "A17": "FIN"}


def main():
    eap = base.read_csv(base.SOURCE_DIR / "EAP_sintetica.csv")
    pert = {r["ID_ATIVIDADE"]: r for r in base.read_csv(base.SOURCE_DIR / "PERT_CPM_sintetico.csv")}
    candidates = defaultdict(list)
    for row in eap:
        aid = row["ID_ATIVIDADE"]
        if row["TIPO_EAP"] != "ATIVIDADE" or aid in base.FIXED_SOURCE_IDS or aid not in pert:
            continue
        family = row["ARQUETIPO_CPU"]
        for sector in range(1, 5):
            if row["DESCRICAO_SINTETICA"].startswith(f"Setor {sector:02d} —"):
                candidates[sector, family].append(row)

    tasks, links, ids = [], [], {}
    for sector in range(1, 5):
        for family in ANTECESSORAS:
            row = candidates[sector, family][0]
            aid = row["ID_ATIVIDADE"]
            task_id = f"OP{len(tasks) + 1:03d}"
            ids[sector, family] = task_id
            # A unidade de pacote é ilustrativa; não se trata de medição física.
            duration = float(pert[aid]["TE_PERT_DIAS"])
            tasks.append({"id": task_id, "name": row["DESCRICAO_SINTETICA"],
                          "unit": "pacote-modelo", "quantity": 1.0,
                          "family": POOL[family], "std_productivity": 1 / duration,
                          "material_share": 0.30, "source_ids": [aid]})
    for sector in range(1, 5):
        for family, predecessors in ANTECESSORAS.items():
            target = ids[sector, family]
            links.extend((ids[sector, pred], target) for pred in predecessors)
            if not predecessors:
                links.append(("OP00", target))

    source_ids = [task["source_ids"][0] for task in tasks]
    assert len(source_ids) == len(set(source_ids)) == 68
    base.TASKS, base.PRECEDENCES = tasks, links
    sys.argv = [sys.argv[0], "--outdir", str(DESTINO)] + sys.argv[1:]
    base.main()

    # Atualiza as premissas específicas do recorte, sem alterar o piloto original.
    path = DESTINO / "premissas.csv"
    rows = base.read_csv(path)
    for row in rows:
        if row["PARAMETRO"] == "Escopo":
            row["VALOR"] = "Quatro setores hipotéticos, com uma tarefa-folha de cada uma de 17 famílias por setor."
            row["NOTA"] = "68 tarefas discretas mais um marco. O recorte não representa a totalidade da EAP nem uma obra real."
        elif row["PARAMETRO"] == "Quantidade por atividade":
            row["VALOR"] = "Um pacote-modelo por tarefa"
            row["NOTA"] = "Unidade abstrata; a produtividade é calibrada à duração sintética de referência e não representa medição física."
    base.write_csv(path, rows, ["PARAMETRO", "VALOR", "UNIDADE", "TIPO", "NOTA"])
    checks_path = DESTINO / "verificacoes.json"
    checks = json.loads(checks_path.read_text(encoding="utf-8"))
    cpm = base.read_csv(DESTINO / "PERT_CPM_sem_recursos.csv")
    executable = [r for r in cpm if r["ID_ATIVIDADE"] != "OP00"]
    parallel = sum(float(a["ES_DIAS"]) < float(b["EF_DIAS"]) - 1e-7 and
                   float(b["ES_DIAS"]) < float(a["EF_DIAS"]) - 1e-7
                   for i, a in enumerate(executable) for b in executable[i+1:])
    checks.update({"fontes_tarefas_unicas": True, "pares_sobrepostos_no_cpm": parallel,
                   "rede_somente_tarefas_e_marco": True})
    assert parallel > 0
    checks_path.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Pares simultâneos no CPM: {parallel}")


if __name__ == "__main__":
    main()
