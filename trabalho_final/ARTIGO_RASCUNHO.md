# Otimização do custo de obras por seleção de equipes e programação de atividades

**Rascunho de pesquisa — resultados e fontes sujeitos à conferência.** Os resultados numéricos abaixo referem-se ao piloto sintético de 12 atividades. Há também um recorte sintético ampliado de 68 tarefas com PERT no nível de tarefas e execução no Gurobi, descrito em `outputs/otimizacao_piloto/LEIA-ME-AMPLIADO.md`; a redação dos resultados abaixo ainda precisa ser atualizada para esse recorte. Nenhum dos dois descreve a obra de referência.

## Resumo

Este trabalho investiga a escolha de equipes e o sequenciamento de atividades de uma obra, considerando precedências, disponibilidade de recursos e a relação entre duração e custos diretos e indiretos. Formula-se um problema de programação linear inteira mista no qual cada atividade é executada por um modo escolhido entre alternativas de produtividade e custo conhecidos. A duração do projeto determina uma parcela do custo indireto. Para verificar a implementação, aplica-se inicialmente um piloto sintético com 12 atividades e um marco. Nesse piloto, o cenário otimizado apresentou duração de 24,33 dias úteis e custo de 23,9759 pontos de índice, ante 34 dias e 24,96 pontos em uma referência factível específica. A solução é ótima para a instância sintética e suas hipóteses, não para uma obra real. O estudo de caso com dados tratados e a discussão sobre o pacote computacional permanecem a concluir.

**Palavras-chave:** programação de obras; programação linear inteira mista; alocação de equipes; trade-off tempo-custo.

## 1. Introdução

A programação de uma obra envolve atividades sujeitas a precedências e à disponibilidade limitada de equipes e equipamentos. Alterar a composição de uma equipe pode modificar sua produtividade e o custo de uma atividade, bem como a duração do projeto e os custos associados ao tempo de permanência da estrutura de apoio. Contudo, a redução da duração de uma atividade não antecipa necessariamente o projeto, pois outras cadeias de atividades ou conflitos de recursos podem determinar seu término.

Este trabalho investiga como a seleção conjunta de modos de execução e horários pode alterar o custo total de um cronograma. A abordagem separa o custo direto associado a cada alternativa da parcela indireta assumida proporcional ao prazo e, no piloto, de uma parcela de apoio proporcional a pessoa-dia. O objetivo é comparar uma referência factível com a solução de uma formulação de programação linear inteira mista. Os resultados dependem das hipóteses de produtividade, capacidade, precedência e custeio.

## 2. Revisão da literatura

Hartmann e Briskorn (2022) revisam variantes do problema de programação de projetos com recursos limitados, incluindo modos alternativos, restrições de recursos e diferentes objetivos. A contribuição para este trabalho é a classificação do problema: cada modo descreve uma forma de executar uma atividade, com duração e uso de recursos associados. Por ser uma revisão, não deve ser apresentada como experimento de um solver específico para a instância deste estudo.

Senouci e Mubarak (2016) apresentam um modelo multiobjetivo de programação de projetos de construção em condições de clima extremo e empregam algoritmos genéticos para obter cronogramas de prazo e custo. Em um exemplo com 12 atividades e cinco formações por atividade, reportam soluções de 63 dias úteis e US$ 1.082.500 até 130 dias úteis e US$ 880.000, obtidas em uma aproximação da fronteira de compromisso. A proximidade está na escolha de equipes e análise conjunta de programação e custos. O estudo considera efeitos climáticos e data de início, enquanto o piloto aqui é determinístico e minimiza um custo total. As soluções de algoritmo genético não devem ser tomadas como certificado de otimalidade global. Fonte: https://doi.org/10.3846/13923730.2014.897968.

Hegazy (1999) trata de alocação e nivelamento de recursos com algoritmos genéticos. A referência motiva a consideração conjunta de programação e recursos. O modelo deste estudo, porém, não inclui o nivelamento do efetivo como objetivo: limita o uso simultâneo dos recursos disponíveis. **Pendente:** confirmar no texto completo os experimentos e os resultados específicos para análise crítica.

Zou et al. (2017) estudam programação de projetos repetitivos com múltiplas equipes, por meio de programação linear inteira mista e consideração do compromisso entre tempo e custo, com prazo limite. Sua formulação é uma referência para o uso de MILP em construção; a instância deste piloto não representa repetição de atividades por trechos nem várias equipes trabalhando ao mesmo tempo em uma mesma atividade. **Pendente:** conferir dados, ferramenta efetiva e resultados do artigo no texto completo.

## 3. Problema e modelagem

Considere atividades \(i\in A\), relações de precedência término–início \((i,j)\in P\) e conjuntos \(E_i\) de modos habilitados. Cada modo \(e\) pertence a um recurso compartilhado de capacidade unitária, tem produtividade \(p_{ie}>0\), custo direto \(c_{ie}\) e efetivo \(h_{ie}\). Para uma quantidade de serviço \(Q_i\), sua duração determinística é \(d_{ie}=Q_i/p_{ie}\).

Seja \(x_{ie}\) binária e igual a 1 quando o modo é escolhido; \(S_i\ge0\), o início de uma atividade; e \(C_{\max}\), o término do projeto. O objetivo do piloto é:

\[
\min C_f+\sum_i\sum_{e\in E_i}c_{ie}x_{ie}+c_tC_{\max}+c_h\sum_i\sum_{e\in E_i}h_{ie}d_{ie}x_{ie}.
\]

Aqui \(C_f\) é custo fixo, \(c_t\) é a taxa indireta por dia de projeto e \(c_h\) é o apoio indireto por pessoa-dia. Custos em cada parcela são separados para evitar dupla contagem; a identificação dessa separação em uma base de obra requer auditoria de composição.

Cada atividade escolhe um modo: \(\sum_{e\in E_i}x_{ie}=1\). Sua duração escolhida é \(D_i=\sum_e d_{ie}x_{ie}\). Impõem-se \(S_i+D_i\le S_j\) para cada precedência e \(S_i+D_i\le C_{\max}\) para cada atividade. Para as atividades \(i,j\) que podem usar o mesmo recurso unitário \(r\), defina \(z_{ir}\) como o indicador derivado dos modos escolhidos que ocupam \(r\), e \(y_{ijr}\) como uma variável binária de ordenação. As restrições a seguir garantem que elas não se sobreponham quando ambas ocuparem esse recurso:

\[
S_i+D_i\le S_j+M(3-z_{ir}-z_{jr}-y_{ijr}),\qquad
S_j+D_j\le S_i+M(2-z_{ir}-z_{jr}+y_{ijr}).
\]

O parâmetro \(M\) deve ser uma cota válida para relaxar as desigualdades quando a respectiva ordem não se aplica. No piloto, foi definida uma cota superior à soma das durações máximas das atividades; não se deve reutilizar esse valor sem recalculá-lo para outra instância. As variáveis \(x\) e \(y\) são binárias; inícios e prazo são contínuos e não negativos. Detalhes e índices constam no arquivo `modelo_matematico.md` do pacote computacional.

O modelo assume atividades sem interrupção, uma formação por atividade e recursos com capacidade unitária constante. Não representa divisão de uma atividade entre equipes simultâneas, calendários específicos, mudanças de modo durante a execução ou risco estocástico.

## 4. Método computacional e dados

O protótipo foi implementado com `scipy.optimize.milp` e também executado com Gurobi. O piloto teve otimalidade comprovada; no recorte ampliado, o Gurobi encontrou solução factível com limite de 30 segundos e gap de 7,57%, sem comprovar otimalidade. Os registros e parâmetros estão nas pastas de resultados correspondentes.

A instância piloto é inteiramente sintética: 12 atividades, um marco, 13 relações de precedência, 36 combinações habilitadas e seis grupos de recursos compartilhados. Quantidades, produtividades, custos, capacidades e relações são hipóteses didáticas. A referência fixa os modos padrão e programa atividades respeitando precedências e recursos; não se afirma que ela seja ótima. O CPM lógico sem recursos não é apresentado como cronograma factível.

**Caso principal pendente:** selecionar e documentar uma versão coerente da base tratada; confirmar sua revisão; conciliar cronograma e custos; estabelecer quais entradas vêm dos dados e quais são hipóteses. A auditoria encontrou 102 linhas de recurso com fórmula não confirmada, três composições sem linhas e 47 atividades sem composição. Não há predecessoras explícitas nem medições de execução na extração disponível.

## 5. Resultados e análise

| Cenário do piloto | Prazo (dias úteis) | Custo total (pontos de índice) |
| --- | ---: | ---: |
| Referência factível com modos padrão | 34,00 | 24,9600 |
| Otimização conjunta de modos e inícios | 24,33 | 23,9759 |

Nas hipóteses do piloto, a solução otimizada reduz o prazo em aproximadamente 28,4% e o custo em 3,9% em relação à referência específica. A diferença combina escolha de modos com o sequenciamento, portanto não isola o efeito de cada decisão. O modelo é ótimo apenas para a instância e o objetivo adotados. As verificações registradas e uma reexecução independente confirmaram as precedências e a ausência de sobreposição em cada pool. Os pontos de índice não representam valores monetários reais.

O CPM lógico do modo padrão resulta em 30 dias, mas não respeita integralmente a capacidade dos pools e não é uma alternativa executável. As análises de sensibilidade já geradas precisam ser revisadas e relacionadas ao cenário principal; a amostra de soluções não constitui uma fronteira custo–prazo completa.

## 6. Conclusões provisórias

O piloto demonstra a viabilidade de formular conjuntamente escolha de equipes e programação, dentro das hipóteses adotadas. Não comprova economia na obra nem superioridade geral em relação a outras práticas. A conclusão final dependerá do caso com dados tratados, da qualidade das hipóteses e da análise dos cenários. Como extensão, podem-se considerar mais de uma equipe por atividade, calendários, custos de mobilização dependentes da decisão e incerteza de produtividade.

## Referências preliminares

HARTMANN, S.; BRISKORN, D. An updated survey of variants and extensions of the resource-constrained project scheduling problem. *European Journal of Operational Research*, v. 297, n. 1, p. 1–14, 2022. DOI: 10.1016/j.ejor.2021.05.004.

HEGAZY, T. Optimization of resource allocation and leveling using genetic algorithms. *Journal of Construction Engineering and Management*, v. 125, n. 3, p. 167–175, 1999. DOI: 10.1061/(ASCE)0733-9364(1999)125:3(167).

SENOUCI, A. B.; MUBARAK, S. A. Multiobjective optimization model for scheduling of construction projects under extreme weather. *Journal of Civil Engineering and Management*, v. 22, n. 3, p. 373–381, 2016. DOI: 10.3846/13923730.2014.897968.

ZOU, X.; FANG, S.-C.; HUANG, Y.-S.; ZHANG, L.-H. Mixed-integer linear programming approach for scheduling repetitive projects with time-cost trade-off consideration. *Journal of Computing in Civil Engineering*, v. 31, n. 3, 2017. DOI: 10.1061/(ASCE)CP.1943-5487.0000641.
