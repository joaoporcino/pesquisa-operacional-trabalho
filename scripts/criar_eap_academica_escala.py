"""Gera uma EAP acadêmica sintética em escala comparável ao exemplo.

O script não lê nenhum dado do projeto. A estrutura é criada com atividades
genéricas; os parâmetros de tamanho (1.849 nós, 1.399 folhas, 450 agrupadores)
foram definidos para atender ao pedido de escala. Valores, quantidades, datas,
descrições e dependências são hipotéticos.

Uso: python scripts/criar_eap_academica_escala.py
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "dados_simulados/eap_academica_sintetica_escala_exemplo"
D = Decimal


def fmt(value: Decimal, places: int = 2) -> str:
    quantum = Decimal("1").scaleb(-places)
    return format(value.quantize(quantum, rounding=ROUND_HALF_UP), f".{places}f")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0]), delimiter=";", lineterminator="\r\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


# 19 famílias de atividade do caso-base. Os orçamentos por família somam 1.000
# pontos de índice e são subdivididos em tarefas novas, sem origem na obra.
FAMILIES: dict[str, dict[str, Any]] = {
    "A01": {"name": "Mobilização e instalações provisórias", "class": "INDIRETA", "budget": 20, "count": 30, "phase": 1, "unit": "PACOTE", "deliverable": "Canteiro e acessos de apoio disponíveis", "duration": (1, 2, 4), "pred": [], "variants": ["Preparar área de apoio", "Montar módulo temporário", "Liberar utilidades provisórias", "Organizar acesso da frente"]},
    "A02": {"name": "Levantamentos topográficos e geotécnicos", "class": "DUVIDA", "budget": 10, "count": 25, "phase": 1, "unit": "HA", "deliverable": "Dados de campo e investigações registrados", "duration": (1, 2, 4), "pred": ["A01"], "variants": ["Implantar pontos de controle", "Levantar faixa de implantação", "Investigar condição do subsolo", "Consolidar registro de campo"]},
    "A03": {"name": "Autorizações e liberação de frentes", "class": "INDIRETA", "budget": 10, "count": 20, "phase": 1, "unit": "PACOTE", "deliverable": "Áreas liberadas para execução", "duration": (1, 2, 4), "pred": ["A02"], "variants": ["Preparar documentação de liberação", "Validar acesso à área", "Registrar condicionantes de execução", "Emitir termo de liberação"]},
    "A04": {"name": "Projeto executivo e construtibilidade", "class": "INDIRETA", "budget": 25, "count": 45, "phase": 1, "unit": "PACOTE", "deliverable": "Detalhes técnicos liberados para construção", "duration": (2, 3, 5), "pred": ["A02"], "variants": ["Detalhar solução executiva", "Compatibilizar interfaces", "Revisar sequência construtiva", "Emitir desenho para campo"]},
    "A05": {"name": "Aquisição de materiais de prazo longo", "class": "DUVIDA", "budget": 40, "count": 80, "phase": 1, "unit": "UN", "deliverable": "Materiais críticos disponíveis", "duration": (2, 4, 7), "pred": ["A04"], "variants": ["Confirmar especificação de fornecimento", "Emitir pedido de material", "Inspecionar recebimento", "Liberar lote para uso"]},
    "A06": {"name": "Limpeza e acessos provisórios", "class": "DIRETA", "budget": 40, "count": 80, "phase": 2, "unit": "M2", "deliverable": "Área de trabalho preparada", "duration": (1, 2, 3), "pred": ["A01", "A03"], "variants": ["Limpar área de trabalho", "Preparar acesso temporário", "Organizar área de estocagem", "Remover material superficial"]},
    "A07": {"name": "Drenagem transversal", "class": "DIRETA", "budget": 70, "count": 100, "phase": 2, "unit": "M", "deliverable": "Travessias de drenagem instaladas", "duration": (1, 2, 4), "pred": ["A06"], "variants": ["Escavar travessia", "Preparar berço de assentamento", "Assentar tubo transversal", "Executar proteção de saída"]},
    "A08": {"name": "Cortes, aterros e conformação", "class": "DIRETA", "budget": 200, "count": 219, "phase": 2, "unit": "M3", "deliverable": "Plataforma conformada", "duration": (1, 2, 4), "pred": ["A06"], "variants": ["Executar corte de material", "Carregar e transportar solo", "Distribuir material de aterro", "Conformar plataforma"]},
    "A09": {"name": "Preparação do subleito", "class": "DIRETA", "budget": 65, "count": 80, "phase": 2, "unit": "M2", "deliverable": "Subleito preparado e compactado", "duration": (1, 2, 3), "pred": ["A08"], "variants": ["Regularizar superfície", "Ajustar umidade", "Compactar camada", "Verificar condição do subleito"]},
    "A10": {"name": "Drenagem longitudinal", "class": "DIRETA", "budget": 65, "count": 100, "phase": 2, "unit": "M", "deliverable": "Dispositivos longitudinais instalados", "duration": (1, 2, 4), "pred": ["A07", "A08"], "variants": ["Escavar vala longitudinal", "Instalar elemento drenante", "Executar enchimento filtrante", "Conectar saída de drenagem"]},
    "A11": {"name": "Fundações e contenções", "class": "DIRETA", "budget": 95, "count": 100, "phase": 2, "unit": "M3", "deliverable": "Fundações e contenções executadas", "duration": (2, 3, 5), "pred": ["A06", "A05"], "variants": ["Preparar base de fundação", "Montar armadura", "Executar concretagem", "Conferir elemento de contenção"]},
    "A12": {"name": "Estruturas de concreto ou metálicas", "class": "DIRETA", "budget": 80, "count": 110, "phase": 3, "unit": "M3", "deliverable": "Estruturas concluídas", "duration": (2, 4, 6), "pred": ["A11", "A05"], "variants": ["Montar elemento estrutural", "Instalar armadura ou ligação", "Concretar ou fixar estrutura", "Inspecionar geometria do elemento"]},
    "A13": {"name": "Sub-base e base granular", "class": "DIRETA", "budget": 70, "count": 120, "phase": 3, "unit": "M3", "deliverable": "Camadas granulares executadas", "duration": (1, 2, 4), "pred": ["A09", "A10", "A12"], "variants": ["Produzir mistura de base", "Transportar material granular", "Espalhar camada", "Compactar camada granular"]},
    "A14": {"name": "Revestimento e superfície de rolamento", "class": "DIRETA", "budget": 90, "count": 120, "phase": 3, "unit": "T", "deliverable": "Superfície de rolamento executada", "duration": (1, 2, 3), "pred": ["A13", "A05"], "variants": ["Produzir mistura asfáltica", "Transportar mistura", "Aplicar camada de revestimento", "Compactar superfície"]},
    "A15": {"name": "Sinalização, defensas e acabamentos", "class": "DIRETA", "budget": 35, "count": 80, "phase": 4, "unit": "M", "deliverable": "Itens de segurança e acabamento instalados", "duration": (1, 2, 4), "pred": ["A14"], "variants": ["Instalar defensa", "Implantar sinalização vertical", "Executar marcação horizontal", "Concluir arremate do trecho"]},
    "A16": {"name": "Inspeções e correções", "class": "DUVIDA", "budget": 25, "count": 40, "phase": 4, "unit": "LOTE", "deliverable": "Verificações concluídas e pendências tratadas", "duration": (1, 2, 3), "pred": ["A15"], "variants": ["Inspecionar serviço concluído", "Executar ensaio de recebimento", "Registrar pendência", "Verificar correção executada"]},
    "A17": {"name": "Entrega e desmobilização", "class": "INDIRETA", "budget": 15, "count": 30, "phase": 5, "unit": "PACOTE", "deliverable": "Infraestrutura entregue e estruturas provisórias removidas", "duration": (1, 2, 3), "pred": ["A16"], "variants": ["Preparar documentação final", "Entregar área ao operador", "Retirar instalação provisória", "Encerrar registro da frente"]},
    "A18": {"name": "Planejamento, controles e supervisão", "class": "INDIRETA", "budget": 30, "count": 10, "phase": 1, "unit": "MES", "deliverable": "Acompanhamento integrado mantido", "duration": None, "pred": [], "variants": ["Atualizar programação", "Consolidar medição de avanço", "Coordenar interface de campo", "Emitir relatório de controle"]},
    "A19": {"name": "Segurança, meio ambiente e qualidade", "class": "INDIRETA", "budget": 15, "count": 10, "phase": 1, "unit": "MES", "deliverable": "Controles de segurança, ambiente e qualidade ativos", "duration": None, "pred": [], "variants": ["Realizar inspeção preventiva", "Acompanhar controle ambiental", "Verificar qualidade de execução", "Orientar equipe da frente"]},
}

PHASE_NAMES = {
    1: "Preparação, mobilização e engenharia",
    2: "Preparação física, terraplenagem e drenagem",
    3: "Estruturas, bases e revestimentos",
    4: "Segurança, inspeção e acabamento",
    5: "Entrega e encerramento",
}
ACCOUNT_LABELS = {
    1: ["Apoio e mobilização", "Levantamentos", "Engenharia e liberações", "Suprimentos", "Gestão contínua"],
    2: ["Acessos e limpeza", "Movimentação de terra", "Subleito", "Dispositivos de drenagem", "Fundações e contenções"],
    3: ["Estruturas", "Camadas granulares", "Revestimento", "Interfaces construtivas", "Controle de execução"],
    4: ["Defensas e sinalização", "Inspeções", "Correções", "Acabamentos", "Aceitação técnica"],
    5: ["Entrega", "Documentação", "Desmobilização", "Encerramento administrativo", "Fechamento de frentes"],
}

FAMILY_GROUPS: dict[str, list[dict[str, Any]]] = defaultdict(list)
FAMILY_TASKS: dict[str, list[dict[str, Any]]] = defaultdict(list)
ACTIVITY_PREDECESSORS: dict[str, list[str]] = {
    "A01": [], "A02": ["A01"], "A03": ["A02"], "A04": ["A02"], "A05": ["A04"],
    "A06": ["A01", "A03"], "A07": ["A06"], "A08": ["A06"], "A09": ["A08"],
    "A10": ["A07", "A08"], "A11": ["A06", "A05"], "A12": ["A11", "A05"],
    "A13": ["A09", "A10", "A12"], "A14": ["A13", "A05"], "A15": ["A14"],
    "A16": ["A15"], "A17": ["A16"],
}
EXPECTED_NODES = 1849
EXPECTED_LEAVES = 1399
EXPECTED_PARENTS = 450
EXPECTED_WORK_PACKAGES = 419


def allocate_group_counts() -> dict[str, int]:
    counts = {key: int(value["count"]) for key, value in FAMILIES.items()}
    minimum = {key: (n + 3) // 4 for key, n in counts.items()}
    maximum = {key: n // 3 for key, n in counts.items()}
    if sum(minimum.values()) > EXPECTED_WORK_PACKAGES or sum(maximum.values()) < EXPECTED_WORK_PACKAGES:
        raise ValueError("A escala de pacotes não permite grupos de três ou quatro atividades.")
    allocation = dict(minimum)
    while sum(allocation.values()) < EXPECTED_WORK_PACKAGES:
        candidates = [key for key in counts if allocation[key] < maximum[key]]
        chosen = max(candidates, key=lambda key: D(counts[key]) / D(allocation[key]))
        allocation[chosen] += 1
    return allocation


def allocate_task_costs(family: str, count: int) -> list[Decimal]:
    total_cents = int(D(FAMILIES[family]["budget"]) * 100)
    base, remainder = divmod(total_cents, count)
    return [D(base + (1 if i < remainder else 0)) / 100 for i in range(count)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera uma EAP acadêmica sintética em grande escala.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Pasta de saída nova.")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"A pasta de saída já existe; escolha outra: {output}")

    nodes: list[dict[str, Any]] = []
    nodes.append({"code": "0", "parent": "", "level": 0, "type": "PROJETO", "name": "Projeto acadêmico de infraestrutura linear", "activity": "", "family": "", "unit": "", "qty": "", "class": "AGRUPADOR", "network": "NAO_AGRUPADOR", "deliverable": "Infraestrutura hipotética pronta para operação"})
    account_codes: dict[tuple[int, int], str] = {}
    package_counts = allocate_group_counts()
    for phase in range(1, 6):
        phase_code = str(phase)
        nodes.append({"code": phase_code, "parent": "0", "level": 1, "type": "FASE", "name": PHASE_NAMES[phase], "activity": "", "family": "", "unit": "", "qty": "", "class": "AGRUPADOR", "network": "NAO_AGRUPADOR", "deliverable": "Entregas da fase hipotética concluídas"})
        for account_no, label in enumerate(ACCOUNT_LABELS[phase], start=1):
            account_code = f"{phase}.{account_no}"
            account_codes[(phase, account_no)] = account_code
            nodes.append({"code": account_code, "parent": phase_code, "level": 2, "type": "CONTA_CONTROLE", "name": f"{label} — frente {account_no:02d}", "activity": "", "family": "", "unit": "", "qty": "", "class": "AGRUPADOR", "network": "NAO_AGRUPADOR", "deliverable": f"Escopo da frente {account_no:02d} liberado"})

    family_package_serial: dict[str, int] = defaultdict(int)
    account_package_serial: dict[tuple[int, int], int] = defaultdict(int)
    next_activity = 1
    activity_by_id: dict[str, dict[str, Any]] = {}
    group_serial_by_family: dict[str, int] = defaultdict(int)
    group_counts = allocate_group_counts()

    for family, spec in FAMILIES.items():
        count = int(spec["count"])
        group_count = group_counts[family]
        base, remainder = divmod(count, group_count)
        task_costs = allocate_task_costs(family, count)
        task_position = 0
        for group_index in range(group_count):
            group_size = base + (1 if group_index < remainder else 0)
            group_serial_by_family[family] += 1
            family_package_serial[family] += 1
            sector = (group_index % 5) + 1
            phase = int(spec["phase"])
            account_code = account_codes[(phase, sector)]
            account_package_serial[(phase, sector)] += 1
            package_no = account_package_serial[(phase, sector)]
            package_code = f"{account_code}.{package_no}"
            package_name = f"{spec['name']} — setor {sector:02d}, pacote {family_package_serial[family]:03d}"
            group = {"family": family, "phase": phase, "sector": sector, "code": package_code, "tasks": [], "index": group_index}
            FAMILY_GROUPS[family].append(group)
            nodes.append({"code": package_code, "parent": account_code, "level": 3, "type": "PACOTE_TRABALHO", "name": package_name, "activity": "", "family": family, "unit": "", "qty": "", "class": "AGRUPADOR", "network": "NAO_AGRUPADOR", "deliverable": spec["deliverable"]})
            for step in range(1, group_size + 1):
                activity_id = f"AT-{next_activity:05d}"
                next_activity += 1
                task_code = f"{package_code}.{step}"
                variant = spec["variants"][(task_position + group_index) % len(spec["variants"])]
                task_name = f"Setor {sector:02d} — pacote {family_package_serial[family]:03d} — {variant}"
                is_loe = spec["duration"] is None
                points = task_costs[task_position]
                task_position += 1
                task = {
                    "id": activity_id,
                    "wbs": task_code,
                    "family": family,
                    "group": group,
                    "name": task_name,
                    "class": spec["class"],
                    "cost": points,
                    "unit": spec["unit"],
                    "qty": D("1"),
                    "loe": is_loe,
                    "o": spec["duration"][0] if not is_loe else None,
                    "m": spec["duration"][1] if not is_loe else None,
                    "p": spec["duration"][2] if not is_loe else None,
                    "pred": [],
                    "successors": [],
                    "mode": "ATIVIDADE",
                }
                group["tasks"].append(task)
                FAMILY_TASKS[family].append(task)
                activity_by_id[activity_id] = task
                nodes.append({"code": task_code, "parent": package_code, "level": 4, "type": "ATIVIDADE_LOE" if is_loe else "ATIVIDADE", "name": task_name, "activity": activity_id, "family": family, "unit": spec["unit"], "qty": "1", "class": spec["class"], "network": "NAO_LOE" if is_loe else "SIM", "deliverable": spec["deliverable"], "cost": points})
        if task_position != count:
            raise ValueError(f"A contagem de tarefas da família {family} divergiu.")

    # Liga os grupos por sequência interna e pelas precedências hipotéticas da rede.
    start_id, finish_id = "M00", "M99"
    dependencies: set[tuple[str, str]] = set()
    for family, groups in FAMILY_GROUPS.items():
        if FAMILIES[family]["duration"] is None:
            continue
        for group in groups:
            tasks = group["tasks"]
            for before, after in zip(tasks, tasks[1:]):
                dependencies.add((before["id"], after["id"]))
                after["pred"].append(before["id"])
                before["successors"].append(after["id"])
            first = tasks[0]
            family_preds = ACTIVITY_PREDECESSORS[family]
            if not family_preds:
                dependencies.add((start_id, first["id"]))
                first["pred"].append(start_id)
            else:
                same_sector_groups = {family: defaultdict(list) for family in family_preds}
                for pred_family in family_preds:
                    for candidate in FAMILY_GROUPS[pred_family]:
                        same_sector_groups[pred_family][candidate["sector"]].append(candidate)
                for pred_family in family_preds:
                    candidates = same_sector_groups[pred_family].get(group["sector"], [])
                    if not candidates:
                        candidates = FAMILY_GROUPS[pred_family]
                    numerator = group["index"] * max(0, len(candidates) - 1)
                    denominator = max(1, len(groups) - 1)
                    candidate_index = min(len(candidates) - 1, (numerator + denominator // 2) // denominator)
                    pred_task = candidates[candidate_index]["tasks"][-1]
                    dependencies.add((pred_task["id"], first["id"]))
                    first["pred"].append(pred_task["id"])
                    pred_task["successors"].append(first["id"])

    terminal_tasks = [group["tasks"][-1] for group in FAMILY_GROUPS["A17"]]
    for task in terminal_tasks:
        dependencies.add((task["id"], finish_id))
        task["successors"].append(finish_id)
    milestones = {
        start_id: {"id": start_id, "wbs": "", "name": "Marco de início", "class": "NAO_APLICA", "pred": [], "successors": [succ for pred, succ in dependencies if pred == start_id], "o": 0, "m": 0, "p": 0, "cost": D(0), "mode": "MARCO"},
        finish_id: {"id": finish_id, "wbs": "", "name": "Marco de conclusão", "class": "NAO_APLICA", "pred": [pred for pred, succ in dependencies if succ == finish_id], "successors": [], "o": 0, "m": 0, "p": 0, "cost": D(0), "mode": "MARCO"},
    }

    network = [milestones[start_id]] + [task for task in activity_by_id.values() if not task["loe"]] + [milestones[finish_id]]
    network_by_id = {task["id"]: task for task in network}
    successors: dict[str, list[str]] = defaultdict(list)
    for pred, succ in dependencies:
        successors[pred].append(succ)
    ordered: list[dict[str, Any]] = []
    completed: set[str] = set()
    while len(ordered) < len(network):
        ready = [task for task in network if task["id"] not in completed and all(pred in completed for pred in task["pred"])]
        if not ready:
            raise ValueError("A rede PERT/CPM ficou cíclica ou tem predecessora ausente.")
        for task in ready:
            if task["mode"] != "MARCO":
                task["te"] = (D(task["o"]) + D(4) * D(task["m"]) + D(task["p"])) / D(6)
            else:
                task["te"] = D(0)
            task["es"] = max((network_by_id[pred]["ef"] for pred in task["pred"]), default=D(0))
            task["ef"] = task["es"] + task["te"]
            completed.add(task["id"])
            ordered.append(task)
    duration = milestones[finish_id]["ef"]
    for task in reversed(ordered):
        task["lf"] = min((network_by_id[succ]["ls"] for succ in successors[task["id"]]), default=duration)
        task["ls"] = task["lf"] - task["te"]
        task["float"] = task["ls"] - task["es"]
        task["critical"] = abs(task["float"]) < D("0.000001")

    parent_children: dict[str, list[str]] = defaultdict(list)
    points_by_code: dict[str, Decimal] = {}
    for node in nodes:
        if node["parent"]:
            parent_children[node["parent"]].append(node["code"])
        if node.get("activity"):
            points_by_code[node["code"]] = node["cost"]
    for node in reversed(nodes):
        if node["code"] not in points_by_code:
            points_by_code[node["code"]] = sum((points_by_code[child] for child in parent_children[node["code"]]), D(0))
    if len(nodes) != EXPECTED_NODES or sum(1 for node in nodes if node.get("activity")) != EXPECTED_LEAVES:
        raise ValueError(f"Tamanho inesperado: {len(nodes)} nós e {sum(bool(n.get('activity')) for n in nodes)} folhas.")
    if len(nodes) - EXPECTED_LEAVES != EXPECTED_PARENTS:
        raise ValueError("A quantidade de agrupadores divergiu do modelo de escala.")
    if points_by_code["0"] != D(1000):
        raise ValueError(f"A EAP precisa totalizar 1.000 pontos; calculado={points_by_code['0']}.")

    eap_rows = []
    for node in nodes:
        eap_rows.append({
            "COD_EAP": node["code"], "COD_PAI": node["parent"], "NIVEL": node["level"],
            "TIPO_EAP": node["type"], "DESCRICAO_SINTETICA": node["name"],
            "CLASSIFICACAO": node["class"], "ID_ATIVIDADE": node.get("activity", ""),
            "INCLUI_REDE_PERT_CPM": node["network"], "PONTOS_CUSTO_INDICE": fmt(points_by_code[node["code"]]),
            "ENTREGA": node["deliverable"], "ARQUETIPO_CPU": node.get("family", ""),
            "UNIDADE_MODELO": node.get("unit", ""), "QUANTIDADE_MODELO": node.get("qty", ""),
        })

    schedule_rows = []
    for task in ordered:
        schedule_rows.append({
            "ID_ATIVIDADE": task["id"], "COD_EAP": task["wbs"], "ATIVIDADE_SINTETICA": task["name"],
            "CLASSIFICACAO": task["class"], "PREDECESSORAS_FS": ",".join(task["pred"]),
            "O_DIAS_UTEIS": task["o"], "M_DIAS_UTEIS": task["m"], "P_DIAS_UTEIS": task["p"],
            "TE_PERT_DIAS": fmt(task["te"]), "ES_DIAS": fmt(task["es"]), "EF_DIAS": fmt(task["ef"]),
            "LS_DIAS": fmt(task["ls"]), "LF_DIAS": fmt(task["lf"]), "FOLGA_DIAS": fmt(task["float"]),
            "CRITICA": "SIM" if task["critical"] else "NAO", "PONTOS_CUSTO_INDICE": fmt(task["cost"]),
            "TIPO": "MARCO" if task.get("mode") == "MARCO" else "ATIVIDADE",
        })
    dependency_rows = [
        {"PREDECESSORA": pred, "SUCESSORA": succ, "RELACAO": "FS", "LAG_DIAS": 0,
         "PREMISSA": "Precedência hipotética do modelo acadêmico"}
        for pred, succ in sorted(dependencies)
    ]

    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "EAP_sintetica.csv", eap_rows)
    write_csv(output / "PERT_CPM_sintetico.csv", schedule_rows)
    write_csv(output / "dependencias_sinteticas.csv", dependency_rows)
    report = {
        "tipo_de_dados": "EAP acadêmica inteiramente sintética; não consulta dados do projeto",
        "referencia_de_escala": "Somente quantidade agregada de nós, folhas e agrupadores; sem descrições, custos, atividades ou relações do projeto",
        "numero_de_nos_eap": len(nodes),
        "numero_de_agrupadores": EXPECTED_PARENTS,
        "numero_de_atividades_folha": EXPECTED_LEAVES,
        "numero_de_atividades_discretas_pert_cpm": sum(not task["loe"] for task in activity_by_id.values()),
        "numero_de_pacotes_loe": sum(task["loe"] for task in activity_by_id.values()),
        "numero_de_marcos_pert_cpm": 2,
        "numero_de_dependencias_fs": len(dependency_rows),
        "total_custo_pontos_indice": fmt(points_by_code["0"]),
        "duracao_esperada_projeto_dias_uteis": fmt(duration),
        "atividades_criticas": sum(1 for task in network if task["critical"] and task["mode"] != "MARCO"),
        "premissas": [
            "O modelo usa 19 famílias genéricas de serviços, segmentadas em frentes e pacotes hipotéticos.",
            "Quantidades-modelo, atividades, descrições, coeficientes sintéticos, custos-índice, durações e precedências foram criados para o estudo.",
            "A classificação direta/indireta/em dúvida é didática e requer critério definido pelo curso.",
            "As atividades A18/A19 são LOE e ficam fora da rede CPM.",
        ],
    }
    (output / "relatorio_modelo.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    methodology = f"""# EAP acadêmica sintética em escala ampliada

## Escopo e escala

Caso hipotético de implantação de infraestrutura linear, criado sem ler as tabelas do projeto. O modelo tem {len(nodes):,} nós de EAP: {EXPECTED_PARENTS:,} agrupadores e {EXPECTED_LEAVES:,} atividades de detalhe. Somente as contagens agregadas serviram de referência para o tamanho; não foram copiados descrições, códigos, custos, quantidades, datas ou relações de precedência.

## Cronograma

A rede PERT/CPM contém {sum(not task['loe'] for task in activity_by_id.values()):,} atividades discretas e dois marcos. Há {sum(task['loe'] for task in activity_by_id.values()):,} linhas de suporte contínuo classificadas como LOE, fora da rede. O PERT usa TE = (O + 4M + P) / 6; o CPM calcula os inícios, términos e folgas pelas precedências finish-to-start explicitadas em `dependencias_sinteticas.csv`.

O cálculo resulta em {fmt(duration)} dias úteis presumidos. Esse resultado serve à demonstração acadêmica; não é estimativa de obra.

## Custos e CPUs

Os custos da EAP somam 1.000 pontos de índice, sem moeda. O arquivo `ARQUETIPO_CPU` conecta cada folha a uma das 19 famílias sintéticas de CPU; as quantidades-modelo são indicativas e foram definidas para facilitar exercícios de custo. A classificação direta/indireta/em dúvida é hipótese didática.

O gerador de CPUs vincula referências SINAPI públicas onde há aderência parcial, completa o escopo com itens sintéticos e usa CPUs inteiramente sintéticas nos demais casos. Nenhum preço de mercado é atribuído.

## Reprodução

`python scripts/criar_eap_academica_escala.py` cria esta pasta, sem sobrescrever versões existentes. Em seguida, na raiz do workspace, execute `python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py --eap dados_simulados/eap_academica_sintetica_escala_exemplo/EAP_sintetica.csv --output-dir dados_simulados/eap_academica_sintetica_escala_exemplo`.

Referências metodológicas do modelo: GAO, *Schedule Assessment Guide*, https://www.gao.gov/assets/gao-12-120g.pdf; FHWA, *Guide for Construction Contract Time Determination Procedures*, https://www.fhwa.dot.gov/construction/contracts/t508015.cfm.
"""
    (output / "premissas_modelo.md").write_text(methodology, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Saída: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
