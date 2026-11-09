# Inventário das fontes de dados

## Visão geral

| Fonte | Tipo | Acesso | Frequência | Dado pessoal? | Uso no projeto |
|---|---|---|---|---|---|
| Planilha do Recadastramento (SEDUC-MT) | Google Sheets publicada por API do Apps Script (JSON) | URL + token, só no GitHub Actions | 1×/dia | **Sim** (nome, matrícula, vínculo) | Fato do recadastramento |
| Municípios de MT (IBGE, API de localidades) | API REST pública (JSON) | Sem autenticação | Estática (copiada uma vez) | Não | Código IBGE de cada município (`bronze.municipio_ibge`) |
| Malha municipal de MT (IBGE, API de malhas v3) | TopoJSON público | Sem autenticação | Estática (copiada uma vez) | Não | Desenho do mapa no Power BI |

## 1. Planilha do Recadastramento

- **Origem:** planilha do Google Sheets usada pela SEDUC-MT no recadastramento. Um Apps Script a publica como API.
- **Formato da resposta:** `{ "ok": true, "cabecalho": [...], "linhas": [[...], ...] }`.
- **Alternativa local:** o mesmo conteúdo exportado em CSV, separado por `,` ou `;`, em UTF-8 ou Windows-1252 (variável `ARQUIVO_PLANILHA`).
- **Granularidade:** uma linha por vínculo de servidor (a mesma pessoa pode ter mais de um vínculo).
- **Período:** a planilha mostra só a situação **atual**. O histórico é construído pelo projeto, com uma carga por dia guardada em SCD Tipo 2 (`bronze.historico`).

### Colunas

| Coluna | Tipo | Descrição | Tratamento |
|---|---|---|---|
| DRE | texto | Diretoria Regional de Educação (ou Órgão Central) | Mantida |
| Municipio | texto | Município da lotação | Mantida; padronizada na Silver e casada com o IBGE |
| Lotacao | texto | Escola ou unidade de lotação | Mantida |
| TipoLotacao | texto | Escola, Escola Campo, Escola Indígena, Educação Especial, DRE ou Órgão Central | Mantida |
| Nome | texto | Nome do servidor | **Descartada** (nunca é lida) |
| Funcao | texto | Função exercida | Mantida |
| TipoVinculo | texto | Efetivo ou Temporário | Mantida |
| Matrícula | texto | Matrícula funcional | **Só entra no HMAC**; nunca é gravada |
| Vínculo | texto | Número do vínculo | **Só entra no HMAC**; nunca é gravada |
| Situação | texto | Não iniciado, Em andamento, Aguardando validação ou Concluído | Mantida; padronizada na Silver |

### Perfil da carga inicial (08/11/2026)

| Medida | Valor |
|---|---|
| Linhas na planilha | 39.250 |
| Linhas gravadas na Bronze | 39.249 (linhas sem matrícula ou repetidas são descartadas e contadas) |
| Tamanho no Supabase | `historico` 18 MB; `carga` 13 MB |
| DREs distintas | 14 (13 DREs + Órgão Central) |
| Municípios distintos | 142 |
| Lotações distintas | 835 |
| Tipos de lotação | 6 |
| Funções | 290 |
| Tipos de vínculo | 2 |
| Situações | 4 |
| Valores vazios | 0 em todas as colunas mantidas |

Distribuição por situação: Não iniciado 21.798 · Em andamento 6.408 · Concluído 6.283 · Aguardando validação 4.760.

### Qualidade encontrada

- **Nomes de município** fora da grafia do IBGE: `CONQUISTA DO OESTE` → Conquista D'Oeste e `SANTO ANTONIO DO LEVERGER` → Santo Antônio de Leverger. Corrigidos na Silver (de-para revisado).
- **Acentuação e caixa** inconsistentes entre municípios (ex.: `CUIABÁ` com acento e a maioria sem). A Silver compara por uma chave sem acento e em minúsculas.
- **A DRE não é atributo do município:** 7 municípios têm lotações em 2 DREs (ex.: Cuiabá, no Órgão Central e na DRE Metropolitana).
- **Nomes de escola repetidos** em municípios diferentes (22 casos). Por isso a lotação é identificada por lotação + município + DRE.

### Amostra

[`dados/exemplo/recadastramento_exemplo.csv`](../dados/exemplo/recadastramento_exemplo.csv) tem o mesmo cabeçalho da planilha, com dados **inteiramente fictícios**. Pela LGPD, nenhuma linha real é versionada. A amostra inclui de propósito os problemas tratados pelo pipeline: espaços sobrando, caixa diferente na situação, município fora da grafia do IBGE, linha repetida e linha sem matrícula.

## 2. Municípios de MT (IBGE)

- **Origem:** `servicodados.ibge.gov.br/api/v1/localidades/estados/51/municipios`.
- **Conteúdo:** 142 municípios com código IBGE de 7 dígitos e nome oficial.
- **Uso:** copiados para `bronze.municipio_ibge` (`sql/03_referencia_municipios.sql`). Assim o Power BI lê tudo de uma só fonte (Supabase) e evita o bloqueio de privacidade do Power Query ao misturar fontes.

## 3. Malha municipal de MT (IBGE)

- **Origem:** `servicodados.ibge.gov.br/api/v3/malhas/estados/51?formato=application/json&qualidade=minima&intrarregiao=municipio`.
- **Conteúdo:** TopoJSON com 141 formas, identificadas por `codarea` (código IBGE). Boa Esperança do Norte, município criado recentemente, ainda não tem forma na malha.
- **Uso:** arquivo `powerbi/PEI.Report/StaticResources/RegisteredResources/mato_grosso_municipios.json`, usado pelos mapas de formas.
