# Modelo matemático do piloto

## Classificação

O piloto é uma variante determinística do problema de programação de projetos com recursos limitados e modos alternativos (MRCPSP), com um objetivo ponderado de custo total. Cada modo é uma formação possível de equipe: quantidade de pessoas, produtividade, duração e custo mudam em conjunto. A decisão escolhe um único modo para cada atividade e otimiza os horários de início sujeitos à precedência e à disponibilidade dos recursos compartilhados.

As referências de modelagem e seus limites de aderência estão em [referencias_modelagem.md](referencias_modelagem.md).

## Conjuntos e índices

- \(A\): atividades de execução OP01–OP12.
- \(E_i\): modos/formações de equipe habilitados para a atividade \(i\).
- \(R\): pools de recursos renováveis compartilhados: TERR, DREN, BASE, ASF, FIN e QA.
- \(g(e)\): pool usado pelo modo de equipe \(e\).
- \(P\): precedências finish-to-start de precedencias.csv.

OP00 é um marco com início e duração iguais a zero. O custo fixo de mobilização está separado em custos_fixos.csv.

## Parâmetros

- \(Q_i\): quantidade hipotética da atividade.
- \(p_{i,e}\): produtividade hipotética no modo \(e\).
- \(d_{i,e}=Q_i/p_{i,e}\): duração determinística, contínua, em dias úteis.
- \(c_{i,e}\): custo direto do modo, incluindo equipe/equipamento e material variável.
- \(h_{i,e}\): efetivo no modo de equipe.
- \(C_f=1{,}34\): custo fixo de mobilização, incluído uma vez.
- \(c_t=0{,}20\): custo indireto sintético por dia de prazo.
- \(c_h=0{,}005\): custo indireto sintético por pessoa-dia.
- \(K_r=1\): capacidade de cada pool compartilhado.
- \(M=58{,}33333333\) dias úteis: limite big-M, maior que a soma das durações máximas.

Os custos são pontos de índice sintéticos, sem moeda. As taxas \(c_t\) e \(c_h\) são premissas, não valores de contrato ou orçamento.

## Variáveis

- \(x_{i,e}\in\{0,1\}\): 1 se a atividade \(i\) usa o modo de equipe \(e\).
- \(S_i\ge0\): início da atividade \(i\).
- \(C_{\max}\ge0\): término do projeto.
- \(z_{i,r}=\sum_{e\in E_i:g(e)=r}x_{i,e}\): indicador de que a atividade \(i\) ocupa o pool \(r\).
- \(y_{i,j,r}\in\{0,1\}\): ordem entre duas atividades que podem ocupar o mesmo pool unitário.

## Função objetivo

Minimizar o custo total do cenário:

\[
C_f+\sum_{i\in A}\sum_{e\in E_i}c_{i,e}x_{i,e}
+c_t C_{\max}
+c_h\sum_{i\in A}\sum_{e\in E_i}h_{i,e}d_{i,e}x_{i,e}.
\]

O prazo e os custos diretos não são objetivos separados no solver-base: \(c_t\) converte prazo em custo indireto. Variações em \(c_t\) e \(c_h\) são resolvidas em analisar_sensibilidade.py. O arquivo fronteira_prazo_custo_amostral.csv apresenta apenas as soluções não dominadas da amostra após reprecificação às taxas-base; não é uma fronteira completa por prazo imposto.

## Restrições

Escolha de um único modo por atividade:

\[
\sum_{e\in E_i}x_{i,e}=1\quad(i\in A).
\]

Precedência finish-to-start:

\[
S_i+\sum_{e\in E_i}d_{i,e}x_{i,e}\le S_j\quad((i,j)\in P).
\]

Conclusão do projeto:

\[
S_i+\sum_{e\in E_i}d_{i,e}x_{i,e}\le C_{\max}\quad(i\in A).
\]

Capacidade unitária compartilhada. Para cada par \(i,j\) que pode usar o mesmo pool \(r\), exatamente uma das ordens precisa valer quando \(z_{i,r}=z_{j,r}=1\):

\[
S_i+D_i\le S_j+M(3-z_{i,r}-z_{j,r}-y_{i,j,r})
\]
\[
S_j+D_j\le S_i+M(2-z_{i,r}-z_{j,r}+y_{i,j,r})
\]

em que \(D_i=\sum_{e\in E_i}d_{i,e}x_{i,e}\). Os modos alternativos da mesma família compartilham a capacidade do pool; por exemplo, TERR_RAPIDA e TERR_PADRAO não representam duas equipes físicas disponíveis em paralelo.

## Interpretação e comparação

- PERT_CPM_sem_recursos.csv fornece uma referência lógica com as durações esperadas PERT dos modos padrão. Não respeita pools e não deve ser tratado como cronograma executável.
- cenario_base_com_equipes.csv fixa o modo padrão e programa cada atividade no início mais cedo que respeita precedências e pools compartilhados. É uma referência factível e reproduzível, não é ótima.
- cenario_otimizado.csv escolhe os modos e os inícios em conjunto, respeitando as mesmas precedências e pools. Só se afirma que a solução é ótima quando o status do solver é ótimo e o gap é zero.
- Nesta execução, o MRCPSP/MILP encontrou 24,33 dias e 23,9759 pontos de índice, ante 34 dias e 24,96 pontos na referência factível. Essa diferença foi medida sob a mesma rede, pools e taxas-base, mas só compara com a heurística-base específica do piloto.
- A comparação de custo e prazo é válida dentro das premissas sintéticas do piloto. Ela não demonstra superioridade geral do método nem representa o prazo integral do S11D.

## Fronteiras e extensões

O modelo supõe uma equipe/recurso disponível por pool. Cada atividade usa uma única formação de equipe durante toda a execução. Não permite aumentar a quantidade de equipes na mesma atividade, dividir uma atividade entre equipes, trocar de modo durante a execução, calendários diferentes por recurso, interrupções ou nivelar picos de efetivo como objetivo.

As atividades do piloto não são repetidas por trecho/unidade e a EAP só serve como referência estrutural. Uma extensão para obra linear repetitiva pode acrescentar unidades de produção e continuidade entre frentes; essa formulação não foi incorporada. A literatura sobre programação repetitiva é uma referência de extensão, não uma descrição do modelo atual.

PERT usa \(O=0{,}80d\), \(M=d\) e \(P=1{,}20d\), portanto \(TE=d\). Essa faixa é didática e determinística: o solver não faz simulação de risco, Monte Carlo ou otimização estocástica. A jornada é 8 h/dia e 180 h/mês (22,5 dias úteis equivalentes), sem feriados ou datas civis.
