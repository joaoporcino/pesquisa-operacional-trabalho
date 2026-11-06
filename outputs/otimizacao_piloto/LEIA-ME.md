# Base acadêmica para otimização tempo-custo

## Escopo

Este pacote contém um piloto hipotético de um segmento de infraestrutura linear associado ao setor 04 da EAP sintética ampliada. A EAP foi usada para selecionar e rastrear atividades e pontos de custo em índice. O recorte não representa o S11D, não usa quantitativos de campo, preços reais ou valores em reais.

O piloto contém 12 atividades de execução e um marco de mobilização. A sequência cobre limpeza, drenagem transversal, terraplenagem, base, revestimento, sinalização e inspeção. As quantidades foram definidas como premissas acadêmicas porque os nós-folha da EAP de escala usam quantidade-modelo igual a um pacote e não representam medições físicas.

## Estrutura do problema

O modelo é uma variante determinística do MRCPSP: cada atividade escolhe exatamente um modo de formação de equipe. Cada modo associa composição do efetivo, produtividade, duração e custo direto. A escolha do modo e o sequenciamento são otimizados juntos, com precedências FS e recursos renováveis limitados.

Todos os perfis da mesma família consomem um pool compartilhado de capacidade unitária. O piloto supõe uma equipe disponível em cada pool. Isso evita interpretar baixa, padrão e alta produtividade como três equipes físicas diferentes. Cada atividade usa uma formação de equipe por vez; dividir a mesma atividade entre várias equipes simultâneas é uma extensão futura, não modelada aqui.

O custo total combina custo fixo de mobilização, custo direto dos modos, custo indireto por dia de prazo e apoio indireto por pessoa-dia. A formulação, premissas e fronteiras estão em modelo_matematico.md; a relação com as referências está em referencias_modelagem.md.

## Arquivos

Os CSVs em dados_modelo usam ponto e vírgula como separador e UTF-8 com BOM.

- atividades.csv: atividades, quantidades sintéticas, EAP de referência e duração PERT do modo padrão.
- precedencias.csv: relações FS próprias do recorte; a hierarquia da EAP não foi interpretada como precedência.
- equipes.csv: catálogo de formações de equipe/modos, ligados aos pools compartilhados.
- recursos_compartilhados.csv: recursos renováveis e disponibilidade unitária assumida por família.
- habilitacoes_alternativas.csv: modos atividade-equipe habilitados, produtividade, duração, composição e custos.
- custos_fixos.csv: mobilização de apoio com itens de origem, somados uma vez.
- premissas.csv: calendário, produtividades, taxas de custo, capacidade, regras e limites.
- PERT_CPM_sem_recursos.csv: CPM lógico com durações esperadas; não é executável sob as capacidades.
- cenario_base_com_equipes.csv: referência factível com modos padrão e pools compartilhados.
- cenario_otimizado.csv: solução do MILP com escolha de modo e inícios em conjunto.
- comparacao_cenarios.csv: comparação dos prazos e custos calculados sob as premissas-base.
- sensibilidade_indiretos.csv: recálculos variando as taxas indiretas.
- fronteira_prazo_custo_amostral.csv: soluções não dominadas na amostra, comparadas após reprecificação às taxas-base. Não é uma fronteira completa por prazo imposto.
- conciliacao_custos.csv: conciliação dos custos diretos padrão com os pontos de origem da EAP.
- verificacoes.json: verificações da rede, custos, capacidades e status/gap do solver.

## Leitura dos cenários

O PERT/CPM sem recursos serve como referência da rede lógica, não como cronograma executável. A referência factível fixa o modo padrão e usa um esquema serial de geração em ordem topológica, iniciando cada atividade assim que precedências e pools permitem. A solução MILP escolhe modos e horários simultaneamente; a comparação é feita em relação a essa referência factível, não ao CPM sem capacidade.

O solver minimiza uma função ponderada de custo total. Para as taxas-base atuais, a solução reportada é ótima somente para este conjunto sintético de atividades, modos, precedências e capacidades. Nesta execução, o MILP encontrou 24,33 dias e 23,9759 pontos, contra 34 dias e 24,96 pontos na referência factível. É uma comparação medida dentro do piloto, não demonstra superioridade geral e não é estimativa ou recomendação para obra real. Consulte verificacoes.json para o status e gap; a sensibilidade e a amostra custo-prazo são regeneradas separadamente.

## Custos sem dupla contagem

Todos os custos são pontos de índice sintéticos, sem moeda.

1. O custo direto de cada modo soma custo diário da equipe/equipamento multiplicado pela duração e materiais variáveis.
2. O modo padrão foi calibrado aos pontos de custo das folhas EAP selecionadas. A parcela de material é uma divisão hipotética, não uma CPU real.
3. Mobilização fixa soma dois itens de origem e entra uma vez; não se repete nas atividades nem na taxa diária.
4. O indireto por prazo é multiplicado pela duração total do projeto.
5. O apoio indireto por pessoa-dia é calculado com efetivo × duração; não repete salários ou equipamentos incluídos no custo direto da equipe.

## Sensibilidade e custo-prazo

analisar_sensibilidade.py reotimiza o piloto para faixas hipotéticas das taxas indiretas de prazo e de efetivo. A tabela sensibilidade_indiretos.csv mostra cada premissa e o resultado recalculado. Para comparar diferentes modos e durações sob uma mesma base de custos, a tabela fronteira_prazo_custo_amostral.csv reprecifica as soluções pelas taxas-base e filtra os pontos dominados da amostra.

Na coluna MODOS_ESCOLHIDOS, R significa produtividade alta, P padrão e B baixa; cada par numérico identifica OP01–OP12.

A amostra é adequada para explorar sensibilidade em sala de aula. Para uma fronteira custo-prazo completa, a etapa seguinte é resolver o modelo para prazos-limite progressivos ou gerar um conjunto de soluções não dominadas, mantendo fixas as premissas econômicas.

## Limites e extensões

Este é um segmento sintético curto, não o prazo integral do S11D. A rede não modela repetição de frentes/unidades, múltiplas equipes simultâneas em uma atividade, divisão de atividades, interrupções, calendários civis, incerteza probabilística ou nivelamento de efetivo como objetivo.

O PERT usa uma faixa simétrica hipotética O/M/P; seu valor esperado coincide com Q/produtividade. O MILP usa durações determinísticas Q/produtividade e não simula risco.

## Reproduzir

Na raiz do workspace, execute:

    python outputs/otimizacao_piloto/gerar_base_otimizacao_piloto.py --force
    python outputs/otimizacao_piloto/resolver_piloto.py
    python outputs/otimizacao_piloto/analisar_sensibilidade.py

O solver requer SciPy com scipy.optimize.milp (HiGHS). O gerador sobrescreve somente os dados_modelo do piloto. Os arquivos anteriores em outras pastas não são alterados.
