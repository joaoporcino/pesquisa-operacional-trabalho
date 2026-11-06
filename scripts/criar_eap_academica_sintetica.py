"""Gera EAP e rede PERT/CPM inteiramente hipotéticas para um estudo acadêmico.

Uso: python scripts/criar_eap_academica_sintetica.py [--output pasta_nova]

O script não lê nem transforma os dados da obra. Os itens, dependências,
durações e custos-índice abaixo foram definidos para um caso genérico.
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
DEFAULT_OUTPUT = ROOT / "dados_simulados/eap_academica_sintetica"
P = Decimal("0.01")


def fmt(value: Decimal) -> str:
    return format(value.quantize(P, rounding=ROUND_HALF_UP), ".2f")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, delimiter=";", lineterminator="\r\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# Todos os pesos são pontos hipotéticos. A soma dos pacotes de trabalho é 1.000.
ACTIVITIES: list[dict[str, Any]] = [
    {"id": "A00", "wbs": "", "name": "Marco de início", "class": "NAO_APLICA", "pred": [], "o": 0, "m": 0, "p": 0, "cost": 0, "mode": "MARCO"},
    {"id": "A01", "wbs": "1.1.1", "name": "Mobilizar equipe e instalar estruturas provisórias", "class": "INDIRETA", "pred": ["A00"], "o": 4, "m": 6, "p": 10, "cost": 20, "mode": "DISCRETA"},
    {"id": "A02", "wbs": "1.1.2", "name": "Executar levantamentos topográficos e geotécnicos", "class": "DUVIDA", "pred": ["A01"], "o": 5, "m": 8, "p": 14, "cost": 10, "mode": "DISCRETA"},
    {"id": "A03", "wbs": "1.2.1", "name": "Obter liberações e autorizações para as frentes", "class": "INDIRETA", "pred": ["A02"], "o": 6, "m": 12, "p": 22, "cost": 10, "mode": "DISCRETA"},
    {"id": "A04", "wbs": "1.2.2", "name": "Concluir projeto executivo e análise de construtibilidade", "class": "INDIRETA", "pred": ["A02"], "o": 10, "m": 16, "p": 28, "cost": 25, "mode": "DISCRETA"},
    {"id": "A05", "wbs": "1.2.3", "name": "Adquirir materiais de prazo longo", "class": "DUVIDA", "pred": ["A04"], "o": 12, "m": 20, "p": 36, "cost": 40, "mode": "DISCRETA"},
    {"id": "A06", "wbs": "2.1.1", "name": "Limpar e preparar acessos e áreas de trabalho", "class": "DIRETA", "pred": ["A01", "A03"], "o": 5, "m": 8, "p": 14, "cost": 40, "mode": "DISCRETA"},
    {"id": "A07", "wbs": "2.2.1", "name": "Executar dispositivos de drenagem transversal", "class": "DIRETA", "pred": ["A06"], "o": 8, "m": 12, "p": 20, "cost": 70, "mode": "DISCRETA"},
    {"id": "A08", "wbs": "2.1.2", "name": "Executar cortes, aterros e conformação do terreno", "class": "DIRETA", "pred": ["A06"], "o": 15, "m": 25, "p": 42, "cost": 200, "mode": "DISCRETA"},
    {"id": "A09", "wbs": "2.1.3", "name": "Preparar e compactar a camada de subleito", "class": "DIRETA", "pred": ["A08"], "o": 6, "m": 10, "p": 17, "cost": 65, "mode": "DISCRETA"},
    {"id": "A10", "wbs": "2.2.2", "name": "Executar valas e dispositivos de drenagem longitudinal", "class": "DIRETA", "pred": ["A07", "A08"], "o": 8, "m": 14, "p": 24, "cost": 65, "mode": "DISCRETA"},
    {"id": "A11", "wbs": "2.3.1", "name": "Executar fundações e contenções", "class": "DIRETA", "pred": ["A06", "A05"], "o": 10, "m": 16, "p": 28, "cost": 95, "mode": "DISCRETA"},
    {"id": "A12", "wbs": "2.3.2", "name": "Construir estruturas de concreto ou metálicas", "class": "DIRETA", "pred": ["A11", "A05"], "o": 12, "m": 20, "p": 34, "cost": 80, "mode": "DISCRETA"},
    {"id": "A13", "wbs": "2.4.1", "name": "Executar sub-base e base granular", "class": "DIRETA", "pred": ["A09", "A10", "A12"], "o": 8, "m": 12, "p": 20, "cost": 70, "mode": "DISCRETA"},
    {"id": "A14", "wbs": "2.4.2", "name": "Executar revestimento e superfície de rolamento", "class": "DIRETA", "pred": ["A13", "A05"], "o": 7, "m": 10, "p": 18, "cost": 90, "mode": "DISCRETA"},
    {"id": "A15", "wbs": "2.4.3", "name": "Instalar sinalização, defensas e acabamentos", "class": "DIRETA", "pred": ["A14"], "o": 4, "m": 7, "p": 13, "cost": 35, "mode": "DISCRETA"},
    {"id": "A16", "wbs": "3.1.1", "name": "Inspecionar, testar e corrigir pendências", "class": "DUVIDA", "pred": ["A15"], "o": 4, "m": 7, "p": 13, "cost": 25, "mode": "DISCRETA"},
    {"id": "A17", "wbs": "3.1.2", "name": "Entregar a infraestrutura e desmobilizar", "class": "INDIRETA", "pred": ["A16"], "o": 2, "m": 4, "p": 8, "cost": 15, "mode": "DISCRETA"},
    {"id": "A18", "wbs": "1.3.1", "name": "Manter planejamento, controles e supervisão de campo", "class": "INDIRETA", "pred": [], "o": None, "m": None, "p": None, "cost": 30, "mode": "LOE"},
    {"id": "A19", "wbs": "1.3.2", "name": "Manter suporte de segurança, meio ambiente e qualidade", "class": "INDIRETA", "pred": [], "o": None, "m": None, "p": None, "cost": 15, "mode": "LOE"},
    {"id": "A99", "wbs": "", "name": "Marco de conclusão", "class": "NAO_APLICA", "pred": ["A17"], "o": 0, "m": 0, "p": 0, "cost": 0, "mode": "MARCO"},
]


NODES: list[dict[str, str]] = [
    {"code": "0", "parent": "", "name": "Projeto acadêmico de implantação de infraestrutura linear", "type": "PROJETO", "deliverable": "Infraestrutura hipotética pronta para operação"},
    {"code": "1", "parent": "0", "name": "Preparação, engenharia e apoio", "type": "FASE", "deliverable": "Frentes liberadas e recursos de apoio disponíveis"},
    {"code": "1.1", "parent": "1", "name": "Implantação e levantamentos", "type": "CONTA_CONTROLE", "deliverable": "Área mobilizada e condições de campo conhecidas"},
    {"code": "1.1.1", "parent": "1.1", "name": "Mobilização e instalações provisórias", "type": "PACOTE_TRABALHO", "activity": "A01", "deliverable": "Canteiro e equipe disponíveis"},
    {"code": "1.1.2", "parent": "1.1", "name": "Levantamentos de campo", "type": "PACOTE_TRABALHO", "activity": "A02", "deliverable": "Dados topográficos e geotécnicos disponíveis"},
    {"code": "1.2", "parent": "1", "name": "Engenharia, liberações e suprimentos", "type": "CONTA_CONTROLE", "deliverable": "Projeto e insumos críticos liberados"},
    {"code": "1.2.1", "parent": "1.2", "name": "Autorizações e liberação de frentes", "type": "PACOTE_TRABALHO", "activity": "A03", "deliverable": "Frentes autorizadas para execução"},
    {"code": "1.2.2", "parent": "1.2", "name": "Projeto executivo e construtibilidade", "type": "PACOTE_TRABALHO", "activity": "A04", "deliverable": "Pacotes de projeto liberados para construção"},
    {"code": "1.2.3", "parent": "1.2", "name": "Aquisição de materiais de prazo longo", "type": "PACOTE_TRABALHO", "activity": "A05", "deliverable": "Materiais críticos disponíveis"},
    {"code": "1.3", "parent": "1", "name": "Gestão e apoio contínuo", "type": "CONTA_CONTROLE", "deliverable": "Controles de campo ativos durante a execução"},
    {"code": "1.3.1", "parent": "1.3", "name": "Planejamento, controles e supervisão", "type": "PACOTE_LOE", "activity": "A18", "deliverable": "Acompanhamento integrado da obra"},
    {"code": "1.3.2", "parent": "1.3", "name": "Segurança, meio ambiente e qualidade", "type": "PACOTE_LOE", "activity": "A19", "deliverable": "Suporte contínuo aos controles de campo"},
    {"code": "2", "parent": "0", "name": "Execução da infraestrutura", "type": "FASE", "deliverable": "Obras civis e camadas executadas"},
    {"code": "2.1", "parent": "2", "name": "Preparação e movimentação de terra", "type": "CONTA_CONTROLE", "deliverable": "Plataforma preparada"},
    {"code": "2.1.1", "parent": "2.1", "name": "Limpeza e acessos provisórios", "type": "PACOTE_TRABALHO", "activity": "A06", "deliverable": "Área de trabalho acessível e liberada"},
    {"code": "2.1.2", "parent": "2.1", "name": "Cortes, aterros e conformação", "type": "PACOTE_TRABALHO", "activity": "A08", "deliverable": "Terreno conformado segundo o projeto"},
    {"code": "2.1.3", "parent": "2.1", "name": "Preparação do subleito", "type": "PACOTE_TRABALHO", "activity": "A09", "deliverable": "Subleito preparado e compactado"},
    {"code": "2.2", "parent": "2", "name": "Drenagem", "type": "CONTA_CONTROLE", "deliverable": "Águas superficiais conduzidas com segurança"},
    {"code": "2.2.1", "parent": "2.2", "name": "Drenagem transversal", "type": "PACOTE_TRABALHO", "activity": "A07", "deliverable": "Dispositivos transversais instalados"},
    {"code": "2.2.2", "parent": "2.2", "name": "Drenagem longitudinal", "type": "PACOTE_TRABALHO", "activity": "A10", "deliverable": "Valas e dispositivos longitudinais executados"},
    {"code": "2.3", "parent": "2", "name": "Fundações e estruturas", "type": "CONTA_CONTROLE", "deliverable": "Estruturas concluídas"},
    {"code": "2.3.1", "parent": "2.3", "name": "Fundações e contenções", "type": "PACOTE_TRABALHO", "activity": "A11", "deliverable": "Fundações e contenções executadas"},
    {"code": "2.3.2", "parent": "2.3", "name": "Estruturas de concreto ou metálicas", "type": "PACOTE_TRABALHO", "activity": "A12", "deliverable": "Estruturas construídas e liberadas"},
    {"code": "2.4", "parent": "2", "name": "Camadas e acabamentos", "type": "CONTA_CONTROLE", "deliverable": "Superfície de rolamento e itens de segurança prontos"},
    {"code": "2.4.1", "parent": "2.4", "name": "Sub-base e base granular", "type": "PACOTE_TRABALHO", "activity": "A13", "deliverable": "Camadas granulares executadas"},
    {"code": "2.4.2", "parent": "2.4", "name": "Revestimento e superfície de rolamento", "type": "PACOTE_TRABALHO", "activity": "A14", "deliverable": "Superfície de rolamento executada"},
    {"code": "2.4.3", "parent": "2.4", "name": "Sinalização, defensas e acabamentos", "type": "PACOTE_TRABALHO", "activity": "A15", "deliverable": "Itens de segurança e acabamento instalados"},
    {"code": "3", "parent": "0", "name": "Inspeção, entrega e encerramento", "type": "FASE", "deliverable": "Infraestrutura aceita e equipe desmobilizada"},
    {"code": "3.1", "parent": "3", "name": "Aceitação e encerramento", "type": "CONTA_CONTROLE", "deliverable": "Pendências tratadas e entrega formalizada"},
    {"code": "3.1.1", "parent": "3.1", "name": "Inspeções e correções", "type": "PACOTE_TRABALHO", "activity": "A16", "deliverable": "Inspeções concluídas e pendências tratadas"},
    {"code": "3.1.2", "parent": "3.1", "name": "Entrega e desmobilização", "type": "PACOTE_TRABALHO", "activity": "A17", "deliverable": "Documentação entregue e instalações provisórias removidas"},
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera EAP e cronograma PERT/CPM de um caso acadêmico sintético.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Pasta de saída nova.")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"A pasta de saída já existe; escolha outra: {output}")

    activity_by_id = {activity["id"]: activity for activity in ACTIVITIES}
    package_activity = {activity["id"]: activity for activity in ACTIVITIES if activity["mode"] in {"DISCRETA", "LOE"}}
    node_by_code = {node["code"]: node for node in NODES}
    if len(node_by_code) != len(NODES):
        raise ValueError("Código EAP duplicado.")
    for node in NODES:
        if node["parent"] and node["parent"] not in node_by_code:
            raise ValueError(f"Pai EAP ausente para {node['code']}.")
        if node.get("activity") and node["activity"] not in package_activity:
            raise ValueError(f"Atividade ausente para pacote {node['code']}.")

    # Custos-índice dos pacotes são agregados de baixo para cima na EAP.
    points_by_code: dict[str, Decimal] = {}
    for node in reversed(NODES):
        activity_id = node.get("activity", "")
        if activity_id:
            points_by_code[node["code"]] = Decimal(str(package_activity[activity_id]["cost"]))
        else:
            points_by_code[node["code"]] = sum(
                (points_by_code.get(child["code"], Decimal("0")) for child in NODES if child["parent"] == node["code"]),
                Decimal("0"),
            )
    root_points = points_by_code["0"]
    if root_points != Decimal("1000"):
        raise ValueError(f"Soma dos pontos de índice precisa ser 1.000; calculado={root_points}.")

    # Calcula TE PERT e passa adiante/para trás pelo grafo finish-to-start.
    network = [activity for activity in ACTIVITIES if activity["mode"] != "LOE"]
    network_ids = {activity["id"] for activity in network}
    for activity in network:
        missing = [pred for pred in activity["pred"] if pred not in network_ids]
        if missing:
            raise ValueError(f"Predecessora não encontrada em {activity['id']}: {missing}")
    successors: dict[str, list[str]] = defaultdict(list)
    for activity in network:
        for predecessor in activity["pred"]:
            successors[predecessor].append(activity["id"])
    ordered: list[dict[str, Any]] = []
    completed: set[str] = set()
    while len(ordered) < len(network):
        ready = [a for a in network if a["id"] not in completed and all(p in completed for p in a["pred"])]
        if not ready:
            raise ValueError("Dependências cíclicas ou atividade sem caminho de entrada.")
        for activity in ready:
            activity["te"] = (Decimal(str(activity["o"])) + Decimal("4") * Decimal(str(activity["m"])) + Decimal(str(activity["p"]))) / Decimal("6")
            activity["es"] = max((activity_by_id[p]["ef"] for p in activity["pred"]), default=Decimal("0"))
            activity["ef"] = activity["es"] + activity["te"]
            completed.add(activity["id"])
            ordered.append(activity)
    project_duration = max(activity["ef"] for activity in ordered)
    for activity in reversed(ordered):
        activity["lf"] = min((activity_by_id[s]["ls"] for s in successors[activity["id"]]), default=project_duration)
        activity["ls"] = activity["lf"] - activity["te"]
        activity["float"] = activity["ls"] - activity["es"]
        activity["critical"] = abs(activity["float"]) < Decimal("0.005")
    critical_path = [activity["id"] for activity in ordered if activity["critical"] and activity["id"] not in {"A00", "A99"}]

    # Monta a tabela EAP com agrupadores e pacotes, incluindo apoio contínuo LOE.
    eap_rows: list[dict[str, Any]] = []
    for node in NODES:
        activity = package_activity.get(node.get("activity", ""))
        classification = activity["class"] if activity else "AGRUPADOR"
        eap_rows.append({
            "COD_EAP": node["code"],
            "COD_PAI": node["parent"],
            "NIVEL": 0 if node["code"] == "0" else node["code"].count(".") + 1,
            "TIPO_EAP": node["type"],
            "DESCRICAO_SINTETICA": node["name"],
            "CLASSIFICACAO": classification,
            "ID_ATIVIDADE": node.get("activity", ""),
            "INCLUI_REDE_PERT_CPM": "SIM" if activity and activity["mode"] == "DISCRETA" else ("NAO_LOE" if activity else "NAO_AGRUPADOR"),
            "PONTOS_CUSTO_INDICE": fmt(points_by_code[node["code"]]),
            "ENTREGA": node["deliverable"],
        })

    # Adiciona marcos sem custo à rede; itens LOE ficam identificados na EAP.
    schedule_rows: list[dict[str, Any]] = []
    for activity in ordered:
        schedule_rows.append({
            "ID_ATIVIDADE": activity["id"],
            "COD_EAP": activity["wbs"],
            "ATIVIDADE_SINTETICA": activity["name"],
            "CLASSIFICACAO": activity["class"],
            "PREDECESSORAS_FS": ",".join(activity["pred"]),
            "O_DIAS_UTEIS": activity["o"],
            "M_DIAS_UTEIS": activity["m"],
            "P_DIAS_UTEIS": activity["p"],
            "TE_PERT_DIAS": fmt(activity["te"]),
            "ES_DIAS": fmt(activity["es"]),
            "EF_DIAS": fmt(activity["ef"]),
            "LS_DIAS": fmt(activity["ls"]),
            "LF_DIAS": fmt(activity["lf"]),
            "FOLGA_DIAS": fmt(activity["float"]),
            "CRITICA": "SIM" if activity["critical"] else "NAO",
            "PONTOS_CUSTO_INDICE": activity["cost"],
            "TIPO": "MARCO" if activity["mode"] == "MARCO" else "ATIVIDADE",
        })

    dependency_rows = [
        {"PREDECESSORA": pred, "SUCESSORA": activity["id"], "RELACAO": "FS", "LAG_DIAS": 0,
         "PREMISSA": "Dependência lógica hipotética para o estudo"}
        for activity in ordered for pred in activity["pred"]
    ]

    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "EAP_sintetica.csv", list(eap_rows[0].keys()), eap_rows)
    write_csv(output / "PERT_CPM_sintetico.csv", list(schedule_rows[0].keys()), schedule_rows)
    write_csv(output / "dependencias_sinteticas.csv", list(dependency_rows[0].keys()), dependency_rows)

    report = {
        "tipo_de_dados": "caso acadêmico inteiramente hipotético; o script não consulta a base da obra",
        "total_de_custo_indice": fmt(root_points),
        "unidade_de_duracao": "dias úteis presumidos",
        "regra_pert": "TE = (O + 4*M + P) / 6",
        "regra_cpm": "relações finish-to-start; sem lag; durações calculadas com TE",
        "duracao_esperada_do_projeto_dias": fmt(project_duration),
        "caminho_critico_exemplo": critical_path,
        "pacotes_loe_excluidos_da_rede": [a["id"] for a in ACTIVITIES if a["mode"] == "LOE"],
        "numero_de_itens_eap": len(NODES),
        "numero_de_atividades_e_marcos_na_rede": len(network),
        "numero_de_dependencias": len(dependency_rows),
        "premissas": [
            "Escopo genérico de infraestrutura linear, sem nomes, códigos, valores, quantidades ou datas da obra real.",
            "Pontos de custo e estimativas de duração são números ilustrativos criados para o estudo.",
            "Classificação direta/indireta/em dúvida é uma hipótese didática de orçamento, não uma regra contábil universal.",
            "Controles contínuos de supervisão e HSE/ambiente/qualidade aparecem como pacotes LOE na EAP e não dirigem a rede CPM.",
            "Predecessoras foram definidas como hipóteses de sequência; devem ser explicadas e ajustadas ao escopo acadêmico.",
        ],
    }
    (output / "relatorio_modelo.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    methodology = f"""# EAP acadêmica sintética — premissas

## Escopo

Caso hipotético de implantação de infraestrutura linear. A EAP foi criada do zero para fins didáticos; o script não lê nem consulta os CSVs da obra. Os rótulos, custos-índice, estimativas de duração e predecessoras são novos e não foram copiados linha a linha de um orçamento real.

## Estrutura e cronograma

A EAP é organizada por entregas e pacotes de trabalho. A rede de cronograma contém atividades discretas e marcos; os serviços contínuos de supervisão e HSE/ambiente/qualidade ficam como pacotes LOE, fora do caminho crítico. A tabela de dependências explicita as relações finish-to-start assumidas.

O PERT usa `TE = (O + 4M + P) / 6`. O CPM calcula início/fim cedo e tarde e folga com essas durações esperadas. O exemplo resulta em {fmt(project_duration)} dias úteis presumidos e caminho crítico {" → ".join(critical_path)}. Esses resultados servem para demonstrar o método, não para estimar uma obra real.

## Custos e classificação

Os custos são pontos sem moeda, somando 1.000 no nível raiz. A classificação `DIRETA`, `INDIRETA` ou `DUVIDA` é uma hipótese didática para treinar análise; deve ser revisada segundo o critério de custeio definido pelo curso.

## Referências metodológicas

- GAO, *Schedule Assessment Guide*: apresenta a WBS como decomposição do escopo/entregáveis e mostra que as atividades do cronograma são derivadas dela. https://www.gao.gov/assets/gao-12-120g.pdf
- FHWA, *Guide for Construction Contract Time Determination Procedures*: orienta sequenciar operações, estimar duração e explicitar precedências, considerando trabalhos paralelos quando aplicável. https://www.fhwa.dot.gov/construction/contracts/t508015.cfm
- FHWA, *Geotechnical Aspects of Pavements — Construction and Construction Monitoring*: descreve a preparação do terreno e subleito como parte da sequência de construção de pavimentos. https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/08.cfm

As referências orientam a forma de decompor e sequenciar o exemplo. As durações, custos-índice, atividades exatas e relações do arquivo são premissas sintéticas, não dados publicados por essas fontes.
"""
    (output / "premissas_modelo.md").write_text(methodology, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Saída: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
