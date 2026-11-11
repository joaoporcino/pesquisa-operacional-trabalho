# Recorte ampliado de tarefas para o trabalho

Este caso sintético contém 68 tarefas executáveis, um marco inicial, 92 relações término-início e 204 alternativas de equipe. Há quatro setores, cada um com uma tarefa-folha distinta de cada uma das 17 famílias discretas da EAP acadêmica. Cada linha de `atividades.csv` aponta para uma única folha da EAP, sem reutilização das folhas entre tarefas. Os dois custos fixos são folhas adicionais, contabilizadas uma vez. O recorte continua sendo uma amostra da EAP ampliada, que tem 1.379 tarefas discretas; não é o projeto integral nem uma reprodução da obra anonimizada.

`PERT_CPM_sem_recursos.csv` contém uma linha por tarefa e pelo marco. `precedencias.csv` registra os vínculos FS de duração zero entre tarefas; não há agrupadores na rede. Em cada setor, por exemplo, drenagem transversal e movimentação de terra podem começar após a preparação da frente, e os quatro setores podem avançar simultaneamente. Essa lógica é uma hipótese didática criada por família e setor; a seleção de uma folha por família não constitui um levantamento de engenharia. As durações otimista e pessimista são variações simétricas hipotéticas da duração padrão, sem dados para estimar risco probabilístico.

O CPM lógico com equipe padrão e sem restrição de recursos tem 29,19 dias úteis e 278 pares de tarefas com intervalos sobrepostos. O cronograma de referência com equipes padrão respeita os seis pools de capacidade unitária, dura 72,40 dias e custa 63,1934 pontos de índice. Os custos são sintéticos e sem moeda. O cenário-base é produzido por heurística, não é solução ótima. Quantidades de um pacote-modelo e produtividades foram calibradas a durações sintéticas, não são medições físicas.

Na execução Gurobi registrada em `resultados_ampliado/`, o limite de 30 segundos produziu uma solução factível de 50,16 dias e 60,65355 pontos, com limite inferior 56,06085 e gap de 7,57%. As precedências e capacidades foram verificadas; a otimalidade não foi comprovada. A comparação com a referência depende das hipóteses deste recorte e não mede economia em obra real.

Os arquivos `atividades.csv`, `precedencias.csv`, `habilitacoes_alternativas.csv`, `equipes.csv`, `recursos_compartilhados.csv` e `premissas.csv` estão em `dados_modelo_ampliado/`. `verificacoes.json` registra checagens de ciclos, custos, durações e viabilidade do cenário-base. `cenario_base_com_equipes.csv` apresenta a alocação factível. O modelo de otimização pode usar o mesmo formato, mas o tamanho maior aumenta o tempo de solução; a qualidade deve ser avaliada pelo status e gap do solver, sem presumir otimalidade.

Para reproduzir, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe outputs/otimizacao_piloto/gerar_recorte_ampliado.py --force
.\.venv\Scripts\python.exe outputs/otimizacao_piloto/resolver_gurobi.py --data-dir outputs/otimizacao_piloto/dados_modelo_ampliado --output-dir outputs/otimizacao_piloto/resultados_ampliado --tempo-limite 30 --gap 0.01
```

O gerador sobrescreve os arquivos gerados do recorte com `--force`. O piloto original, seus resultados e comparações continuam em pastas próprias e não devem ser associados aos indicadores deste recorte. As precedências e as alocações propostas precisam de validação técnica antes de qualquer aplicação real.

Depois de encontrar e verificar uma solução, o comando Gurobi acima atualiza automaticamente o Gantt do README a partir dos CSVs e do resumo recém-gravados. Isso ocorre para a combinação `dados_modelo_ampliado/` e `resultados_ampliado/`; outras pastas não alteram o README. Use `--sem-atualizar-readme` para desativar a atualização. Se não houver solução viável, o Gantt não é atualizado. Se a geração do Gantt falhar depois de salvar a solução, o comando informa o erro e retorna código diferente de zero.
