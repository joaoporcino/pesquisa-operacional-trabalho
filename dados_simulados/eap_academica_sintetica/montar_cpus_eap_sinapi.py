"""Vincula a EAP acadêmica independente a CPUs didáticas.

O script lê somente EAP_sintetica.csv, que é um modelo hipotético. Não acessa
as tabelas da obra nem baixa preços SINAPI. Os coeficientes das referências
SINAPI são transcritos dos Cadernos Técnicos oficiais; todos os preços e
quantidades do modelo são pontos e premissas sintéticas.

Uso: python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py
"""
from __future__ import annotations

import csv
import argparse
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
EAP_PATH = ROOT / "EAP_sintetica.csv"
Q = Decimal("0.000000000001")
CENT = Decimal("0.01")


def D(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def fmt(value: Decimal, places: int = 2) -> str:
    quantum = Decimal("1").scaleb(-places)
    return format(value.quantize(quantum, rounding=ROUND_HALF_UP), f".{places}f")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            delimiter=";",
            lineterminator="\r\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def item(tipo: str, codigo: str, descricao: str, unidade: str, coef: str,
         base: str, origem: str = "SINAPI", obs: str = "") -> dict[str, Any]:
    return {
        "tipo": tipo, "codigo": codigo, "descricao": descricao,
        "unidade": unidade, "coef": D(coef), "base": D(base),
        "origem": origem, "obs": obs,
    }


SINAPI_DOCS = {
    "95568": "https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-ASSENTAMENTO-DE-TUBOS-DE-ESGOTO-OU-DRENAGEM-PLUVIAL-EM-CONCRETO.pdf",
    "102680": "https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-DRENOS.pdf",
    "105534": "https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-USINAGENS.pdf",
    "104361": "https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-USINAGENS.pdf",
    "103751": "https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-SINALIZACAO-HORIZONTAL-VIARIA.pdf",
}


OFFICIAL: dict[str, dict[str, Any]] = {
    "A07": {
        "code": "95568", "unit": "M",
        "description": "TUBO DE CONCRETO (SIMPLES) PARA REDES COLETORAS DE ÁGUAS PLUVIAIS, DN 400 MM, JUNTA RÍGIDA, BAIXO NÍVEL DE INTERFERÊNCIAS - FORNECIMENTO E ASSENTAMENTO",
        "revision": "Caderno atualizado em 01/04/2024; referência AF_03/2024",
        "status": "ATIVO no Caderno consultado",
        "coverage": "PARCIAL: exemplo de tubo DN 400 mm; não representa todos os dispositivos, escavação e recomposição da drenagem transversal.",
        "items": [
            item("C", "88629", "ARGAMASSA TRAÇO 1:3, PREPARO MANUAL. AF_08/2019", "M3", "0.0016", "1.5"),
            item("C", "88316", "SERVENTE COM ENCARGOS COMPLEMENTARES", "H", "0.4302", "1.0"),
            item("C", "88246", "ASSENTADOR DE TUBOS COM ENCARGOS COMPLEMENTARES", "H", "0.2151", "1.2"),
            item("I", "7781", "TUBO DE CONCRETO SIMPLES PARA ÁGUAS PLUVIAIS, CLASSE PS-1, DN 400 MM", "M", "1.03", "2.0"),
            item("C", "5632", "ESCAVADEIRA HIDRÁULICA 111 HP - CHI DIURNO. AF_06/2014", "CHI", "0.0934", "2.5"),
            item("C", "5631", "ESCAVADEIRA HIDRÁULICA 111 HP - CHP DIURNO. AF_06/2014", "CHP", "0.0481", "3.0"),
        ],
        "supplements": [
            item("SINT", "SINT-EXC-A07", "Escavação, preparo de berço, reaterro e proteção complementar", "M", "1", "2.2", "SINTETICO", "Premissa de complementação do pacote; coeficiente ilustrativo."),
            item("SINT", "SINT-OBRA-A07", "Bocas, alas, dissipadores e acessórios da travessia", "M", "1", "2.8", "SINTETICO", "Premissa de complementação do pacote; coeficiente ilustrativo."),
        ],
    },
    "A10": {
        "code": "102680", "unit": "M",
        "description": "DRENO PROFUNDO, SEÇÃO 0,50 X 1,50 M, TUBO PEAD PERFURADO DN 100 MM, BRITA, GEOTÊXTIL E SELO DE ARGILA",
        "revision": "Caderno atualizado em 04/09/2023; referência AF_07/2021",
        "status": "ATIVO no Caderno consultado",
        "coverage": "PARCIAL: representa um tipo de dreno profundo; não cobre todas as valas, caixas, descargas e recomposições longitudinais.",
        "items": [
            item("C", "93382", "REATERRO MANUAL DE VALAS COM COMPACTADOR DE SOLOS DE PERCUSSÃO. AF_08/2023", "M3", "0.125", "1.6"),
            item("C", "90106", "ESCAVAÇÃO MECANIZADA DE VALA ATÉ 1,5 M, SOLO DE 1A CATEGORIA. AF_09/2024", "M3", "0.75", "2.0"),
            item("C", "88316", "SERVENTE COM ENCARGOS COMPLEMENTARES", "H", "0.1682", "1.0"),
            item("C", "88309", "PEDREIRO COM ENCARGOS COMPLEMENTARES", "H", "0.0561", "1.2"),
            item("I", "38052", "TUBO DRENO PEAD CORRUGADO, PERFURADO, DN 100 MM", "M", "1.003", "2.0"),
            item("C", "5679", "RETROESCAVADEIRA 88 HP - CHI DIURNO. AF_06/2014", "CHI", "0.0851", "2.5"),
            item("C", "5678", "RETROESCAVADEIRA 88 HP - CHP DIURNO. AF_06/2014", "CHP", "0.027", "3.0"),
            item("I", "4718", "PEDRA BRITADA N. 2, SEM FRETE", "M3", "0.6789", "1.7"),
            item("I", "4021", "GEOTÊXTIL NÃO TECIDO, RESISTÊNCIA À TRAÇÃO 14 KN/M", "M2", "4.6", "1.4"),
        ],
        "supplements": [
            item("SINT", "SINT-CAIXAS-A10", "Caixas de inspeção, descargas e conexões fora do dreno-tipo", "M", "1", "2.5", "SINTETICO", "Premissa de complementação do pacote; coeficiente ilustrativo."),
            item("SINT", "SINT-RECOMP-A10", "Recomposição superficial e serviços locais complementares", "M", "1", "1.8", "SINTETICO", "Premissa de complementação do pacote; coeficiente ilustrativo."),
        ],
    },
    "A13": {
        "code": "105534", "unit": "M3",
        "description": "USINAGEM DE SOLO-BRITA 50%-50% COM 8% DE CIMENTO, UTILIZANDO BRITA COMERCIAL. AF_09/2025",
        "revision": "Caderno atualizado em 05/09/2025; referência AF_09/2025",
        "status": "ATIVO no Caderno consultado",
        "coverage": "PARCIAL: representa uma alternativa de mistura produzida em usina; a composição não cobre toda a execução, espalhamento e compactação da base/sub-base.",
        "items": [
            item("C", "95122", "USINA MISTURADORA DE SOLOS 200 A 500 TON/H - CHI DIURNO", "CHI", "0.0059508", "2.5"),
            item("C", "95121", "USINA MISTURADORA DE SOLOS 200 A 500 TON/H - CHP DIURNO", "CHP", "0.0064467", "3.0"),
            item("C", "93428", "GRUPO GERADOR 150 KVA - CHI DIURNO", "CHI", "0.0059508", "2.0"),
            item("C", "93427", "GRUPO GERADOR 150 KVA - CHP DIURNO", "CHP", "0.0064467", "2.5"),
            item("C", "90776", "ENCARREGADO GERAL COM ENCARGOS COMPLEMENTARES", "H", "0.0120664", "1.0"),
            item("C", "88316", "SERVENTE COM ENCARGOS COMPLEMENTARES", "H", "0.0241328", "0.9"),
            item("C", "5942", "PÁ CARREGADEIRA 128 HP - CHI DIURNO", "CHI", "0.0142509", "2.5"),
            item("C", "5940", "PÁ CARREGADEIRA 128 HP - CHP DIURNO", "CHP", "0.0105442", "3.0"),
            item("I", "4741", "PÓ DE PEDRA, SEM FRETE", "M3", "0.3342244", "1.3"),
            item("I", "4721", "PEDRA BRITADA N. 1, SEM FRETE", "M3", "0.093", "1.4"),
            item("I", "4720", "PEDRA BRITADA N. 0, SEM FRETE", "M3", "0.3357871", "1.3"),
            item("I", "4718", "PEDRA BRITADA N. 2, SEM FRETE", "M3", "0.1648695", "1.5"),
            item("I", "1379", "CIMENTO PORTLAND COMPOSTO CP II-32", "KG", "168", "0.4"),
        ],
        "supplements": [
            item("SINT", "SINT-EXEC-A13", "Espalhamento, umidificação, compactação e controle da camada", "M3", "1", "3.2", "SINTETICO", "Premissa de complementação; tecnologia de camada precisa ser definida no projeto hipotético."),
            item("SINT", "SINT-TRANS-A13", "Transporte interno e regularização complementar dos materiais", "M3", "1", "1.7", "SINTETICO", "Premissa de complementação; coeficiente ilustrativo."),
        ],
    },
    "A14": {
        "code": "104361", "unit": "T",
        "description": "USINAGEM DE CONCRETO ASFÁLTICO CAP 50/70 PARA CAMADA DE ROLAMENTO, DNIT FAIXA C, USINA CONTÍNUA 140 TON/H. AF_09/2025",
        "revision": "Caderno atualizado em 05/09/2025; referência AF_09/2025",
        "status": "SEM CUSTO no Caderno consultado",
        "coverage": "PARCIAL: cobre a produção da mistura; transporte até a obra e execução/compactação da camada são excluídos pelo Caderno.",
        "items": [
            item("C", "104689", "GRUPO GERADOR 400–460 KVA - CHI DIURNO", "CHI", "0.009454", "2.0"),
            item("C", "104688", "GRUPO GERADOR 400–460 KVA - CHP DIURNO", "CHP", "0.0102418", "2.5"),
            item("C", "100642", "USINA DE MISTURA ASFÁLTICA 100–140 TON/H - CHI DIURNO", "CHI", "0.009454", "2.5"),
            item("C", "100641", "USINA DE MISTURA ASFÁLTICA 100–140 TON/H - CHP DIURNO", "CHP", "0.0102418", "3.0"),
            item("C", "90776", "ENCARREGADO GERAL COM ENCARGOS COMPLEMENTARES", "H", "0.0196958", "1.0"),
            item("C", "88316", "SERVENTE COM ENCARGOS COMPLEMENTARES", "H", "0.0393916", "0.9"),
            item("I", "44951", "CIMENTO ASFÁLTICO DE PETRÓLEO CAP 50/70", "T", "0.05545", "5.0"),
            item("C", "7030", "TANQUE DE ASFALTO ESTACIONÁRIO 30.000 L - CHP DIURNO", "CHP", "0.0393916", "2.0"),
            item("C", "5942", "PÁ CARREGADEIRA 128 HP - CHI DIURNO", "CHI", "0.014523", "2.0"),
            item("C", "5940", "PÁ CARREGADEIRA 128 HP - CHP DIURNO", "CHP", "0.0051728", "2.5"),
            item("I", "4741", "PÓ DE PEDRA, SEM FRETE", "M3", "0.33631", "1.3"),
            item("I", "4721", "PEDRA BRITADA N. 1, SEM FRETE", "M3", "0.03215", "1.4"),
            item("I", "4720", "PEDRA BRITADA N. 0, SEM FRETE", "M3", "0.42634", "1.3"),
            item("I", "1106", "CAL HIDRATADA CH-I PARA ARGAMASSAS", "KG", "14.4636", "0.4"),
            item("I", "370", "AREIA MÉDIA, SEM TRANSPORTE", "M3", "0.02701", "1.3"),
        ],
        "supplements": [
            item("SINT", "SINT-APLIC-A14", "Transporte, aplicação com vibroacabadora e compactação da camada", "T", "1", "4.5", "SINTETICO", "Complemento essencial do serviço; não fornecido pelo CPU 104361."),
            item("SINT", "SINT-CONTROLE-A14", "Pintura de ligação, ensaios e controle tecnológico", "T", "1", "1.8", "SINTETICO", "Premissa ilustrativa de complemento."),
        ],
    },
    "A15": {
        "code": "103751", "unit": "M",
        "description": "FORNECIMENTO E INSTALAÇÃO DE DEFENSA METÁLICA TRIPLA ONDA DUPLA, SOBRE SOLO. AF_03/2022",
        "revision": "Caderno atualizado em 24/03/2022; referência AF_03/2022",
        "status": "SEM CUSTO no Caderno consultado",
        "coverage": "PARCIAL: representa apenas defensa metálica; sinalização vertical/horizontal e outros acabamentos são complementos sintéticos.",
        "items": [
            item("C", "103668", "BATE-ESTACA PARA DEFENSAS METÁLICAS - CHI DIURNO", "CHI", "0.044", "2.0"),
            item("C", "103667", "BATE-ESTACA PARA DEFENSAS METÁLICAS - CHP DIURNO", "CHP", "0.026", "2.5"),
            item("C", "88278", "MONTADOR DE ESTRUTURA METÁLICA COM ENCARGOS COMPLEMENTARES", "H", "1.5058", "1.0"),
            item("I", "44776", "PORCA SEXTAVADA DE AÇO ZINCADO M16", "UN", "8", "0.4"),
            item("I", "44774", "LÂMINA DE DEFENSA METÁLICA TRIPLA ONDA, PERFIL W", "UN", "0.5", "2.0"),
            item("I", "44752", "PLAQUETA PARA DEFENSA METÁLICA", "UN", "1", "0.4"),
            item("I", "44749", "ESPAÇADOR METÁLICO PARA DEFENSA TRIPLA ONDA", "UN", "0.5", "0.5"),
            item("I", "44745", "POSTE C-150 PARA DEFENSA METÁLICA, C=2,00 M", "UN", "0.25", "1.5"),
            item("I", "44742", "ARRUELA LISA DE AÇO ZINCADO M16", "UN", "8", "0.2"),
            item("I", "44740", "PARAFUSO M16 INOX, 50 MM", "UN", "1", "0.4"),
            item("I", "44739", "PARAFUSO M16 AÇO ZINCADO, 25 MM", "UN", "7", "0.3"),
        ],
        "supplements": [
            item("SINT", "SINT-SINAL-A15", "Sinalização vertical e horizontal do trecho", "M", "1", "3.0", "SINTETICO", "Premissa de complementação do pacote; coeficiente ilustrativo."),
            item("SINT", "SINT-ACAB-A15", "Arremates e acabamentos não cobertos pela defensa", "M", "1", "1.5", "SINTETICO", "Premissa de complementação do pacote; coeficiente ilustrativo."),
        ],
    },
}


# Quantidades físicas/administrativas inteiramente hipotéticas, escolhidas para
# facilitar exercícios de custos unitários e consolidação. Não vêm da obra.
ACTIVITIES: dict[str, dict[str, Any]] = {
    "A01": {"unit": "PACOTE", "qty": "1", "items": [
        item("SINT", "SINT-MDO-A01", "Equipe de mobilização e montagem", "H", "160", "0.08", "SINTETICO"),
        item("SINT", "SINT-EQ-A01", "Mobilização de equipamentos", "DIA_EQ", "10", "1.2", "SINTETICO"),
        item("SINT", "SINT-CANTEIRO-A01", "Instalações provisórias e utilidades", "KIT", "1", "4", "SINTETICO"),
    ]},
    "A02": {"unit": "HA", "qty": "100", "items": [
        item("SINT", "SINT-TOPO-A02", "Equipe de topografia", "H", "4", "1", "SINTETICO"),
        item("SINT", "SINT-EQUIP-A02", "Equipamento topográfico", "DIA_EQ", "0.5", "2", "SINTETICO"),
        item("SINT", "SINT-GEO-A02", "Sondagens e ensaios geotécnicos de referência", "UN", "0.2", "2.5", "SINTETICO"),
    ]},
    "A03": {"unit": "PACOTE", "qty": "1", "items": [
        item("SINT", "SINT-ENG-A03", "Apoio técnico à liberação de frentes", "H", "32", "1", "SINTETICO"),
        item("SINT", "SINT-TAXA-A03", "Taxas e documentação em índice", "PACOTE", "1", "2", "SINTETICO"),
    ]},
    "A04": {"unit": "PACOTE", "qty": "1", "items": [
        item("SINT", "SINT-ENG-A04", "Horas de engenharia de projeto", "H", "120", "1", "SINTETICO"),
        item("SINT", "SINT-REV-A04", "Revisão interdisciplinar e construtibilidade", "H", "40", "1.2", "SINTETICO"),
        item("SINT", "SINT-DOC-A04", "Modelos e documentação técnica", "PACOTE", "1", "2", "SINTETICO"),
    ]},
    "A05": {"unit": "UN", "qty": "100", "items": [
        item("SINT", "SINT-MAT-A05", "Materiais de prazo longo em unidade-modelo", "UN", "1", "2.2", "SINTETICO"),
        item("SINT", "SINT-LOG-A05", "Logística e recebimento unitário", "UN", "1", "0.7", "SINTETICO"),
    ]},
    "A06": {"unit": "M2", "qty": "10000", "items": [
        item("SINT", "SINT-MDO-A06", "Equipe de limpeza e preparação", "H", "0.002", "1", "SINTETICO"),
        item("SINT", "SINT-EQ-A06", "Equipamento de limpeza - tempo improdutivo", "CHI", "0.0008", "2", "SINTETICO"),
        item("SINT", "SINT-RES-A06", "Remoção de resíduos", "M3", "0.02", "1.5", "SINTETICO"),
    ]},
    "A07": {"unit": "M", "qty": "100", "items": []},
    "A08": {"unit": "M3", "qty": "1000", "items": [
        item("SINT", "SINT-ESC-A08", "Escavadeira para corte e carga", "CHP", "0.001", "3", "SINTETICO"),
        item("SINT", "SINT-TR-A08", "Transporte de solo em caminhão basculante", "H", "0.003", "2", "SINTETICO"),
        item("SINT", "SINT-MDO-A08", "Apoio de campo e conformação", "H", "0.004", "1", "SINTETICO"),
        item("SINT", "SINT-REG-A08", "Regularização e controle geométrico", "M3", "1", "0.8", "SINTETICO"),
    ]},
    "A09": {"unit": "M2", "qty": "1000", "items": [
        item("SINT", "SINT-MDO-A09", "Equipe de preparação do subleito", "H", "0.0008", "1", "SINTETICO"),
        item("SINT", "SINT-MOT-A09", "Motoniveladora", "CHI", "0.0004", "2.5", "SINTETICO"),
        item("SINT", "SINT-ROLO-A09", "Rolo compactador", "CHP", "0.0003", "3", "SINTETICO"),
        item("SINT", "SINT-AGUA-A09", "Água para umectação", "M3", "0.02", "0.3", "SINTETICO"),
    ]},
    "A10": {"unit": "M", "qty": "500", "items": []},
    "A11": {"unit": "M3", "qty": "100", "items": [
        item("SINT", "SINT-ESC-A11", "Escavação e preparo da fundação", "M3", "0.7", "1.5", "SINTETICO"),
        item("SINT", "SINT-CONC-A11", "Concreto estrutural", "M3", "0.7", "3", "SINTETICO"),
        item("SINT", "SINT-ACO-A11", "Aço para armadura", "KG", "55", "0.04", "SINTETICO"),
        item("SINT", "SINT-FORMA-A11", "Formas e escoramento", "M2", "2.5", "0.5", "SINTETICO"),
    ]},
    "A12": {"unit": "M3", "qty": "100", "items": [
        item("SINT", "SINT-CONC-A12", "Concreto para estruturas", "M3", "1.05", "3", "SINTETICO"),
        item("SINT", "SINT-ACO-A12", "Aço para armadura", "KG", "80", "0.04", "SINTETICO"),
        item("SINT", "SINT-MDO-A12", "Equipe de concretagem e montagem", "H", "5", "1", "SINTETICO"),
        item("SINT", "SINT-EQ-A12", "Equipamento de içamento", "H", "0.05", "4", "SINTETICO"),
    ]},
    "A13": {"unit": "M3", "qty": "500", "items": []},
    "A14": {"unit": "T", "qty": "1000", "items": []},
    "A15": {"unit": "M", "qty": "100", "items": []},
    "A16": {"unit": "LOTE", "qty": "10", "items": [
        item("SINT", "SINT-LAB-A16", "Ensaios e testes de recebimento", "UN", "2", "2", "SINTETICO"),
        item("SINT", "SINT-INSP-A16", "Inspeção técnica", "H", "8", "1", "SINTETICO"),
        item("SINT", "SINT-COR-A16", "Correções e reinspeção", "LOTE", "1", "1.5", "SINTETICO"),
    ]},
    "A17": {"unit": "PACOTE", "qty": "1", "items": [
        item("SINT", "SINT-DOC-A17", "Documentação e entrega técnica", "PACOTE", "1", "3", "SINTETICO"),
        item("SINT", "SINT-DESM-A17", "Desmobilização de estruturas provisórias", "DIA_EQ", "2", "1.5", "SINTETICO"),
        item("SINT", "SINT-MDO-A17", "Equipe de encerramento", "H", "80", "0.08", "SINTETICO"),
    ]},
    "A18": {"unit": "MES", "qty": "6", "items": [
        item("SINT", "SINT-PLAN-A18", "Planejamento, programação e controle", "H", "120", "1", "SINTETICO"),
        item("SINT", "SINT-SUP-A18", "Supervisão de campo", "H", "160", "1", "SINTETICO"),
        item("SINT", "SINT-SIST-A18", "Ferramentas e apoio de controle", "MES", "1", "3", "SINTETICO"),
    ]},
    "A19": {"unit": "MES", "qty": "6", "items": [
        item("SINT", "SINT-SSMA-A19", "Equipe de segurança e meio ambiente", "H", "120", "1", "SINTETICO"),
        item("SINT", "SINT-QA-A19", "Inspeções de qualidade", "H", "40", "1", "SINTETICO"),
        item("SINT", "SINT-KIT-A19", "Materiais e kits de controle", "MES", "1", "2", "SINTETICO"),
    ]},
}


def load_eap(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def price_base(row: dict[str, Any]) -> Decimal:
    return row["base"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera CPUs didáticas ligadas à EAP acadêmica sintética.")
    parser.add_argument("--eap", type=Path, default=EAP_PATH, help="CSV de EAP acadêmica sintética.")
    parser.add_argument("--output-dir", type=Path, default=ROOT, help="Pasta onde os arquivos de CPU serão gravados.")
    args = parser.parse_args()
    eap_path = args.eap.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    eap = load_eap(eap_path)
    activity_rows = [r for r in eap if r["ID_ATIVIDADE"]]
    archetypes = {r.get("ARQUETIPO_CPU") or r["ID_ATIVIDADE"] for r in activity_rows}
    unknown_archetypes = archetypes - set(ACTIVITIES)
    if unknown_archetypes:
        raise ValueError(f"Arquétipos sem modelo de CPU: {sorted(unknown_archetypes)}")

    headers: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []
    link_rows: list[dict[str, Any]] = []
    package_costs: dict[str, Decimal] = {}

    for eap_row in activity_rows:
        activity = eap_row["ID_ATIVIDADE"]
        archetype = eap_row.get("ARQUETIPO_CPU") or activity
        budget = D(eap_row["PONTOS_CUSTO_INDICE"])
        setup = ACTIVITIES[archetype]
        ref = OFFICIAL.get(archetype)
        cpu_id = f"CPU-{activity}"
        qty = D(eap_row.get("QUANTIDADE_MODELO") or setup["qty"])
        unit = eap_row.get("UNIDADE_MODELO") or setup["unit"]
        if ref:
            if unit != ref["unit"]:
                raise ValueError(f"Unidade de {activity} ({archetype}) diverge da referência SINAPI: {unit}/{ref['unit']}")
            source_items = ref["items"] + ref["supplements"]
            origin = "ESTRUTURA SINAPI PARCIAL + COMPLEMENTOS SINTÉTICOS"
            reference_code = ref["code"]
            ref_status = ref["status"]
            coverage = ref["coverage"]
            source_url = SINAPI_DOCS[reference_code]
            revision = ref["revision"]
        else:
            source_items = setup["items"]
            origin = "COMPOSIÇÃO INTEIRAMENTE SINTÉTICA"
            reference_code = ""
            ref_status = "SEM REFERÊNCIA TÉCNICA DIRETA SELECIONADA"
            coverage = "CPU hipotética para atividade acadêmica detalhada; requer validação técnica se usada fora do exercício."
            source_url = ""
            revision = ""
        if qty <= 0:
            raise ValueError(f"Quantidade-modelo precisa ser positiva em {activity}")

        target_unit_cost = budget / qty
        raw_total = sum((r["coef"] * price_base(r) for r in source_items), D(0))
        if raw_total <= 0:
            raise ValueError(f"Sem base de cálculo para {activity}")
        scale = target_unit_cost / raw_total
        prices: list[Decimal] = []
        for i, row in enumerate(source_items):
            if i < len(source_items) - 1:
                prices.append(row["base"] * scale)
            else:
                prior = sum((source_items[j]["coef"] * prices[j] for j in range(i)), D(0))
                prices.append((target_unit_cost - prior) / row["coef"])

        calculated_rate = D(0)
        for seq, (row, rate) in enumerate(zip(source_items, prices), start=1):
            line_cost = row["coef"] * rate
            calculated_rate += line_cost
            item_rows.append({
                "ID_CPU": cpu_id,
                "SEQ": seq,
                "TIPO_ITEM": row["tipo"],
                "CODIGO_ITEM": row["codigo"],
                "DESCRICAO_ITEM": row["descricao"],
                "UNIDADE_ITEM": row["unidade"],
                "COEFICIENTE": fmt(row["coef"], 8),
                "PRECO_UNITARIO_INDICE_SINTETICO": fmt(rate, 12),
                "CUSTO_INDICE_POR_UNIDADE_CPU": fmt(line_cost, 12),
                "ORIGEM_COEFICIENTE": row["origem"],
                "STATUS_PRECO": "SINTÉTICO; NÃO É PREÇO SINAPI",
                "OBSERVACAO": row["obs"] or ("Coeficiente transcrito do Caderno Técnico; rateio em índice didático. "
                                               "Itens C não foram expandidos recursivamente nesta versão." if row["origem"] == "SINAPI" else "")
            })
        if abs(calculated_rate - target_unit_cost) > D("0.000000001"):
            raise ArithmeticError(f"CPU {cpu_id} não fecha: {calculated_rate} != {target_unit_cost}")

        package_cost = qty * calculated_rate
        package_costs[eap_row["COD_EAP"]] = package_cost
        headers.append({
            "ID_CPU": cpu_id,
            "COD_EAP": eap_row["COD_EAP"],
            "ID_ATIVIDADE": activity,
            "DESCRICAO_CPU": eap_row["DESCRICAO_SINTETICA"],
            "UNIDADE_CPU": unit,
            "QUANTIDADE_MODELO": fmt(qty, 2),
            "CUSTO_UNITARIO_INDICE": fmt(calculated_rate, 12),
            "CUSTO_TOTAL_INDICE": fmt(package_cost, 2),
            "ORIGEM_ESTRUTURA": origin,
            "CODIGO_SINAPI_REFERENCIA": reference_code,
            "SITUACAO_REFERENCIA": ref_status,
            "REVISAO_CADERNO": revision,
            "UF_PRECO": "NAO_APLICA",
            "COMPETENCIA_PRECO": "NAO_APLICA",
            "STATUS_CUSTO": "PONTOS DE ÍNDICE SINTÉTICOS; SEM VALOR EM R$",
            "FONTE": source_url,
            "COBERTURA_TECNICA": coverage,
            "CLASSIFICACAO_ATIVIDADE": eap_row["CLASSIFICACAO"],
        })
        link_rows.append({
            "COD_EAP": eap_row["COD_EAP"],
            "ID_ATIVIDADE": activity,
            "ID_CPU": cpu_id,
            "TIPO_VINCULO": "REFERÊNCIA PARCIAL SINAPI + CPU DIDÁTICA" if ref else "CPU DIDÁTICA SINTÉTICA",
            "CODIGO_SINAPI": reference_code,
            "UNIDADE": unit,
            "QUANTIDADE_MODELO": fmt(qty, 2),
            "PONTOS_CUSTO_INDICE": fmt(package_cost, 2),
            "CLASSIFICACAO": eap_row["CLASSIFICACAO"],
            "COBERTURA_TECNICA": coverage,
            "PRECO_USADO": "NENHUM PREÇO SINAPI; índice sintético calibrado para reconciliar com a EAP acadêmica",
        })

    # Consolidação dos custos dos pacotes para os níveis superiores da EAP.
    nodes = {r["COD_EAP"]: r for r in eap}
    children: dict[str, list[str]] = defaultdict(list)
    for r in eap:
        parent = r["COD_PAI"]
        if parent:
            children[parent].append(r["COD_EAP"])
    rollup: dict[str, Decimal] = dict(package_costs)
    ordered = sorted(eap, key=lambda r: int(r["NIVEL"]), reverse=True)
    for r in ordered:
        code = r["COD_EAP"]
        if code in rollup:
            continue
        rollup[code] = sum((rollup.get(child, D(0)) for child in children.get(code, [])), D(0))
    rollup_rows = []
    for r in eap:
        code = r["COD_EAP"]
        source_value = D(r["PONTOS_CUSTO_INDICE"])
        computed = rollup.get(code, D(0))
        rollup_rows.append({
            "COD_EAP": code,
            "COD_PAI": r["COD_PAI"],
            "NIVEL": r["NIVEL"],
            "DESCRICAO_SINTETICA": r["DESCRICAO_SINTETICA"],
            "PONTOS_EAP_ORIGINAIS": fmt(source_value, 2),
            "PONTOS_ROLLUP_CPU": fmt(computed, 2),
            "DIFERENCA": fmt(computed - source_value, 2),
            "RECONCILIADO": "SIM" if abs(computed - source_value) <= CENT else "NAO",
        })

    write_csv(output_dir / "CPUs_EAP_sinteticas.csv", [
        "ID_CPU", "COD_EAP", "ID_ATIVIDADE", "DESCRICAO_CPU", "UNIDADE_CPU",
        "QUANTIDADE_MODELO", "CUSTO_UNITARIO_INDICE", "CUSTO_TOTAL_INDICE",
        "ORIGEM_ESTRUTURA", "CODIGO_SINAPI_REFERENCIA", "SITUACAO_REFERENCIA",
        "REVISAO_CADERNO", "UF_PRECO", "COMPETENCIA_PRECO", "STATUS_CUSTO",
        "FONTE", "COBERTURA_TECNICA", "CLASSIFICACAO_ATIVIDADE",
    ], headers)
    write_csv(output_dir / "Itens_CPU_EAP_sinteticas.csv", [
        "ID_CPU", "SEQ", "TIPO_ITEM", "CODIGO_ITEM", "DESCRICAO_ITEM", "UNIDADE_ITEM",
        "COEFICIENTE", "PRECO_UNITARIO_INDICE_SINTETICO", "CUSTO_INDICE_POR_UNIDADE_CPU",
        "ORIGEM_COEFICIENTE", "STATUS_PRECO", "OBSERVACAO",
    ], item_rows)
    write_csv(output_dir / "Vinculo_EAP_CPU.csv", [
        "COD_EAP", "ID_ATIVIDADE", "ID_CPU", "TIPO_VINCULO", "CODIGO_SINAPI", "UNIDADE",
        "QUANTIDADE_MODELO", "PONTOS_CUSTO_INDICE", "CLASSIFICACAO", "COBERTURA_TECNICA", "PRECO_USADO",
    ], link_rows)
    write_csv(output_dir / "Conferencia_rollup_EAP_CPU.csv", [
        "COD_EAP", "COD_PAI", "NIVEL", "DESCRICAO_SINTETICA", "PONTOS_EAP_ORIGINAIS",
        "PONTOS_ROLLUP_CPU", "DIFERENCA", "RECONCILIADO",
    ], rollup_rows)

    source_rows = []
    for activity, ref in OFFICIAL.items():
        source_rows.append({
            "ID_ATIVIDADE": activity,
            "CODIGO_SINAPI": ref["code"],
            "DESCRICAO_REFERENCIA": ref["description"],
            "UNIDADE": ref["unit"],
            "SITUACAO_NO_CADERNO": ref["status"],
            "REVISAO": ref["revision"],
            "COBERTURA_NA_EAP": ref["coverage"],
            "URL_OFICIAL": SINAPI_DOCS[ref["code"]],
        })
    write_csv(output_dir / "Referencias_SINAPI_publicas.csv", [
        "ID_ATIVIDADE", "CODIGO_SINAPI", "DESCRICAO_REFERENCIA", "UNIDADE",
        "SITUACAO_NO_CADERNO", "REVISAO", "COBERTURA_NA_EAP", "URL_OFICIAL",
    ], source_rows)

    total = sum(package_costs.values(), D(0))
    mismatch = [r for r in rollup_rows if r["RECONCILIADO"] != "SIM"]
    report = {
        "tipo_dataset": "EAP acadêmica inteiramente hipotética",
        "entrada_unica": eap_path.name,
        "referencias_sinapi": len(OFFICIAL),
        "cpus_por_atividade": len(headers),
        "itens_cpu": len(item_rows),
        "custo_total_pontos_indice": fmt(total, 2),
        "custo_em_moeda": False,
        "quantidades_sao_sinteticas": True,
        "precos_sinapi_utilizados": False,
        "precos_sinteticos_calibrados_para_reconciliar_com_eap": True,
        "niveis_eap_divergentes": len(mismatch),
        "observacao": "Coeficientes SINAPI são referências técnicas. Preços, quantidades e complementos são sintéticos; itens SINAPI tipo C não foram expandidos recursivamente.",
    }
    (output_dir / "relatorio_cpus_eap.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    workspace_root = ROOT.parent.parent
    try:
        eap_command_path = eap_path.relative_to(workspace_root).as_posix()
    except ValueError:
        eap_command_path = str(eap_path)
    try:
        output_command_path = output_dir.relative_to(workspace_root).as_posix()
    except ValueError:
        output_command_path = str(output_dir)

    readme = """# CPUs de referência para a EAP acadêmica

## O que foi montado

O arquivo `Vinculo_EAP_CPU.csv` liga cada pacote da EAP hipotética a uma CPU didática. Cinco pacotes trazem uma referência técnica parcial de composição SINAPI: drenagem transversal, drenagem longitudinal, produção de mistura para base, usinagem do revestimento e defensa metálica. Os pacotes sem correspondência direta usam apenas composição sintética.

`CPUs_EAP_sinteticas.csv` guarda o cabeçalho por pacote; `Itens_CPU_EAP_sinteticas.csv` guarda os coeficientes de referência ou os itens hipotéticos; `Conferencia_rollup_EAP_CPU.csv` confere a soma dos itens para CPU, da CPU para pacote e dos pacotes para todos os níveis da EAP.

## Regra de custo e quantidade

Os códigos, descrições e coeficientes técnicos indicados como SINAPI foram transcritos dos Cadernos Técnicos da CAIXA. As quantidades dos pacotes, os itens complementares e todos os preços unitários em pontos de índice foram criados para o exercício. As taxas sintéticas foram calibradas para preservar os pontos de custo já definidos na EAP, totalizando 1.000 pontos sem moeda. Nenhum preço de mercado, preço regional ou custo SINAPI foi usado.

A Nota SINAPI 12/2025 nº 01 da CAIXA informou publicação de relatórios com preços/custos zerados a partir da referência outubro/2025. A Nota 12/2025 nº 02 registrou a retificação, em 22/12/2025, dos relatórios de outubro e novembro/2025 com as informações de preço recebidas do IBGE. Este modelo não utiliza preços SINAPI; para uma futura monetização, deve-se conferir diretamente o relatório mais recente da UF e competência escolhidas. Os Cadernos consultados identificam explicitamente as referências 104361 e 103751 como sem custo.

Os itens SINAPI do tipo C são mantidos como referências de subcomposição, mas esta versão não abre recursivamente cada subcomposição até todos os insumos. Seus preços unitários de índice também são sintéticos. Assim, a tabela demonstra a ligação e o roll-up de custos no nível disponibilizado; ela não substitui orçamento referencial nem reproduz integralmente uma CPU SINAPI.

## Limites da aderência

As CPUs destacadas não cobrem sozinhas a atividade inteira: 95568 é um tubo simples DN 400 mm em baixa interferência; 102680 é um tipo específico de dreno profundo; 105534 é a usinagem de uma mistura solo-brita com cimento; 104361 é a produção de mistura asfáltica sem transporte e aplicação; 103751 cobre defensa metálica, não todo o escopo de sinalização e acabamentos. Os complementos sintéticos permanecem sinalizados nos itens.

As quantidades-modelo e os coeficientes de complementos são premissas acadêmicas e não descrevem dimensões, produtividade, valores ou estrutura da obra usada como inspiração. A EAP e as CPUs aqui vinculadas são independentes dos dados locais da obra.

## Fontes oficiais

- CAIXA, [SINAPI — relatórios mensais, documentação e consulta de preços/custos](https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/paginas/default.aspx).
- CAIXA, [Notas SINAPI](https://www.caixa.gov.br/Downloads/sinapi-historico-de-encargos-e-notas/Notas_SINAPI.pdf), incluindo a nota inicial de valores zerados e a retificação posterior dos relatórios de outubro e novembro/2025.
- CAIXA, [Caderno de assentamento de tubos de esgoto/drenagem pluvial em concreto](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-ASSENTAMENTO-DE-TUBOS-DE-ESGOTO-OU-DRENAGEM-PLUVIAL-EM-CONCRETO.pdf), referência 95568.
- CAIXA, [Caderno de drenos](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-DRENOS.pdf), referência 102680.
- CAIXA, [Caderno de usinagens](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-USINAGENS.pdf), referências 105534 e 104361.
- CAIXA, [Caderno de sinalização horizontal viária](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-SINALIZACAO-HORIZONTAL-VIARIA.pdf), referência 103751.

## Reprodução

O gerador lê somente o CSV de EAP sintética informado e grava as CPUs na pasta de saída. A linha de comando exata para esta versão está logo abaixo.
"""
    readme += f"\n\nPara reproduzir usando esta EAP: `python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py --eap \"{eap_command_path}\" --output-dir \"{output_command_path}\"`.\n"
    (output_dir / "premissas_cpus_sinapi.md").write_text(readme, encoding="utf-8")

    if mismatch:
        raise ArithmeticError(f"Roll-up não reconciliou em {len(mismatch)} níveis da EAP")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
