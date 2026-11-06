# Regras do trabalho — orçamento, anonimização e uso das tabelas

## 1. Objetivo e base local

Este trabalho usa a extração anonimizada de uma única versão do projeto, armazenada em `dados_anonimizados/dados_anonimizados_base_completa/`. Não combinar tabelas de versões diferentes, nem acrescentar o histograma de outra revisão sem uma decisão explícita e uma validação dos vínculos.

A pasta contém as tabelas RM exportadas em CSV, `dicionario_colunas.csv`, `LEIA-ME.txt` e `manifesto_anonimizacao.json`. Os arquivos CSV usam `;` como separador e preservam chaves para relacionamento entre tabelas.

## 2. Como o orçamento da obra se organiza

O orçamento começa pela **EAP**, que organiza a obra em atividades e subatividades. Cada atividade orçamentária pode ser associada a uma composição de serviço. A composição pode usar diretamente insumos ou usar outra composição como recurso. Uma composição auxiliar, por exemplo, pode reunir salário, hora extra e outros insumos de mão de obra; essa composição passa a ser um recurso de uma composição de serviço maior. A composição maior pode, por sua vez, ser usada por outra composição.

Assim, o vínculo é uma árvore ou rede de dependências:

```text
EAP / atividade
└── composição de serviço associada
    ├── insumo cadastrado
    └── composição auxiliar
        ├── insumo de mão de obra
        └── outros insumos
```

As quantidades e os valores dos níveis inferiores determinam os valores dos níveis superiores. Quando um insumo, coeficiente ou preço for alterado, os custos dependentes precisam ser recalculados de baixo para cima: linhas de recursos, composições auxiliares, composições de serviço, atividade e totais do projeto. Não editar isoladamente o total superior para fazê-lo parecer consistente.

O cálculo real do RM/Compor pode incluir produtividade, mão de obra produtiva e improdutiva, leis sociais, BDI, DMT, fórmulas e outros fatores. Portanto, `quantidade × valor unitário` é uma verificação útil em campos que tenham essa regra, mas não deve ser presumida para toda linha de `MRECCMP`. Usar as regras de cálculo da composição e comparar com a extração original antes de implementar uma recálculo.

## 3. Regra de anonimização que preserva o orçamento

Não aplicar, de forma independente, o mesmo multiplicador a **quantidades, preços unitários e totais já calculados**. Isso altera os dois lados das relações de cálculo sem recalcular os totais. Por exemplo, se quantidade e preço unitário forem multiplicados por `f`, o produto passa a variar por `f²`, enquanto um total que foi multiplicado apenas por `f` deixa de corresponder a eles.

Para produzir uma base anonimizada consistente:

1. Identificar quais campos são **entradas primitivas** (por exemplo, preço de insumo e coeficiente de consumo) e quais são **valores derivados** (totais de linhas, composições, atividades e projeto).
2. Definir se quantidades também precisam ser anonimizadas. Se forem alteradas, recalcular todos os valores dependentes usando as regras efetivas da composição. Se não houver fórmula confiável para recalcular uma classe de quantidade, preservá-la e anonimizar os valores monetários de forma uniforme é mais seguro para a consistência do orçamento.
3. Recalcular em ordem inversa da dependência: insumos/recursos → composições auxiliares → composições de serviço → atividades da EAP → totais e valores planejados derivados.
4. Validar somas, fórmulas, vínculos e ausências de referências antes de usar a base em análises ou apresentar resultados.

### Situação da base atual

`dados_anonimizados/dados_anonimizados_base_completa/` é uma versão anonimizada preliminar. Ela escalou colunas de quantidades e de valores monetários, mas não recalculou todos os totais dependentes. Na auditoria, 1.352 linhas de atividade com composição vinculada satisfaziam a relação entre quantidade, valor unitário e valor total na origem; na base atual, 935 dessas linhas deixaram de satisfazê-la. **Não tratar a base atual como orçamento reconciliado** até refazer a anonimização ou recalcular os campos dependentes.

O campo original `MTAREFA.INDIRETO` estava zerado em todas as linhas e não foi usado como regra de classificação.

## 4. Relação de cada tabela salva

| Arquivo | Papel no modelo | Chaves e campos úteis |
|---|---|---|
| `MPRJ.csv` | Dados e totais do projeto. A identificação foi anonimizada. | `IDPRJ`; campos de valores totais do projeto. |
| `MTAREFA.csv` | EAP e cadastro das atividades/subatividades. | `IDTRF` identifica a tarefa; `IDPAI` identifica o pai na hierarquia; `CODTRF` é o código EAP; `IDCMP` liga a atividade à composição; quantidade, custos, valores e datas. Inclui `CLASSIFICACAO_ATIVIDADE`. |
| `MCMP.csv` | Cadastro de composições de serviço e composições auxiliares, com custos e parâmetros calculados. | `IDCMP` identifica a composição; códigos, descrição, unidade, valores e custos. |
| `MRECCMP.csv` | Itens que formam cada composição: insumos ou composições filhas. É a tabela central para percorrer a árvore de custos. | `IDCMP` é a composição pai; `IDISM` aponta para insumo; `IDCMPFILHA` aponta para composição filha; `IDREC` identifica o recurso; `QUANTIDADE`, fatores e valores da linha. |
| `MISM.csv` | Cadastro de insumos, como materiais e itens de mão de obra, com unidade e preços/custos. | `IDISM` identifica o insumo; descrição, unidade e campos de valor/custo. |
| `MGIS.csv` | Grupos de custo e parâmetros associados, como BDI e leis sociais. | `IDGIS`; grupo, BDI, leis sociais e parâmetros. |
| `MTRFPLAN.csv` | Valores, percentuais e quantidades planejados por atividade e período. | `IDTRF`, `NUMPERIODO`, `PERCPLANEJADO`, `QUANTPLANEJADO`, valores. Conferir/recalcular valores se o total da atividade mudar. |
| `MTRFBASE.csv` | Linha de base de quantidades e valores por atividade e período. | `IDTRF`, `NUMPERIODO`, `PERCBASE`, `QUANTBASE`, valores. |
| `MTRFPDO.csv` | Calendário/perfil por atividade e período, com produção planejada, quantidade e valor planejado. | `IDTRF`, `IDPERIODO`, `NUMDIAS`, `NUMHORASTURNO`, `NUMTURNOS`, produção, quantidade e valor. `CAMPO_05` a `CAMPO_10` são posições sem valores cuja ordem física não foi confirmada. |
| `MPERIODO.csv` | Cadastro de períodos e suas datas. | `IDPERIODO`, `DTINICIO`, `DTFIM`. |
| `MTRFMED.csv` | Medições associadas a itens contratuais. | A extração local não tem linhas para o projeto; foi mantido apenas o cabeçalho. |
| `MTRFMEDIDO.csv` | Medições por tarefa e período. | A extração local não tem linhas para o projeto; foi mantido apenas o cabeçalho. |
| `dicionario_colunas.csv` | Relação das colunas e suas posições nos CSVs gerados. | Metadado para leitura dos arquivos; não é tabela de orçamento. |

## 5. Regras de relacionamento

- `MTAREFA.IDCMP` → `MCMP.IDCMP`: composição associada à atividade.
- `MRECCMP.IDCMP` → `MCMP.IDCMP`: composição pai da linha de recurso.
- `MRECCMP.IDCMPFILHA` → `MCMP.IDCMP`: composição auxiliar/filha usada como recurso.
- `MRECCMP.IDISM` → `MISM.IDISM`: insumo usado diretamente na composição.
- `MTAREFA.IDPAI` → `MTAREFA.IDTRF`: pai da atividade na EAP. Esse vínculo representa hierarquia, **não** predecessora de cronograma.
- `MTRFPLAN.IDTRF`, `MTRFBASE.IDTRF` e `MTRFPDO.IDTRF` → `MTAREFA.IDTRF`: ligação do cronograma/calendário à atividade.
- `MPERIODO.IDPERIODO` → períodos referenciados pelas tabelas de planejamento/calendário.

Antes de agregar, confirmar se os IDs estão preenchidos, se as chaves têm a mesma coligada/projeto e se não há órfãos. Uma composição filha deve ser calculada antes da composição que a consome.

## 6. Classificação direta, indireta e em dúvida

`MTAREFA.CLASSIFICACAO_ATIVIDADE` usa os ramos da EAP como evidência, não o campo original `INDIRETO`:

- **INDIRETA:** `01.16` (mão de obra indireta) e `01.17` (equipamentos indiretos), incluindo seus descendentes.
- **DIRETA:** escopos de execução `01.04` a `01.08`, `01.10`, `01.11` e `01.14`, incluindo seus descendentes.
- **DUVIDA:** mobilização, instalações, serviços preliminares/complementares, gerenciamento, locações, serviços TAC, taxas/verbas, agrupadores e códigos fora das regras explícitas. Validar com o critério contábil/operacional da obra.

A classificação é indicativa; não substitui validação da equipe de orçamento. O manifesto informa contagens de todas as linhas e das atividades-folha separadamente.

## 7. Uso para PERT/CPM

`MTAREFA` fornece atividades e hierarquia; `MTRFPLAN`, `MTRFBASE`, `MTRFPDO` e `MPERIODO` fornecem dados temporais planejados. A hierarquia EAP não define dependências lógicas. Como não há predecessoras explícitas nesta extração, relações de precedência para o PERT/CPM precisam ser levantadas ou justificadas separadamente. As tabelas de medição vazias também não permitem calibrar durações com realizado.

## 8. Script de atualização dos valores

`atualizar_valores_orcamento.py` lê a base anonimizada, cria uma nova pasta de saída e não sobrescreve a entrada. O processamento segue a árvore de dependências: insumos/recursos, composições, atividades vinculadas e agrupadores da EAP. Valores monetários do cronograma são redistribuídos pelo novo total da tarefa, preservando a participação entre períodos.

```powershell
python scripts/atualizar_valores_orcamento.py
```

O script atualiza linhas de recurso quando a regra produtiva validada é aplicável e quando não há coeficiente improdutivo. Linhas com coeficiente improdutivo, coeficiente produtivo inválido ou referência ausente permanecem com o total de entrada e são registradas em `relatorio_recalculo.json`. A saída fica marcada como `recalculado_com_pendencias` nesses casos. Use `--strict` para cancelar a geração da cópia se houver qualquer pendência. Antes de chamar o orçamento de totalmente reconciliado, revisar essas linhas e confirmar a fórmula de cálculo correspondente.

Na conferência desta extração, 102 linhas de recurso (23 ligadas a insumos e 79 a composições filhas) não puderam ser reproduzidas com a fórmula produtiva simples por envolverem coeficientes improdutivos. Elas são mantidas como pendência pelo script.

Referências oficiais úteis para interpretar exceções de cálculo:

- [TOTVS — Insumo percentual na composição](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360031399214-TOTVS-Constru%C3%A7%C3%A3o-Obras-e-Projetos-TCOP-Como-Utilizar-Insumo-Percentual-na-Composi%C3%A7%C3%A3o)
- [TOTVS — Curva ABC de composições e serviços auxiliares](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360033991154-TOTVS-Constru%C3%A7%C3%A3o-Obras-e-Projetos-TCOP-Como-Gerar-a-Curva-ABC-do-seu-Projeto)

## 9. Cópia sintética para apresentação acadêmica

`criar_base_sintetica_pesquisa.py` gera `dados_simulados/dados_sinteticos_pesquisa_operacional/` a partir da cópia recalculada `dados_anonimizados/dados_anonimizados_orcamento_atualizado/`, sem alterar a entrada. A execução atual foi conferida e registrou zero divergências nas somas das composições, atividades vinculadas e agrupadores da EAP.

- Os valores monetários são pontos de índice, com total da raiz da EAP igual a 1.000; não representam reais.
- As quantidades são índices sem unidade física: a maior quantidade positiva de atividade por categoria de unidade passa a 1.000, e as demais mantêm proporção. Os preços unitários são ajustados para preservar os totais em índice.
- IDs, códigos de cadastro, unidades, descrições e metadados de autoria são substituídos ou removidos; as datas de calendário são deslocadas para uma linha do tempo sintética.
- A hierarquia e as chaves entre tabelas, as classes `DIRETA`/`INDIRETA`/`DUVIDA` e as durações são preservadas para permitir análise estrutural.
- A cópia continua preservando parte das proporções e do desenho do orçamento. Não é uma garantia de anonimização absoluta, não autoriza divulgação por si só e não deve ser usada para orçamento ou execução da obra.
- As pendências de fórmula da base anterior continuam indicadas no relatório sintético. A extração ainda não fornece predecessoras explícitas para PERT/CPM.

Para gerar outra cópia, escolha uma pasta de saída que ainda não exista:

```powershell
python scripts/criar_base_sintetica_pesquisa.py --output dados_sinteticos_pesquisa_operacional_nova
```

## 10. EAP acadêmica independente e PERT/CPM hipotético

`criar_eap_academica_sintetica.py` produz `dados_simulados/eap_academica_sintetica/`. Esse gerador não lê as tabelas reais nem a cópia sintética derivada delas. A EAP, atividades, predecessoras, durações e pontos de custo são premissas novas para um caso genérico de infraestrutura linear.

- `EAP_sintetica.csv` organiza 31 elementos por projeto, fase, conta de controle e pacote de trabalho; os pacotes totalizam 1.000 pontos de custo sem moeda.
- `PERT_CPM_sintetico.csv` apresenta 17 atividades discretas, dois marcos, estimativas otimista/provável/pessimista, duração PERT e cálculo CPM de início/fim cedo e tarde, folga e caminho crítico.
- `dependencias_sinteticas.csv` lista as 25 relações hipotéticas finish-to-start.
- `A18` e `A19` são pacotes contínuos de suporte (LOE), incluídos nos pontos da EAP e excluídos da rede CPM para não criar uma duração artificial.
- A classificação direta/indireta/em dúvida é didática, as durações são em dias úteis presumidos e os custos são pontos de índice. Não representam a obra, não devem ser tratados como orçamento real nem como cronograma aprovado.

O modelo segue a ideia de decompor entregas na WBS/EAP e derivar dela as atividades de cronograma; a sequência e as dependências foram definidas como hipóteses do caso. Referências: GAO, [Schedule Assessment Guide](https://www.gao.gov/assets/gao-12-120g.pdf); FHWA, [Guide for Construction Contract Time Determination Procedures](https://www.fhwa.dot.gov/construction/contracts/t508015.cfm).

## 11. CPUs para a EAP acadêmica e referências SINAPI

`dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py` lê somente uma EAP sintética passada com `--eap` (ou a EAP resumida padrão). Não lê as tabelas derivadas da obra nem `dados_simulados/dados_sinteticos_pesquisa_operacional/`. Seu objetivo é conectar a EAP acadêmica independente a composições ilustrativas sem reutilizar o orçamento do projeto.

### Arquivos e vínculos

| Arquivo | Papel |
|---|---|
| `dados_simulados/eap_academica_sintetica/CPUs_EAP_sinteticas.csv` | Cabeçalho de CPU para cada pacote de trabalho: quantidade hipotética, unidade, custo unitário e total em pontos de índice, além dos metadados de referência. |
| `dados_simulados/eap_academica_sintetica/Itens_CPU_EAP_sinteticas.csv` | Itens da CPU: coeficiente, preço unitário de índice sintético, custo da linha e origem do coeficiente. |
| `dados_simulados/eap_academica_sintetica/Vinculo_EAP_CPU.csv` | Relação de cada pacote/atividade da EAP com a CPU didática e o escopo coberto por eventual referência pública. |
| `dados_simulados/eap_academica_sintetica/Referencias_SINAPI_publicas.csv` | Catálogo das referências da CAIXA/SINAPI selecionadas, links, revisão e notas de cobertura. |
| `dados_simulados/eap_academica_sintetica/Conferencia_rollup_EAP_CPU.csv` | Conferência do roll-up de custos dos itens para a CPU, pacote e nós pais da EAP. |
| `dados_simulados/eap_academica_sintetica/premissas_cpus_sinapi.md` | Premissas, limites e fontes para o modelo de CPUs. |

As cinco referências públicas parciais são SINAPI 95568 (tubo pluvial específico DN 400 mm), 102680 (dreno profundo específico), 105534 (produção de mistura solo-brita-cimento), 104361 (produção de mistura asfáltica) e 103751 (defensa metálica). Elas não cobrem todo o escopo dos pacotes amplos da EAP; os complementos estão identificados como sintéticos. Os pacotes sem referência selecionada adequada usam CPUs somente sintéticas.

### Regras de custo e hierarquia

- Somente descrições e coeficientes identificados como SINAPI são retirados dos Cadernos Técnicos oficiais da CAIXA. Nenhum preço SINAPI, custo regional ou valor monetário do projeto foi usado.
- A situação e a revisão das referências são registradas conforme constam nos cadernos consultados; isso não afirma que a base ao vivo permaneça inalterada.
- A Nota SINAPI 12/2025 nº 01 da CAIXA informou publicação de relatórios com preços/custos zerados a partir da referência outubro/2025; a Nota 12/2025 nº 02 registrou que os relatórios de outubro e novembro/2025 foram retificados em 22/12/2025 com informações de preços recebidas do IBGE. Alguns cadernos também marcam referências como sem custo. Este modelo não usa preço SINAPI; para monetizar, conferir o relatório mais recente da UF e competência escolhidas. Todos os valores unitários deste modelo são pontos de índice sintéticos, sem moeda, calibrados para preservar os 1.000 pontos da EAP hipotética.
- Quantidades de pacote, coeficientes de itens complementares e preços unitários de índice são hipotéticos. Não são medições nem quantidades da obra real.
- A tabela preserva os tipos C/I e coeficientes disponíveis nos cadernos. Este modelo não expande recursivamente cada item C até os insumos primitivos; o preço de índice calculado para esse item é uma proxy sintética agregada. Não descrever o modelo como orçamento SINAPI integralmente aberto ou precificado.
- A ordem de roll-up é: linha de componente → CPU → pacote da EAP → nó pai. Regerar a base após qualquer alteração de quantidade, coeficiente, índice unitário ou custo do pacote para recalcular os derivados e a conferência.

Recrie os arquivos a partir da raiz do workspace:

```powershell
python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py
```

## 12. EAP acadêmica em escala comparável ao exemplo

`criar_eap_academica_escala.py` cria `dados_simulados/eap_academica_sintetica_escala_exemplo/`. O modelo tem 1.849 nós: 450 agrupadores e 1.399 atividades detalhadas. A contagem agregada dos nós foi usada somente para escolher o tamanho; descrições, atividades, quantidades, custos, durações e precedências foram criados para o caso acadêmico, sem leitura ou cópia de linhas da obra.

- `EAP_sintetica.csv` apresenta os 1.849 elementos, com quantidade-modelo e arquétipo de CPU nas atividades de detalhe.
- `PERT_CPM_sintetico.csv` contém 1.379 atividades discretas, dois marcos e estimativas PERT/CPM; 20 atividades de apoio contínuo são LOE e ficam fora da rede.
- `dependencias_sinteticas.csv` registra as 1.613 relações hipotéticas finish-to-start.
- `CPUs_EAP_sinteticas.csv` contém uma CPU por atividade detalhada; `Itens_CPU_EAP_sinteticas.csv` lista seus 9.826 componentes. Cinco referências SINAPI são usadas parcialmente onde há aderência técnica; o restante é sintético ou complemento sintético.
- O roll-up de itens → CPU → atividade → agrupadores fecha em 1.000 pontos de índice, sem moeda e sem divergência. Preços unitários e quantidades-modelo são premissas acadêmicas, não preços SINAPI nem dados da obra.
- Itens SINAPI do tipo C não são expandidos recursivamente até insumos primitivos; seus custos de índice são proxies sintéticas. Não apresentar este material como orçamento SINAPI completo.

Gere a EAP e as CPUs a partir da raiz do workspace:

```powershell
python scripts/criar_eap_academica_escala.py
python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py --eap dados_simulados/eap_academica_sintetica_escala_exemplo/EAP_sintetica.csv --output-dir dados_simulados/eap_academica_sintetica_escala_exemplo
```
