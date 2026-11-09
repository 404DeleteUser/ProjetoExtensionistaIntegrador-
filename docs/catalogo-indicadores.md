# Catálogo de indicadores

Liga cada pergunta de negócio da SEDUC-MT sobre o Recadastramento ao indicador que a responde no Power BI.

## Regras comuns

- **Granularidade da fonte:** `fato_recadastramento` tem uma linha por servidor anonimizado por dia de carga.
- **Medidas semiaditivas:** cada dia é uma foto completa. As contagens usam só o **último dia com carga** do período filtrado (`[Última data]`) e nunca somam dias.
- **LGPD:** todos os indicadores são contagens ou percentuais agregados. Nenhum mostra servidor individual.
- **Meta oficial:** 90% de servidores com recadastramento concluído até 31/12/2026.
- **Medidas:** ficam na tabela `_Medidas` (pasta indicada entre parênteses) do modelo `powerbi/PEI.SemanticModel`.

## Painel gerencial

| Nº | Pergunta de negócio | Indicador (medida) | Fórmula | Fonte | Visual |
|---|---|---|---|---|---|
| G1 | Quantos servidores precisam se recadastrar? | Servidores (Situação) | Linhas do fato na `[Última data]` | fato_recadastramento, dim_tempo | Cartão |
| G2 | Quanto do recadastramento já terminou? | % Concluído (Situação) | Concluídos ÷ Servidores | + dim_situacao | Cartão com "X de N servidores" |
| G3 | Quantos aguardam a validação da SEDUC? | Aguardando validação e % (Situação) | Servidores com situação "Aguardando validação" ÷ Servidores | + dim_situacao | Cartão |
| G4 | Quantos começaram e não terminaram? | Em andamento e % (Situação) | Servidores com situação "Em andamento" ÷ Servidores | + dim_situacao | Cartão |
| G5 | Quantos ainda não começaram? | Não iniciado e % (Situação) | Servidores com situação "Não iniciado" ÷ Servidores | + dim_situacao | Cartão (alerta quando > 0) |
| G6 | Quais DREs estão mais atrasadas? | % Concluído por DRE | G2 por dim_dre, em ordem crescente | + dim_dre | Barras 100% "Situação por DRE" |
| G7 | Em que regiões do estado estão os atrasos? | Faixa % Concluído (Mapa) | MIN(4, INT(% Concluído × 100 ÷ 20)): faixas de 20 pontos | + dim_municipio (código IBGE) | Mapa de formas |
| G8 | Quantos servidores há por tipo de vínculo? | Servidores por vínculo | G1 por dim_vinculo | + dim_vinculo | Barras |
| G9 | Quantos servidores há por tipo de lotação? | Servidores por tipo de lotação | G1 por dim_lotacao[tipo_lotacao] | + dim_lotacao | Barras |
| G10 | Quais funções concentram mais servidores? | Servidores por função (top 8) | G1 por dim_funcao, top 8 | + dim_funcao | Barras |

## Painel operacional

| Nº | Pergunta de negócio | Indicador (medida) | Fórmula | Fonte | Visual |
|---|---|---|---|---|---|
| O1 | Quais lotações (escolas) precisam de cobrança primeiro? | % Concluído e as 4 situações por lotação | G2 a G5 por DRE > Município > Lotação, em ordem crescente de % | + dim_lotacao (hierarquia) | Matriz com drill-down |
| O2 | Como cada município está em relação aos outros da mesma DRE? | Ranking do município na DRE (Ranking) | RANKX do % Concluído entre os municípios da DRE (1 = maior) | + dim_lotacao | Matriz |

## Painel estratégico

| Nº | Pergunta de negócio | Indicador (medida) | Fórmula | Fonte | Visual |
|---|---|---|---|---|---|
| E1 | Quanto da meta já foi alcançado? | % da meta atingido (Meta) | % Concluído ÷ Meta % | medidas de Meta | Cartão |
| E2 | Quantos concluídos ainda faltam para a meta? | Faltam para a meta (Meta) | MAX(0, ROUNDUP(Servidores × 90%) − Concluídos) | medidas de Meta | Cartão |
| E3 | Quanto tempo resta? | Dias restantes (Meta) | MAX(0, Data-limite − Última data) | medidas de Meta | Cartão |
| E4 | Quantos precisam concluir por dia para cumprir o prazo? | Ritmo necessário por dia (Meta) | Faltam para a meta ÷ Dias restantes | medidas de Meta | Cartão, comparado com E6 |
| E5 | Quantos concluíram desde a última carga? | Novos concluídos (Evolução) | Concluídos − Concluídos no dia anterior com carga | fato_recadastramento, dim_tempo | Cartão e colunas por dia |
| E6 | Qual é o ritmo real de conclusão? | Média móvel 7 dias (Evolução) | Média de Novos concluídos nos últimos 7 dias | fato_recadastramento, dim_tempo | Cartão |
| E7 | O % concluído está subindo como deveria? | % Concluído por data, Variação p.p., Variação semanal (Evolução) | % de cada dia; diferença para o dia anterior; Concluídos − Concluídos 7 dias antes | fato_recadastramento, dim_tempo | Linha, com Meta % como referência |
| E8 | Quando todos terminam, no ritmo atual? | Dias para concluir, Data prevista de conclusão (Evolução) | ROUNDUP((Servidores − Concluídos) ÷ Média móvel 7 dias); Última data + esse valor | medidas de Evolução | Cartões |
| E9 | Vamos bater a meta no prazo? | Situação da meta, Data prevista da meta (Meta) | Última data + ROUNDUP(Faltam ÷ Média móvel 7 dias), comparada com 31/12/2026 → "Meta atingida", "No prazo", "Atrasado" ou "Sem histórico" | medidas de Meta e Evolução | Cartão |

Os indicadores E5 a E9 dependem de pelo menos 2 dias de carga. Sem isso, os cartões mostram "Sem histórico".

## Controle de qualidade

| Nº | Pergunta | Indicador | Fórmula | Esperado |
|---|---|---|---|---|
| Q1 | Toda situação recebida está entre as 4 oficiais? | Outras situações (Situação) | Servidores − soma das 4 situações | 0 |

## Medidas auxiliares (não são indicadores)

- **Última data e Data anterior:** definem o dia usado nos cálculos semiaditivos.
- **Cor do mapa e Cor da situação:** cores da formatação condicional, iguais às do SEDUC DataHub.
- **% Concluído (rótulo) e as medidas da pasta Exibição:** textos para os cartões ("X de N servidores", "Sem histórico").
- **Meta % e Data-limite:** parâmetros da meta oficial.
