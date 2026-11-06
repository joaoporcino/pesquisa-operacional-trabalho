# EAP acadêmica sintética em escala ampliada

## Escopo e escala

Caso hipotético de implantação de infraestrutura linear, criado sem ler as tabelas do projeto. O modelo tem 1,849 nós de EAP: 450 agrupadores e 1,399 atividades de detalhe. Somente as contagens agregadas serviram de referência para o tamanho; não foram copiados descrições, códigos, custos, quantidades, datas ou relações de precedência.

## Cronograma

A rede PERT/CPM contém 1,379 atividades discretas e dois marcos. Há 20 linhas de suporte contínuo classificadas como LOE, fora da rede. O PERT usa TE = (O + 4M + P) / 6; o CPM calcula os inícios, términos e folgas pelas precedências finish-to-start explicitadas em `dependencias_sinteticas.csv`.

O cálculo resulta em 116.67 dias úteis presumidos. Esse resultado serve à demonstração acadêmica; não é estimativa de obra.

## Custos e CPUs

Os custos da EAP somam 1.000 pontos de índice, sem moeda. O arquivo `ARQUETIPO_CPU` conecta cada folha a uma das 19 famílias sintéticas de CPU; as quantidades-modelo são indicativas e foram definidas para facilitar exercícios de custo. A classificação direta/indireta/em dúvida é hipótese didática.

O gerador de CPUs vincula referências SINAPI públicas onde há aderência parcial, completa o escopo com itens sintéticos e usa CPUs inteiramente sintéticas nos demais casos. Nenhum preço de mercado é atribuído.

## Reprodução

`python scripts/criar_eap_academica_escala.py` cria esta pasta, sem sobrescrever versões existentes. Em seguida, na raiz do workspace, execute `python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py --eap dados_simulados/eap_academica_sintetica_escala_exemplo/EAP_sintetica.csv --output-dir dados_simulados/eap_academica_sintetica_escala_exemplo`.

Referências metodológicas do modelo: GAO, *Schedule Assessment Guide*, https://www.gao.gov/assets/gao-12-120g.pdf; FHWA, *Guide for Construction Contract Time Determination Procedures*, https://www.fhwa.dot.gov/construction/contracts/t508015.cfm.
