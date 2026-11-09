# Pesquisa operacional aplicada ao planejamento de obras

Projeto acadêmico com modelos sintéticos de EAP, composições de custos e planejamento de atividades. O modelo piloto explora alternativas de cronograma e custos com recursos limitados.

## A ideia em uma leitura

No orçamento convencional, as quantidades de serviços e as composições determinam o custo; o cronograma e a distribuição dos recursos são desenvolvidos a partir das durações e precedências. Neste trabalho, investigamos uma decisão integrada: **qual equipe habilitada executar em cada atividade e quando**, considerando que sua produtividade altera a duração e que o prazo afeta os custos indiretos do projeto.

Termos úteis: **EAP** é a decomposição hierárquica do trabalho; **composição de custo unitário (CPU)** reúne os recursos necessários por unidade de serviço; **PERT/CPM** analisa a rede de precedências, datas e folgas; e **PO** é pesquisa operacional. Uma relação pai–filho na EAP não é, por si só, uma precedência entre atividades.

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

**Situação do piloto:** a implementação atual já otimiza modos e inícios e inclui um indireto por dia de projeto, mobilização fixa e uma parcela de apoio por pessoa-dia. Essa última parcela ainda existe no piloto; a separação de custos desejada acima precisa ser validada e, se adotada, implementada e conciliada. O piloto usa dados sintéticos, duração determinística e pools unitários; não otimiza explicitamente o nivelamento de histogramas nem usa calendários civis. Veja o [modelo matemático](outputs/otimizacao_piloto/modelo_matematico.md) e o [guia do piloto](outputs/otimizacao_piloto/LEIA-ME.md).

As sugestões bibliográficas fornecidas para fundamentar o trabalho estão em [referências bibliográficas](referencias/referencias_fornecidas.txt). O arquivo preserva as indicações e ressalvas recebidas; ele não contém os artigos e os dados bibliográficos precisam ser conferidos antes de sua citação.

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

Para o piloto, consulte [as instruções específicas](outputs/otimizacao_piloto/LEIA-ME.md), incluindo as dependências e as premissas do modelo. Os dados de entrada para esse piloto estão em `dados_simulados/eap_academica_sintetica_escala_exemplo/`.

Antes de publicar, revise o conteúdo que será incluído no repositório, inclusive artigo, documentação, planilhas e histórico. A exclusão por `.gitignore` não garante anonimização nem remove arquivos já adicionados ao Git.
