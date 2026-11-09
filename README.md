# Pesquisa operacional aplicada ao planejamento de obras

Projeto acadêmico de Pesquisa Operacional aplicada ao planejamento de obras. A minimização de custo será realizada sobre um caso simulado, com escolha de equipes e datas de início sujeita a recursos limitados. Os dados anonimizados contextualizam a organização do orçamento e o processo convencional de planejamento.

## A ideia em uma leitura

No orçamento convencional, as quantidades de serviços e as composições determinam o custo; o cronograma e a distribuição dos recursos são desenvolvidos a partir das durações e precedências. Neste trabalho, investigamos uma decisão integrada: **qual equipe habilitada executar em cada atividade e quando**, considerando que sua produtividade altera a duração e que o prazo afeta os custos indiretos do projeto.

Termos úteis: **EAP** é a decomposição hierárquica do trabalho; **composição de custo unitário (CPU)** reúne os recursos necessários por unidade de serviço; **PERT/CPM** analisa a rede de precedências, datas e folgas; e **PO** é pesquisa operacional. Uma relação pai–filho na EAP não é, por si só, uma precedência entre atividades.

## Escopo do trabalho e bases utilizadas

O trabalho consiste no **desenvolvimento e na avaliação de um modelo de PO em um caso simulado de construção, contextualizado pelo processo de orçamento e planejamento observado no projeto anonimizado**.

A pergunta de pesquisa é: **como a escolha conjunta de equipes e datas de início influencia o custo total e o prazo de uma obra, respeitando precedências e disponibilidade de recursos?** O modelo é uma variante determinística do MRCPSP, problema de programação de projetos com recursos limitados e modos alternativos de execução. A contribuição acadêmica está na aplicação, formulação e avaliação do modelo e na interpretação dos resultados. O vínculo com a literatura está descrito nas [referências de modelagem](outputs/otimizacao_piloto/referencias_modelagem.md).

### Qual base será usada na minimização?

| Base ou pasta | Papel no trabalho |
|---|---|
| `dados_anonimizados/` | Referência para explicar EAP, composições, insumos e planejamento na abordagem convencional |
| `dados_simulados/eap_academica_sintetica_escala_exemplo/` | EAP acadêmica independente usada como referência estrutural e de pontos de custo para o recorte simulado |
| `outputs/otimizacao_piloto/dados_modelo/` | Entradas efetivamente lidas pelos solvers: atividades, alternativas, precedências, recursos e premissas de custo |
| `outputs/otimizacao_piloto/resultados_gurobi/` | Cronograma e resumo produzidos pelo solver Gurobi |

Portanto, **a aplicação quantitativa será feita nos dados simulados**, preparados para o problema de otimização. O gerador do piloto utiliza a EAP acadêmica independente e acrescenta quantidades, produtividades, alternativas de equipe e precedências hipotéticas. Os vínculos de origem registrados nesses CSVs apontam para a EAP acadêmica. Eles não estabelecem uma correspondência validada com as atividades do projeto anonimizado.

### Os dados já permitem executar o modelo?

Sim. O piloto já dispõe de 12 atividades de execução, um marco, 13 precedências, 36 alternativas de equipe e seis famílias de recursos com capacidade unitária. As verificações registram rede sem ciclos, durações coerentes com quantidade/produtividade, conciliação dos custos diretos padrão com a EAP acadêmica e ausência de conflitos na referência factível. O script de minimização já está implementado e há resultados salvos.

Essas verificações demonstram a consistência interna do caso simulado. A produtividade, os custos e a disponibilidade usados na otimização são premissas acadêmicas. Sua aplicação a uma obra específica exigiria levantamento e validação próprios.

### Como comparar as metodologias?

O paralelo com o projeto anonimizado será **metodológico**: explicar como o orçamento convencional organiza atividades e composições e como a proposta incorpora alternativas de equipe à decisão de programação.

A comparação **quantitativa** será feita entre dois cenários do mesmo caso simulado:

| Cenário | Equipes e programação |
|---|---|
| Referência factível | Fixa as equipes padrão e usa uma heurística serial para programar as atividades, respeitando precedências e recursos |
| Otimizado | Escolhe equipes e datas de início conjuntamente para minimizar o custo total, respeitando as mesmas condições de execução |

Os dois cenários compartilham escopo, quantidades, precedências, calendário de referência, disponibilidade de recursos, catálogo de alternativas e critérios de custo. Na referência, a escolha é fixada no modo padrão; no otimizado, o modelo pode selecionar os demais modos habilitados. A referência é uma representação acadêmica de escolhas fixadas, não uma reprodução comprovada do cronograma do projeto anonimizado.

O PERT/CPM sem restrição de recursos é usado para analisar a rede lógica. A comparação principal de desempenho utiliza a referência factível, pois o CPM pode permitir sobreposição de atividades que disputam o mesmo recurso.

Nos [resultados salvos do piloto](outputs/otimizacao_piloto/dados_modelo/comparacao_cenarios.csv):

| Indicador | Referência factível | Otimizado | Redução em relação à referência |
|---|---:|---:|---:|
| Prazo em dias úteis | 34,00 | 24,33 | 28,4% |
| Custo total em pontos de índice | 24,9600 | 23,9759 | 3,9% |

Esses ganhos se referem ao caso simulado e à referência específica adotada. Não representam uma estimativa de economia no projeto anonimizado nem demonstram superioridade geral sobre o planejamento convencional. Ao alterar dados ou taxas, é necessário resolver novamente e atualizar os resultados e as verificações.

Uma aplicação futura aos dados anonimizados exigiria selecionar um recorte da mesma versão do projeto, mapear suas atividades, validar quantidades e precedências, levantar alternativas de equipe e conciliar os custos diretos e de apoio. A documentação registra ausência de predecessoras explícitas e pendências em fórmulas de parte da extração; essas questões precisam ser resolvidas para uma comparação econômica com a obra.

### Tipos de variáveis e atendimento ao requisito da disciplina

O modelo reúne pelo menos dois tipos de variáveis de decisão:

| Tipo | Variáveis | Exemplo |
|---|---|---|
| Booleana/binária | Escolha da equipe e ordem entre atividades que disputam um recurso | Escolher uma alternativa: 0 ou 1 |
| Contínua | Início das atividades e término do projeto | Início no dia útil 2,5 |

Essa combinação caracteriza uma programação linear inteira mista e atende ao requisito de usar pelo menos dois tipos. A variável binária é um caso particular de variável inteira discreta. O modelo atual não possui uma decisão inteira geral, como contratar 0, 1, 2 ou 3 equipes. A quantidade de pessoas de cada formação é um parâmetro cadastrado; a decisão consiste em escolher a formação. Se forem exigidos os três tipos separadamente, será necessário acrescentar uma decisão inteira geral com custos e restrições correspondentes.

## Como as informações do orçamento se relacionam

O diagrama representa o significado das entidades da base, não um esquema físico completo. Um recurso de composição é a linha que liga uma composição a um insumo **ou** a uma composição filha. A mesma composição pode ser usada em várias atividades ou composições.

```mermaid
erDiagram
    PROJETO ||--o{ ATIVIDADE : organiza
    ATIVIDADE o|--o{ ATIVIDADE : "agrupa na EAP"
    COMPOSICAO o|--o{ ATIVIDADE : "associada a"
    COMPOSICAO ||--o{ RECURSO_COMPOSICAO : contem
    INSUMO o|--o{ RECURSO_COMPOSICAO : "pode ser o recurso"
    COMPOSICAO o|--o{ RECURSO_COMPOSICAO : "pode ser composicao filha"
    ATIVIDADE ||--o{ PLANEJAMENTO_PERIODO : possui
    PERIODO ||--o{ PLANEJAMENTO_PERIODO : agrupa
    ATIVIDADE ||--o{ PRECEDENCIA : predecessora
    ATIVIDADE ||--o{ PRECEDENCIA : sucessora
    ATIVIDADE ||--o{ RESULTADO_PERT_CPM : analisada

    ATIVIDADE {
        string id
        string id_pai
        string descricao
        float quantidade
        string unidade
    }
    COMPOSICAO {
        string id
        string descricao
        string unidade
        float custo_unitario
    }
    RECURSO_COMPOSICAO {
        string composicao_pai
        string insumo_ou_composicao_filha
        float coeficiente
    }
    INSUMO {
        string id
        string tipo
        string unidade
        float custo_unitario
    }
    PLANEJAMENTO_PERIODO {
        float quantidade_planejada
        float valor_planejado
    }
    PERIODO {
        date inicio
        date fim
    }
    PRECEDENCIA {
        string atividade_predecessora
        string atividade_sucessora
        string tipo
    }
    RESULTADO_PERT_CPM {
        float inicio_mais_cedo
        float termino_mais_cedo
        float folga
    }
```

Na extração descrita em [RULES.md](RULES.md), `MTAREFA` contém as atividades; `MCMP`, as composições; `MRECCMP`, suas linhas de recurso; e `MISM`, os insumos. `MTRFPLAN`/`MTRFPDO` e `MPERIODO` relacionam atividades e períodos. A extração não traz predecessoras explícitas: `PRECEDENCIA` e `RESULTADO_PERT_CPM` representam informações a levantar ou calcular, não tabelas confirmadas dessa extração.

## Fluxo convencional de orçamento e planejamento

Leia o diagrama **de cima para baixo**. Cada coluna representa uma parte do processo; as setas mostram as informações que passam entre elas. Os blocos numerados indicam a ordem principal de trabalho.

```mermaid
sequenceDiagram
    participant Eng as Engenheiro
    participant Cad as Cadastros
    participant Orc as Orçamento
    participant Plan as Planejamento

    rect rgb(235, 245, 255)
    Note over Eng,Orc: 1. Preparar o orçamento
    Eng->>Orc: Define EAP, atividades e quantidades
    Cad->>Orc: Fornece composições e custos unitários
    Note over Cad: Insumos formam composições auxiliares e de serviço
    Orc->>Orc: Associa composições às atividades
    Orc->>Orc: Quantidade × custo unitário = custo da atividade
    Orc->>Orc: Soma atividades e custos indiretos do projeto
    end

    rect rgb(240, 250, 240)
    Note over Orc,Plan: 2. Levantar a demanda total de recursos
    Orc->>Orc: Explode composições em materiais e horas de recursos
    Orc->>Orc: Calcula curva ABC por participação no custo
    Orc->>Plan: Envia quantidades e horas por atividade
    end

    rect rgb(255, 248, 230)
    Note over Eng,Plan: 3. Planejar e nivelar
    Eng->>Plan: Define precedências e durações
    Plan->>Plan: Calcula PERT/CPM, caminho crítico e folgas
    Eng->>Plan: Define calendário e jornada de trabalho
    Plan->>Plan: Distribui recursos por semana ou mês
    Plan->>Eng: Apresenta histogramas de pessoas e equipamentos
    Eng->>Plan: Ajusta datas de atividades com folga
    Plan->>Plan: Recalcula datas e confere recursos
    end
```

A explosão fornece as quantidades e horas totais; a curva ABC classifica os insumos por participação no custo. A sequência e as durações são definidas com apoio da experiência, de projetos anteriores e da bibliografia. A EAP organiza o escopo e não define, por si só, a sequência. O dimensionamento depende da jornada e utilização; ao deslocar atividades, é necessário conferir novamente as precedências e folgas.

Conforme o critério da empresa, alimentação e EPI podem compor os custos horários dos recursos diretos. Administração, mobilização e desmobilização são exemplos de custos que podem ser tratados separadamente como indiretos do projeto, sem dupla contagem.

## Proposta do trabalho: equipes, prazo e custo integrados

Cada atividade de serviço tem uma quantidade e alternativas de equipe habilitadas. Cada alternativa, ou **modo**, associa produtividade, formação, consumo de recursos e custo. A duração é obtida por `quantidade / produtividade`, com unidades compatíveis; por exemplo, 100 m³ a 20 m³/dia resultam em 5 dias úteis. O custo direto pode combinar custo diário de equipe e equipamento durante a execução com materiais e outros custos diretos pertinentes.

Nesta proposta, os custos de apoio antes incorporados ao custo horário do direto são tratados como indiretos, de acordo com as premissas escolhidas, sem duplicação. Custos indiretos dependentes do prazo aumentam ou diminuem com a duração do projeto; mobilização ou outros itens fixos entram uma única vez. A classificação de cada item deve ser documentada.

### Entidades propostas

```mermaid
erDiagram
    PROJETO ||--o{ ATIVIDADE : contem
    ATIVIDADE o|--o{ ATIVIDADE : "agrupa na EAP"
    ATIVIDADE ||--|{ MODO_ATIVIDADE : admite
    EQUIPE ||--o{ MODO_ATIVIDADE : caracteriza
    MODO_ATIVIDADE ||--o{ CONSUMO_RECURSO : exige
    RECURSO_COMPARTILHADO ||--o{ CONSUMO_RECURSO : limita
    ATIVIDADE ||--o{ PRECEDENCIA : predecessora
    ATIVIDADE ||--o{ PRECEDENCIA : sucessora
    ATIVIDADE ||--o{ ALOCACAO : recebe
    MODO_ATIVIDADE ||--o{ ALOCACAO : escolhido
    CENARIO ||--o{ ALOCACAO : registra
    CENARIO ||--o{ CUSTO_INDIRETO : inclui
    CALENDARIO ||--o{ CENARIO : orienta

    ATIVIDADE {
        string id
        float quantidade
        string unidade
    }
    MODO_ATIVIDADE {
        float produtividade
        float duracao_calculada
        float custo_direto
    }
    EQUIPE {
        string formacao
        float custo_diario
    }
    RECURSO_COMPARTILHADO {
        string tipo
        float disponibilidade
    }
    ALOCACAO {
        float inicio
        float termino
    }
    CUSTO_INDIRETO {
        string criterio
        float taxa_ou_valor_fixo
    }
```

`MODO_ATIVIDADE` representa a combinação habilitada de atividade e equipe: a produtividade e o custo podem depender da atividade. `ALOCACAO` registra a escolha em um cenário; conceitualmente, cada atividade executável recebe um modo por cenário. O catálogo de insumos e CPUs continua útil para fundamentar materiais e custos das alternativas, desde que as parcelas usadas no modelo sejam conciliadas.

### Fluxo de decisão

O diagrama segue a mesma leitura, de cima para baixo. O engenheiro prepara os dados; o modelo compara as alternativas e entrega uma solução para análise.

```mermaid
sequenceDiagram
    participant Eng as Engenheiro
    participant Cad as Cadastros
    participant PO as Modelo de PO
    participant Res as Resultado

    rect rgb(235, 245, 255)
    Note over Eng,PO: 1. Preparar os dados
    Eng->>PO: Informa atividades, quantidades e precedências
    Cad->>PO: Fornece equipes habilitadas, produtividade e custo
    Cad->>PO: Fornece materiais e custos de referência
    Eng->>PO: Informa disponibilidade, calendário e custos indiretos
    PO->>PO: Calcula duração e custo de cada alternativa
    end

    rect rgb(240, 250, 240)
    Note over PO,Res: 2. Escolher equipes e datas em conjunto
    PO->>PO: Considera precedências e limites dos recursos
    PO->>PO: Busca o menor custo total conforme as premissas
    PO->>Res: Entrega equipe escolhida e datas de cada atividade
    PO->>Res: Calcula prazo, custo direto e custo indireto
    end

    rect rgb(255, 248, 230)
    Note over Eng,Res: 3. Avaliar a solução
    Res->>Eng: Apresenta cronograma, custo total e histogramas
    Eng->>Eng: Analisa datas, folgas e distribuição dos recursos
    end
```

Ao mudar a equipe, mudam produtividade, duração e custo direto. A duração influencia o cronograma e o prazo do projeto; o prazo, por sua vez, influencia os custos indiretos dependentes do tempo. O custo total reúne custos diretos, indiretos e itens fixos, cada parcela contabilizada uma vez.

O modelo considera precedências e disponibilidade de recursos ao escolher equipes e inícios. O caminho crítico lógico deve ser interpretado junto às restrições de recursos; o PERT/CPM isolado não garante um cronograma executável. Histogramas ajudam a avaliar a distribuição das equipes, mas limitar recursos não significa necessariamente minimizar oscilações: para isso seria preciso um objetivo ou restrições adicionais.

**Situação do piloto:** a implementação atual já otimiza modos e inícios e inclui um indireto por dia de projeto, mobilização fixa e uma parcela de apoio por pessoa-dia. As parcelas de apoio ficam separadas dos salários e equipamentos do custo direto; sua classificação e seus valores precisam ser conciliados ao aplicar o modelo a uma obra. O piloto usa dados sintéticos, duração determinística e pools unitários; não otimiza explicitamente o nivelamento de histogramas nem usa calendários civis. Veja o [modelo matemático](outputs/otimizacao_piloto/modelo_matematico.md) e o [guia do piloto](outputs/otimizacao_piloto/LEIA-ME.md).

As sugestões bibliográficas fornecidas para fundamentar o trabalho estão em [referências bibliográficas](referencias/referencias_fornecidas.txt). O arquivo preserva as indicações e ressalvas recebidas; ele não contém os artigos e os dados bibliográficos precisam ser conferidos antes de sua citação.

## Modelo de minimização de custo: equações e implementação Python

Esta seção relaciona cada regra matemática ao código utilizado na análise. Os trechos em Python/Gurobi pertencem à função `solve()` de [resolver_gurobi.py](outputs/otimizacao_piloto/resolver_gurobi.py) e compartilham as variáveis preparadas nessa função. Para executar o modelo completo, use os comandos ao final da seção.

### Notação e dados de entrada

| Símbolo | Significado | Nome ou origem no Python |
|---|---|---|
| $A$ | Atividades de execução | `executable`, de `atividades.csv` |
| $E_i$ | Alternativas de equipe habilitadas para a atividade $i$ | `by_activity[i]`, de `habilitacoes_alternativas.csv` |
| $P$ | Pares predecessora–sucessora | `edges`, de `precedencias.csv` |
| $g(e)$ | Família de recurso compartilhado da alternativa $e$ | `pool[e]`, de `equipes.csv` |
| $Q_i$, $p_{i,e}$ | Quantidade do serviço e produtividade da alternativa | `QUANTIDADE`, `PRODUTIVIDADE_UNID_DIA` |
| $d_{i,e}$, $c_{i,e}$, $h_{i,e}$ | Duração, custo direto e efetivo de cada alternativa | `DURACAO_DIAS`, `CUSTO_DIRETO_TOTAL_INDICE`, `PESSOAS_EQUIPE` |
| $x_{i,e}$ | Variável binária de escolha da alternativa | `x[i, e]` |
| $S_i$, $D_i$ | Início e duração selecionada da atividade | `start[i]`, `duration[i]` |
| $T$ | Término do projeto contado a partir do dia zero | `end` |
| $C_f$, $c_t$, $c_h$ | Custo fixo, taxa indireta por dia útil e taxa de apoio por pessoa-dia | `cf`, `ct`, `ch`, de `custos_fixos.csv` e `premissas.csv` |
| $M$ | Horizonte usado para limitar as variáveis e desativar restrições condicionais | `horizon` |

Cada alternativa é uma formação possível de equipe, com mão de obra e equipamentos. Os perfis de uma mesma família compartilham a disponibilidade física dessa família. O marco `OP00` tem início e duração zero e não recebe equipe. Todos os custos atuais são pontos de índice sintéticos, sem moeda.

### Preparação: duração e custo de cada alternativa

Antes de resolver o modelo, calcula-se:

$$
d_{i,e}=\frac{Q_i}{p_{i,e}},\qquad p_{i,e}>0
$$

$$
c_{i,e}=k_{i,e}\,d_{i,e}+m_{i,e}
$$

Aqui, $k_{i,e}$ é o custo diário da equipe e equipamentos e $m_{i,e}$, o custo total dos materiais. Esses valores são parâmetros previamente calculados. O solver lê os valores do CSV; ele não estima produtividade.

**Script:** [gerar_base_otimizacao_piloto.py](outputs/otimizacao_piloto/gerar_base_otimizacao_piloto.py), no bloco que gera `habilitacoes_alternativas.csv`:

```python
productivity = task["std_productivity"] * profile["productivity_factor"]
duration = task["quantity"] / productivity
crew_day_cost = crew_equipment_day_std * profile["daily_cost_factor"]
crew_equipment_cost = crew_day_cost * duration
direct_cost = material_total + crew_equipment_cost
```

As produtividades e os multiplicadores do gerador são hipóteses acadêmicas. As durações são contínuas, sem arredondamento para dias inteiros.

### R1. Uma alternativa habilitada por atividade

$$
\sum_{e\in E_i}x_{i,e}=1 \qquad \forall i\in A
$$

Cada atividade recebe exatamente uma formação de equipe. Em `solve()`, apenas as alternativas com `HABILITADA = SIM` entram nas variáveis, e a ausência de alternativa habilitada provoca erro de validação.

```python
for i in executable:
    model.addConstr(
        gp.quicksum(x[i, e] for e in by_activity[i]) == 1,
        name=f"escolha_{i}",
    )
```

### R2. Duração correspondente à alternativa escolhida

$$
D_i=\sum_{e\in E_i}d_{i,e}x_{i,e} \qquad \forall i\in A
$$

Como apenas um $x_{i,e}$ vale 1, a expressão assume a duração da equipe escolhida. No código, `duration` é uma expressão linear, usada nas restrições seguintes; não é uma variável independente que o solver possa reduzir livremente.

```python
duration = {
    i: gp.quicksum(
        float(indexed[i, e]["DURACAO_DIAS"]) * x[i, e]
        for e in by_activity[i]
    )
    for i in ids
}
```

### R3. Respeitar as precedências técnicas

$$
S_i+D_i\le S_j \qquad \forall(i,j)\in P
$$

A sucessora só começa após o término da predecessora. A implementação usa relações término–início, sem defasagem. Os vínculos vêm de `precedencias.csv`, levantados separadamente da hierarquia da EAP.

```python
for k, edge in enumerate(edges):
    i, j = edge["PREDECESSORA"], edge["SUCESSORA"]
    model.addConstr(
        start[i] + duration[i] <= start[j],
        name=f"precedencia_{k}",
    )
```

### R4. Respeitar a disponibilidade dos recursos compartilhados

O piloto admite uma equipe disponível por família de recurso, conforme `recursos_compartilhados.csv`. Assim, duas atividades que escolham a mesma família não podem executar simultaneamente.

Definimos o indicador de uso da família $r$:

$$
z_{i,r}=\sum_{e\in E_i:g(e)=r}x_{i,e}
$$

Para cada par de atividades $i,j$ que pode usar essa família, a variável binária $y_{i,j,r}$ escolhe a ordem. Quando ambas usam $r$, $y=1$ impõe $i$ antes de $j$; $y=0$ impõe a ordem inversa:

$$
S_i+D_i\le S_j+M(3-z_{i,r}-z_{j,r}-y_{i,j,r})
$$

$$
S_j+D_j\le S_i+M(2-z_{i,r}-z_{j,r}+y_{i,j,r})
$$

Se uma das atividades não escolher a família, os termos com $M$ liberam a ordenação desse par. A implementação fica em `solve()`:

```python
for r in capacities:
    eligible = [
        i for i in executable
        if any(pool[e] == r for e in by_activity[i])
    ]
    for i, j in combinations(eligible, 2):
        zi = gp.quicksum(x[i, e] for e in by_activity[i] if pool[e] == r)
        zj = gp.quicksum(x[j, e] for e in by_activity[j] if pool[e] == r)
        order = model.addVar(vtype=GRB.BINARY, name=f"ordem_{r}_{i}_{j}")
        model.addConstr(
            start[i] + duration[i]
            <= start[j] + horizon * (3 - zi - zj - order)
        )
        model.addConstr(
            start[j] + duration[j]
            <= start[i] + horizon * (2 - zi - zj + order)
        )
```

`M = horizon` é calculado como a soma das maiores durações de cada atividade, mais um dia. Para uma rede acíclica, sem datas mínimas adicionais, esse horizonte comporta um cronograma inteiramente serial. A capacidade unitária é validada pelo script; capacidades maiores, recursos adicionais usados simultaneamente e disponibilidades variáveis exigem ampliar a formulação.

### R5. O prazo deve abranger todas as atividades

$$
T\ge S_i+D_i \qquad \forall i
$$

```python
for i in ids:
    model.addConstr(
        start[i] + duration[i] <= end,
        name=f"termino_{i}",
    )
```

Com $c_t>0$, minimizar o custo também pressiona `end` para o término da última atividade. Se $c_t=0$, essa igualdade não é garantida pela função objetivo; o resumo do script calcula o prazo efetivo como o maior término do cronograma.

### R6. Prazo máximo, quando houver exigência

$$
T\le T_{\max}
$$

Esta restrição é opcional e é ativada pelo argumento `--prazo-maximo` do solver Gurobi. Um prazo incompatível com as precedências e os recursos pode tornar o problema inviável.

```python
if deadline is not None:
    model.addConstr(end <= deadline, name="prazo_limite")
```

### R7. Domínios das variáveis e marco inicial

$$
x_{i,e},y_{i,j,r}\in\{0,1\},\qquad
0\le S_i\le M,\qquad 0\le T\le M,\qquad S_{OP00}=0
$$

Inícios e prazo são contínuos em dias úteis. O marco inicial fixa a origem temporal do projeto.

```python
x = model.addVars(list(indexed), vtype=GRB.BINARY, name="modo")
start = model.addVars(ids, lb=0, ub=horizon, name="inicio")
end = model.addVar(lb=0, ub=horizon, name="prazo")
model.addConstr(start["OP00"] == 0, name="marco_inicial")
```

As variáveis binárias de ordem são criadas no trecho de R4. A disponibilidade e a habilitação das equipes vêm dos cadastros; o solver não pode contratar recursos adicionais por conta própria.

### FO. Função objetivo: minimizar o custo total

O modelo implementado minimiza:

$$
\min C_{total}=
C_f+
\underbrace{\sum_{i\in A}\sum_{e\in E_i}c_{i,e}x_{i,e}}_{C_{direto}}+
\underbrace{c_tT+c_h\sum_{i\in A}\sum_{e\in E_i}h_{i,e}d_{i,e}x_{i,e}}_{C_{indireto\ variavel}}
$$

| Parcela | Interpretação |
|---|---|
| $C_f$ | Mobilização de apoio, contabilizada uma única vez |
| $c_{i,e}x_{i,e}$ | Equipe, equipamentos e materiais da alternativa escolhida |
| $c_tT$ | Administração/canteiro por tempo de permanência da obra |
| $c_hh_{i,e}d_{i,e}x_{i,e}$ | Apoio por pessoa-dia, separado dos salários e equipamentos diretos |

O custo fixo entra no total, mas, por ser igual para todas as soluções deste piloto, não altera a escolha ótima. As taxas $c_t$ e $c_h$ são lidas de `premissas.csv`; não são calculadas como percentual do custo direto.

**Script:** [resolver_gurobi.py](outputs/otimizacao_piloto/resolver_gurobi.py), função `solve()`:

```python
direct = gp.quicksum(
    float(row["CUSTO_DIRETO_TOTAL_INDICE"]) * x[i, e]
    for (i, e), row in indexed.items()
)
person_days = gp.quicksum(
    float(row["PESSOAS_EQUIPE"])
    * float(row["DURACAO_DIAS"])
    * x[i, e]
    for (i, e), row in indexed.items()
)
model.setObjective(cf + direct + ch * person_days + ct * end, GRB.MINIMIZE)
model.optimize()
```

Uma equipe mais cara e produtiva pode compensar quando reduz o prazo do projeto e o custo de permanência. A redução de uma atividade com folga pode não alterar esse prazo. O solver avalia o efeito conjunto das durações, precedências e disputas pelos recursos.

### Indicador de qualidade: relação indireto/direto

Os **20% são uma referência de avaliação do orçamento**, para investigar a coerência da estrutura de apoio. Esse percentual não define o custo indireto e não impõe um teto no modelo.

Para avaliar o conjunto dos indiretos do piloto, incluindo a mobilização de apoio:

$$
I_{indireto/direto}=100\,
\frac{C_f+c_tT+c_h\sum_{i\in A}\sum_{e\in E_i}h_{i,e}d_{i,e}x_{i,e}}
{C_{direto}}
$$

O exemplo de pós-processamento abaixo pode ser executado em Python, a partir da raiz do projeto, após gerar `resumo_gurobi.json`. Ele calcula o indicador; ainda não há uma coluna automática com esse percentual no resumo do solver.

```python
import json
from pathlib import Path

path = Path("outputs/otimizacao_piloto/resultados_gurobi/resumo_gurobi.json")
resultado = json.loads(path.read_text(encoding="utf-8"))
direto = resultado["custo_direto_indice"]
indireto = (
    resultado["custo_fixo_indice"]
    + resultado["custo_indireto_prazo_indice"]
    + resultado["custo_indireto_efetivo_indice"]
)
indicador = 100 * indireto / direto if direto > 0 else None
print({"indireto_sobre_direto_pct": indicador, "referencia_pct": 20.0})
```

Para avaliar especificamente o inchaço da administração, é necessário delimitar quais itens administrativos entram no numerador e manter o mesmo critério em todos os cenários. O percentual deve ser lido junto dos custos absolutos e do prazo: ele também pode cair quando o custo direto aumenta.

### Scripts utilizados e sequência de análise

| Etapa | Script e função | Responsabilidade |
|---|---|---|
| Preparar alternativas e referência factível | [gerar_base_otimizacao_piloto.py](outputs/otimizacao_piloto/gerar_base_otimizacao_piloto.py), incluindo `schedule_fixed_assignment()` | Calcula durações e custos, gera os CSVs e programa as equipes padrão respeitando recursos |
| Resolver em Gurobi | [resolver_gurobi.py](outputs/otimizacao_piloto/resolver_gurobi.py), `solve()` | Implementa R1–R7 e FO; verifica precedências, sobreposições e eventual prazo máximo após resolver |
| Resolver em SciPy/HiGHS | [resolver_piloto.py](outputs/otimizacao_piloto/resolver_piloto.py), `solve_model()` | Formula escolha, precedências, capacidade, término e objetivo em matrizes; a interface atual não recebe prazo máximo e pressupõe alternativas previamente habilitadas |
| Analisar sensibilidade | [analisar_sensibilidade.py](outputs/otimizacao_piloto/analisar_sensibilidade.py), `main()` | Reotimiza via SciPy para diferentes taxas de indiretos e compara soluções reprecificadas nas taxas-base |

Os CSVs de entrada já estão em `outputs/otimizacao_piloto/dados_modelo/`. Com ambiente e licença configurados, execute na raiz:

```powershell
# Resolver o cenário-base de taxas, escolhendo equipes e datas.
.\.venv\Scripts\python.exe outputs/otimizacao_piloto/resolver_gurobi.py

# Resolver uma alternativa com prazo máximo de 25 dias úteis.
.\.venv\Scripts\python.exe outputs/otimizacao_piloto/resolver_gurobi.py --prazo-maximo 25 --output-dir outputs/otimizacao_piloto/gurobi_prazo_25

# Reotimizar a sensibilidade das taxas pela implementação SciPy.
.\.venv\Scripts\python.exe outputs/otimizacao_piloto/analisar_sensibilidade.py
```

O Gurobi grava cronograma e resumo na pasta de saída; a sensibilidade atualiza seus CSVs em `dados_modelo`. Compare custos sob as mesmas taxas e registre status, gap e viabilidade. Calendários civis, nivelamento de histogramas como objetivo e escolha do tamanho da administração são extensões futuras; não integram as restrições acima.

## Organização

- `scripts/`: geradores e rotinas de transformação das bases.
- `dados_anonimizados/`: versões separadas das bases anonimizadas da obra, mantidas localmente.
- `dados_simulados/`: bases sintéticas e exemplos acadêmicos independentes.
- `dados_simulados/eap_academica_sintetica/`: exemplo acadêmico resumido, CPUs e seu gerador.
- `dados_simulados/eap_academica_sintetica_escala_exemplo/`: exemplo acadêmico em escala ampliada.
- `outputs/otimizacao_piloto/`: modelo piloto, resultados e instruções de execução.
- `trabalho_final/`: artigo e roteiro do seminário.
- `referencias/`: indicações bibliográficas fornecidas para o trabalho.
- `RULES.md`: premissas, relacionamento das tabelas e instruções de reprodução.
- `APRESENTACAO.sty`: estilo LaTeX utilizado no trabalho.

O workspace também pode conter bases anonimizadas e resultados de análises de uma obra. Eles permanecem locais e estão no `.gitignore`, assim como a base sintética derivada da obra e o script de anonimização com caminhos locais. Os exemplos acadêmicos independentes continuam disponíveis para versionamento.

## Reprodução

### Gurobi no Windows

O Gurobi para Python pode ser instalado em um ambiente virtual local:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install gurobipy
$env:GRB_LICENSE_FILE = (Resolve-Path .\gurobi.lic).Path
.\.venv\Scripts\python.exe -c "import gurobipy; print(gurobipy.gurobi.version())"
```

Defina `GRB_LICENSE_FILE` em cada terminal que for executar o Gurobi, se a licença não for descoberta automaticamente. A licença é pessoal, permanece fora do Git e pode exigir conexão com o servidor de licenças. O piloto agora possui implementação nativa em Gurobi, além da implementação anterior em `scipy.optimize.milp`:

```powershell
.\.venv\Scripts\python.exe outputs/otimizacao_piloto/resolver_gurobi.py
```

O resultado usa dados acadêmicos sintéticos e não é um orçamento real. Veja opções e limitações no [guia do piloto](outputs/otimizacao_piloto/LEIA-ME.md).

Execute os comandos a partir da raiz do projeto. Os geradores de EAP exigem uma pasta de saída que ainda não exista:

```powershell
python scripts/criar_eap_academica_sintetica.py --output eap_nova
python scripts/criar_eap_academica_escala.py --output eap_escala_nova
```

Para o piloto, consulte [as instruções específicas](outputs/otimizacao_piloto/LEIA-ME.md), incluindo as dependências e as premissas do modelo. A EAP de referência está em `dados_simulados/eap_academica_sintetica_escala_exemplo/`; as entradas efetivamente lidas pelos solvers estão em `outputs/otimizacao_piloto/dados_modelo/`.

Antes de publicar, revise o conteúdo que será incluído no repositório, inclusive artigo, documentação, planilhas e histórico. A exclusão por `.gitignore` não garante anonimização nem remove arquivos já adicionados ao Git.
