# EAP acadêmica sintética — premissas

## Escopo

Caso hipotético de implantação de infraestrutura linear. A EAP foi criada do zero para fins didáticos; o script não lê nem consulta os CSVs da obra. Os rótulos, custos-índice, estimativas de duração e predecessoras são novos e não foram copiados linha a linha de um orçamento real.

## Estrutura e cronograma

A EAP é organizada por entregas e pacotes de trabalho. A rede de cronograma contém atividades discretas e marcos; os serviços contínuos de supervisão e HSE/ambiente/qualidade ficam como pacotes LOE, fora do caminho crítico. A tabela de dependências explicita as relações finish-to-start assumidas.

O PERT usa `TE = (O + 4M + P) / 6`. O CPM calcula início/fim cedo e tarde e folga com essas durações esperadas. O exemplo resulta em 134.00 dias úteis presumidos e caminho crítico A01 → A02 → A04 → A05 → A11 → A12 → A13 → A14 → A15 → A16 → A17. Esses resultados servem para demonstrar o método, não para estimar uma obra real.

## Custos e classificação

Os custos são pontos sem moeda, somando 1.000 no nível raiz. A classificação `DIRETA`, `INDIRETA` ou `DUVIDA` é uma hipótese didática para treinar análise; deve ser revisada segundo o critério de custeio definido pelo curso.

## Referências metodológicas

- GAO, *Schedule Assessment Guide*: apresenta a WBS como decomposição do escopo/entregáveis e mostra que as atividades do cronograma são derivadas dela. https://www.gao.gov/assets/gao-12-120g.pdf
- FHWA, *Guide for Construction Contract Time Determination Procedures*: orienta sequenciar operações, estimar duração e explicitar precedências, considerando trabalhos paralelos quando aplicável. https://www.fhwa.dot.gov/construction/contracts/t508015.cfm
- FHWA, *Geotechnical Aspects of Pavements — Construction and Construction Monitoring*: descreve a preparação do terreno e subleito como parte da sequência de construção de pavimentos. https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/08.cfm

As referências orientam a forma de decompor e sequenciar o exemplo. As durações, custos-índice, atividades exatas e relações do arquivo são premissas sintéticas, não dados publicados por essas fontes.
