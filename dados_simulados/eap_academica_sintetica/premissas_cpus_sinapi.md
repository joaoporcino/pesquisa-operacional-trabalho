# CPUs de referência para a EAP acadêmica

## O que foi montado

O arquivo `Vinculo_EAP_CPU.csv` liga cada pacote da EAP hipotética a uma CPU didática. Cinco pacotes trazem uma referência técnica parcial de composição SINAPI: drenagem transversal, drenagem longitudinal, produção de mistura para base, usinagem do revestimento e defensa metálica. Os pacotes sem correspondência direta usam apenas composição sintética.

`CPUs_EAP_sinteticas.csv` guarda o cabeçalho por pacote; `Itens_CPU_EAP_sinteticas.csv` guarda os coeficientes de referência ou os itens hipotéticos; `Conferencia_rollup_EAP_CPU.csv` confere a soma dos itens para CPU, da CPU para pacote e dos pacotes para todos os níveis da EAP.

## Regra de custo e quantidade

Os códigos, descrições e coeficientes técnicos indicados como SINAPI foram transcritos dos Cadernos Técnicos da CAIXA. As quantidades dos pacotes, os itens complementares e todos os preços unitários em pontos de índice foram criados para o exercício. As taxas sintéticas foram calibradas para preservar os pontos de custo já definidos na EAP, totalizando 1.000 pontos sem moeda. Nenhum preço de mercado, preço regional ou custo SINAPI foi usado.

A Nota SINAPI 12/2025 nº 01 da CAIXA informou publicação de relatórios com preços/custos zerados a partir da referência outubro/2025. A Nota 12/2025 nº 02 registrou a retificação, em 22/12/2025, dos relatórios de outubro e novembro/2025 com as informações de preço recebidas do IBGE. Este modelo não utiliza preços SINAPI; para uma futura monetização, deve-se conferir diretamente o relatório mais recente da UF e competência escolhidas. Os Cadernos consultados identificam explicitamente as referências 104361 e 103751 como sem custo.

Os itens SINAPI do tipo C são mantidos como referências de subcomposição, mas esta versão não abre recursivamente cada subcomposição até todos os insumos. Seus preços unitários de índice também são sintéticos. Assim, a tabela demonstra a ligação e o roll-up de custos no nível disponibilizado; ela não substitui orçamento referencial nem reproduz integralmente uma CPU SINAPI.

## Limites da aderência

As CPUs destacadas não cobrem sozinhas a atividade inteira: 95568 é um tubo simples DN 400 mm em baixa interferência; 102680 é um tipo específico de dreno profundo; 105534 é a usinagem de uma mistura solo-brita com cimento; 104361 é a produção de mistura asfáltica sem transporte e aplicação; 103751 cobre defensa metálica, não todo o escopo de sinalização e acabamentos. Os complementos sintéticos permanecem sinalizados nos itens.

As quantidades-modelo e os coeficientes de complementos são premissas acadêmicas e não descrevem dimensões, produtividade, valores ou estrutura da obra usada como inspiração. A EAP e as CPUs aqui vinculadas são independentes dos dados locais da obra.

## Fontes oficiais

- CAIXA, [SINAPI — relatórios mensais, documentação e consulta de preços/custos](https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/paginas/default.aspx).
- CAIXA, [Notas SINAPI](https://www.caixa.gov.br/Downloads/sinapi-historico-de-encargos-e-notas/Notas_SINAPI.pdf), incluindo a nota inicial de valores zerados e a retificação posterior dos relatórios de outubro e novembro/2025.
- CAIXA, [Caderno de assentamento de tubos de esgoto/drenagem pluvial em concreto](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-ASSENTAMENTO-DE-TUBOS-DE-ESGOTO-OU-DRENAGEM-PLUVIAL-EM-CONCRETO.pdf), referência 95568.
- CAIXA, [Caderno de drenos](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-DRENOS.pdf), referência 102680.
- CAIXA, [Caderno de usinagens](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-USINAGENS.pdf), referências 105534 e 104361.
- CAIXA, [Caderno de sinalização horizontal viária](https://www.caixa.gov.br/Downloads/sinapi-cadernos-tecnicos/SINAPI-CT-SINALIZACAO-HORIZONTAL-VIARIA.pdf), referência 103751.

## Reprodução

Execute `python dados_simulados/eap_academica_sintetica/montar_cpus_eap_sinapi.py` na raiz do projeto. O gerador lê somente `EAP_sintetica.csv` nesta pasta e recria os CSVs e o relatório JSON desta entrega.
