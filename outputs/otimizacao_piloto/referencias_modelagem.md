# Referências de modelagem e aderência ao piloto

## Referências selecionadas

| Referência | Contribuição aproveitada | Aderência e limite |
| --- | --- | --- |
| Hartmann & Briskorn (2022) | Base conceitual e taxonomia do RCPSP/MRCPSP; modos representam formas alternativas de executar atividades e podem alterar recursos e duração. | Referência de enquadramento do problema. O piloto é uma variante pequena e estilizada, não cobre todas as extensões do survey. |
| Senouci & Mubarak (2016) | Exemplo de modelo de construção que separa programação, cálculo de custos e avaliação de trade-offs entre tempo e custo. | Próximo no domínio e na estrutura de custos. O artigo trata efeitos climáticos e busca multiobjetivo com algoritmo genético; o piloto é determinístico e usa MILP com um objetivo ponderado. |
| Hegazy (1999) | Motivação para considerar decisões de alocação e programação de recursos de forma integrada. | O artigo combina alocação e nivelamento de recursos com algoritmo genético. O piloto integra escolha de modo e início, mas não inclui suavização do histograma como objetivo. |
| Zou et al. (2017) | Referência de formulação MILP com trade-off de tempo e custo em projetos repetitivos. | Útil como caminho de extensão. O recorte atual não repete atividades por trecho/unidade e não modela várias equipes simultâneas em uma mesma atividade. |

Os metadados foram conferidos nas páginas dos periódicos ou registros bibliográficos dos editores. As descrições acima são sínteses para explicar a aderência; para citações textuais, pressupostos detalhados ou reprodução de formulações, é necessário consultar o texto integral.

## Aplicação ao trabalho

1. O modelo foi classificado como variante determinística do MRCPSP: cada atividade escolhe exatamente um modo de formação de equipe.
2. Cada modo associa efetivo, produtividade, duração e custo. Os modos da mesma família compartilham um pool de recurso renovável com capacidade unitária.
3. A escolha de modo e o sequenciamento são otimizados conjuntamente, sujeitos às precedências e aos pools. A comparação usa uma referência serial factível com equipes padrão. O CPM sem recursos fica identificado como referência de lógica, não como alternativa executável.
4. O objetivo atual é custo total ponderado: custo direto + custo indireto por prazo + apoio por pessoa-dia. A sensibilidade varia as duas taxas e reotimiza, em vez de afirmar que um cronograma é melhor antes de comparar os valores.
5. A seleção de uma formação de equipe por atividade significa uma equipe por atividade durante a execução. Dividir uma atividade em várias equipes simultâneas é extensão explícita; não deve ser inferida dos modos disponíveis.
6. A solução ótima é uma afirmação restrita ao modelo e aos dados correntes. Registrar status do solver, gap, verificações de precedência e capacidade junto ao resultado.

## Bibliografia

- Hartmann, S.; Briskorn, D. (2022). “An updated survey of variants and extensions of the resource-constrained project scheduling problem.” *European Journal of Operational Research*, 297(1), 1–14. [https://doi.org/10.1016/j.ejor.2021.05.004](https://doi.org/10.1016/j.ejor.2021.05.004)
- Senouci, A. B.; Mubarak, S. A. (2016). “Multiobjective optimization model for scheduling of construction projects under extreme weather.” *Journal of Civil Engineering and Management*, 22(3), 373–381. [https://doi.org/10.3846/13923730.2014.897968](https://doi.org/10.3846/13923730.2014.897968)
- Hegazy, T. (1999). “Optimization of Resource Allocation and Leveling Using Genetic Algorithms.” *Journal of Construction Engineering and Management*, 125(3), 167–175. [https://doi.org/10.1061/(ASCE)0733-9364(1999)125:3(167)](https://doi.org/10.1061/(ASCE)0733-9364(1999)125:3(167))
- Zou, X.; Fang, S.-C.; Huang, Y.-S.; Zhang, L.-H. (2017). “Mixed-Integer Linear Programming Approach for Scheduling Repetitive Projects with Time-Cost Trade-Off Consideration.” *Journal of Computing in Civil Engineering*, 31(3). [https://doi.org/10.1061/(ASCE)CP.1943-5487.0000641](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000641)
