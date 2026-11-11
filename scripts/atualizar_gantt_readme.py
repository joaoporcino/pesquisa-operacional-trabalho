"""Atualiza o Gantt Mermaid do recorte ampliado a partir da solução salva."""
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "outputs/otimizacao_piloto/dados_modelo_ampliado"
SOLUTION = ROOT / "outputs/otimizacao_piloto/resultados_ampliado/cronograma_gurobi.csv"
EAP = ROOT / "dados_simulados/eap_academica_sintetica_escala_exemplo/EAP_sintetica.csv"
README = ROOT / "README.md"
START = "<!-- INICIO GANTT AMPLIADO -->"
END = "<!-- FIM GANTT AMPLIADO -->"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def main():
    summary = json.loads(SOLUTION.with_name("resumo_gurobi.json").read_text(encoding="utf-8"))
    hierarchy = {r["COD_EAP"]: r for r in read(EAP)}
    tasks = {r["ID_ATIVIDADE"]: r for r in read(DATA / "atividades.csv") if r["TIPO"] == "EXECUCAO"}
    schedule = {r["ID_ATIVIDADE"]: r for r in read(SOLUTION) if r["ID_ATIVIDADE"] in tasks}
    if set(tasks) != set(schedule):
        raise ValueError("O cronograma e as tarefas do recorte não coincidem.")
    predecessors = defaultdict(list)
    successors = defaultdict(list)
    for edge in read(DATA / "precedencias.csv"):
        before, after = edge["PREDECESSORA"], edge["SUCESSORA"]
        if before not in tasks and before != "OP00" or after not in tasks:
            raise ValueError(f"Precedência fora do recorte: {before} -> {after}")
        predecessors[after].append(before)
        successors[before].append(after)
    rows = []
    for task_id, task in tasks.items():
        code = task["CODIGOS_EAP_ORIGEM"]
        if code not in hierarchy or hierarchy[code]["ID_ATIVIDADE"] != task["IDS_ATIVIDADE_EAP_ORIGEM"]:
            raise ValueError(f"Vínculo EAP inválido em {task_id}")
        ancestors = []
        parent = hierarchy[code]["COD_PAI"]
        while parent and parent != "0":
            ancestors.append(hierarchy[parent])
            parent = hierarchy[parent]["COD_PAI"]
        rows.append((tuple(map(int, code.split("."))), code, task_id, task, schedule[task_id], list(reversed(ancestors))))
    rows.sort()
    origin = datetime(2026, 1, 1)
    duration = f"{float(summary['prazo_dias_uteis']):.2f}".replace(".", ",")
    gap = f"{100 * float(summary['gap_mip']):.2f}".replace(".", ",")
    status = "com otimalidade comprovada" if summary["otimo_comprovado"] else "sem otimalidade comprovada"
    lines = [START, "### Gantt do recorte ampliado por EAP", "",
             f"A visualização usa a solução factível do Gurobi registrada em `resultados_ampliado/`: {len(rows)} tarefas, prazo de {duration} dias úteis e gap de {gap}%, {status}. As linhas estão agrupadas pela hierarquia original da EAP (fase → conta de controle → pacote → tarefa); os agrupadores não são atividades nem criam precedências. O marco inicial ocorre no dia 0.", "",
             "O Mermaid exige uma escala de datas: **01/01/2026 representa o dia útil 0**, e cada dia no eixo equivale a um dia útil do modelo. As datas são apenas uma régua fictícia, sem calendário civil, fins de semana ou feriados. Os horários são convertidos e arredondados ao minuto para a visualização; os valores originais estão no CSV. Tarefas em linhas diferentes podem ocorrer em paralelo, respeitando os recursos da solução. Cada seção identifica fase e conta; o código antes de cada tarefa identifica também seu pacote de trabalho.", "",
             "Em cada linha, **P** indica predecessoras e **S** sucessoras pelos IDs das tarefas; `-` indica ausência. `OP00` é o marco inicial. As relações são término-início, sem defasagem. Conforme a [sintaxe do Mermaid](https://mermaid.ai/open-source/syntax/gantt.html), `after` posiciona a tarefa no término mais tardio das predecessoras, enquanto a solução com recursos pode iniciá-la mais tarde. Por isso, as barras usam datas explícitas do solver e os vínculos aparecem nos rótulos; o Gantt não desenha setas entre elas.", "", "```mermaid",
             "gantt", "    title Cronograma ampliado por tarefa e EAP — escala fictícia", "    dateFormat YYYY-MM-DD HH:mm", "    axisFormat %d/%m", "    todayMarker off", "    section Marcos", "    OP00 Marco inicial :milestone, OP00, 2026-01-01 00:00, 0d"]
    previous_section = None
    for _, code, task_id, task, result, parents in rows:
        if len(parents) != 3:
            raise ValueError(f"Hierarquia inesperada para {code}")
        phase, account, package = parents
        section = (phase["COD_EAP"], account["COD_EAP"])
        if section != previous_section:
            lines.append(f"    section {phase['COD_EAP']} {phase['DESCRICAO_SINTETICA']} / {account['COD_EAP']} {account['DESCRICAO_SINTETICA']}")
        begin, finish = float(result["INICIO_DIA"]), float(result["FIM_DIA"])
        description = task["DESCRICAO"].split(" — ")[-1]
        start_date = (origin + timedelta(minutes=round(begin * 1440))).strftime("%Y-%m-%d %H:%M")
        finish_date = (origin + timedelta(minutes=round(finish * 1440))).strftime("%Y-%m-%d %H:%M")
        pred = "+".join(sorted(predecessors[task_id])) or "-"
        succ = "+".join(sorted(successors[task_id])) or "-"
        label = f"{code} {task_id} {description} [P {pred} | S {succ}]".replace(":", " -").replace(",", " -")
        lines.append(f"    {label} :{task_id}, {start_date}, {finish_date}")
        previous_section = section
    lines += ["```", "", "O Gantt é atualizado automaticamente após uma solução válida do recorte ampliado gravada em `resultados_ampliado/`. Para atualizá-lo manualmente, execute `python scripts/atualizar_gantt_readme.py`. Os horários originais estão em [cronograma_gurobi.csv](outputs/otimizacao_piloto/resultados_ampliado/cronograma_gurobi.csv).", END]
    text = README.read_text(encoding="utf-8")
    block = "\n".join(lines)
    if START in text and END in text:
        left, rest = text.split(START, 1)
        _, right = rest.split(END, 1)
        text = left + block + right
    else:
        anchor = "### Os dados já permitem executar o modelo?"
        if text.count(anchor) != 1:
            raise ValueError("Não foi encontrado o ponto de inserção no README.")
        text = text.replace(anchor, block + "\n\n" + anchor)
    README.write_text(text, encoding="utf-8")
    print(f"Gantt Mermaid atualizado: {len(rows)} tarefas.")


if __name__ == "__main__":
    main()
