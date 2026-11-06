from __future__ import annotations

import csv
from pathlib import Path

from resolver_piloto import DATA_DIR, solve_model


OUTPUT_DIR = Path(__file__).resolve().parent / "dados_modelo"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rounded(value: float) -> float:
    return round(float(value), 8)


def main() -> None:
    assumptions = {
        row["PARAMETRO"]: float(row["VALOR"])
        for row in read_csv(DATA_DIR / "premissas.csv")
        if row["PARAMETRO"] in {"Custo indireto por prazo", "Custo indireto por efetivo"}
    }
    base_day_rate = assumptions["Custo indireto por prazo"]
    base_person_day_rate = assumptions["Custo indireto por efetivo"]
    fixed_cost = sum(
        float(row["CUSTO_FIXO_PONTOS_INDICE"])
        for row in read_csv(DATA_DIR / "custos_fixos.csv")
    )
    base_summary = read_csv(DATA_DIR / "cenario_base_com_equipes.csv")
    base_duration = max(float(row["FIM_DIA"]) for row in base_summary)
    base_direct = sum(float(row["CUSTO_DIRETO_INDICE"]) for row in base_summary)
    base_person_days = sum(
        float(row["PESSOAS_EQUIPE"]) * float(row["DURACAO_DIAS"])
        for row in base_summary
    )

    cases: list[tuple[str, float, float]] = []
    for rate in (0.05, 0.10, base_day_rate, 0.40, 0.80):
        cases.append(("CUSTO_POR_PRAZO", rate, base_person_day_rate))
    for rate in (0.0025, base_person_day_rate, 0.0100):
        cases.append(("CUSTO_POR_PESSOA_DIA", base_day_rate, rate))
    cases = list(dict.fromkeys(cases))

    rows = []
    for idx, (parameter, day_rate, person_rate) in enumerate(cases, start=1):
        summary, schedule, choices = solve_model(
            data_dir=DATA_DIR,
            ci_day_override=day_rate,
            ci_person_day_override=person_rate,
            write_outputs=False,
        )
        if not summary["otimo_comprovado"] or summary["gap_mip"] not in (0, 0.0):
            raise RuntimeError(
                f"{parameter}={day_rate}/{person_rate}: solução não ótima "
                f"(status {summary['status_solver']}, gap {summary['gap_mip']})."
            )
        person_days = float(summary["efetivo_pessoa_dias"])
        duration = float(summary["prazo_dias_uteis"])
        direct = float(summary["custo_direto_equipes_e_materiais_indice"])
        case_total = fixed_cost + direct + day_rate * duration + person_rate * person_days
        revalued_base_total = (
            fixed_cost + direct + base_day_rate * duration + base_person_day_rate * person_days
        )
        rows.append(
            {
                "ID_CENARIO": f"SENS{idx:02d}",
                "PARAMETRO": "Prazo" if parameter == "CUSTO_POR_PRAZO" else "Pessoa-dia",
                "TAXA_PRAZO": rounded(day_rate),
                "TAXA_PESSOA_DIA": rounded(person_rate),
                "PRAZO_DIAS": rounded(duration),
                "CUSTO_DIRETO": rounded(direct),
                "PESSOA_DIAS": rounded(person_days),
                "INDIRETO_PRAZO": rounded(day_rate * duration),
                "INDIRETO_PESSOA_DIA": rounded(person_rate * person_days),
                "CUSTO_TOTAL_CASO": rounded(case_total),
                "CUSTO_TOTAL_TAXAS_BASE": rounded(revalued_base_total),
                "MODOS_ESCOLHIDOS": " | ".join(
                    f"{activity[-2:]}:{team.rsplit('_', 1)[-1][0]}" for activity, team in choices.items()
                ),
                "STATUS_MILP": "OTIMO" if summary["otimo_comprovado"] else str(summary["status_texto"]),
                "OTIMO": "SIM" if summary["otimo_comprovado"] else "NAO",
                "GAP_MIP": summary["gap_mip"],
                "CAPACIDADE": summary["restricoes_capacidade"],
                "OBSERVACAO": "Cenário sintético; totais entre taxas diferentes só são comparáveis após reprecificação às taxas-base.",
            }
        )

    write_csv(
        OUTPUT_DIR / "sensibilidade_indiretos.csv",
        rows,
        list(rows[0]),
    )

    frontier_candidates = [
        {
            "ID_SOLUCAO": "BASE_SERIAL_PADRAO",
            "DURACAO_DIAS_UTEIS": rounded(base_duration),
            "CUSTO_DIRETO_INDICE": rounded(base_direct),
            "PESSOA_DIAS": rounded(base_person_days),
            "CUSTO_TOTAL_TAXAS_BASE": rounded(
                fixed_cost
                + base_direct
                + base_day_rate * base_duration
                + base_person_day_rate * base_person_days
            ),
            "BASE": "Referência factível (geração serial)",
        }
    ]
    for row in rows:
        frontier_candidates.append(
            {
                "ID_SOLUCAO": row["ID_CENARIO"],
                "DURACAO_DIAS_UTEIS": row["PRAZO_DIAS"],
                "CUSTO_DIRETO_INDICE": row["CUSTO_DIRETO"],
                "PESSOA_DIAS": row["PESSOA_DIAS"],
                "CUSTO_TOTAL_TAXAS_BASE": row["CUSTO_TOTAL_TAXAS_BASE"],
                "BASE": "Solucao MILP reprecificada pelas taxas-base",
            }
        )

    unique = {}
    for row in frontier_candidates:
        key = (row["DURACAO_DIAS_UTEIS"], row["CUSTO_TOTAL_TAXAS_BASE"])
        unique.setdefault(key, row)
    candidates = list(unique.values())
    frontier = []
    for candidate in candidates:
        dominated = any(
            other["DURACAO_DIAS_UTEIS"] <= candidate["DURACAO_DIAS_UTEIS"]
            and other["CUSTO_TOTAL_TAXAS_BASE"] <= candidate["CUSTO_TOTAL_TAXAS_BASE"]
            and (
                other["DURACAO_DIAS_UTEIS"] < candidate["DURACAO_DIAS_UTEIS"]
                or other["CUSTO_TOTAL_TAXAS_BASE"] < candidate["CUSTO_TOTAL_TAXAS_BASE"]
            )
            for other in candidates
        )
        if not dominated:
            frontier.append(candidate)

    frontier.sort(key=lambda row: (row["DURACAO_DIAS_UTEIS"], row["CUSTO_TOTAL_TAXAS_BASE"]))
    frontier_rows = [
        {
            "SOLUCAO": row["ID_SOLUCAO"],
            "PRAZO_DIAS": row["DURACAO_DIAS_UTEIS"],
            "CUSTO_DIRETO": row["CUSTO_DIRETO_INDICE"],
            "PESSOA_DIAS": row["PESSOA_DIAS"],
            "CUSTO_TOTAL_BASE": row["CUSTO_TOTAL_TAXAS_BASE"],
            "ORIGEM": row["BASE"],
            "PARETO": "Não dominada na amostra",
            "OBSERVACAO": (
                "Amostra de soluções por variação dos pesos; "
                "não é a fronteira completa por prazo imposto."
            ),
        }
        for row in frontier
    ]
    write_csv(
        OUTPUT_DIR / "fronteira_prazo_custo_amostral.csv",
        frontier_rows,
        [
            "SOLUCAO",
            "PRAZO_DIAS",
            "CUSTO_DIRETO",
            "PESSOA_DIAS",
            "CUSTO_TOTAL_BASE",
            "ORIGEM",
            "PARETO",
            "OBSERVACAO",
        ],
    )
    print(
        f"{len(rows)} cenários de sensibilidade; "
        f"{len(frontier)} soluções não dominadas na amostra. "
        "Todos os casos MILP precisam estar com status ótimo antes de usar os resultados."
    )


if __name__ == "__main__":
    main()
