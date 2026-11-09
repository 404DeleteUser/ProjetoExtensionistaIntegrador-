# Perfis de adesão dos municípios (mineração de dados)

**Técnica:** clusterização (K-means), seguindo o CRISP-DM.
**Script:** `mineracao/clusterizar_municipios.py`. Para rodar, na raiz do repositório:

```
pip install -r mineracao/requirements.txt
python -m mineracao.clusterizar_municipios
```

## 1. Entendimento do negócio

O painel mostra **onde** o recadastramento está atrasado. A mineração procura **que tipos de atraso existem**: municípios com o mesmo problema pedem a mesma ação. Por exemplo, cobrar a validação, mobilizar temporários ou apoiar escolas do campo.

Pergunta: *os municípios formam grupos com perfis de adesão distintos? Quais são esses perfis?*

## 2. Entendimento dos dados

- **Fonte:** `bronze.historico`, a situação vigente de cada servidor anonimizado (`valido_ate IS NULL`).
- **Unidade de análise:** o município. O SQL agrega no banco, então nenhuma linha individual sai dele (LGPD).
- **Variáveis por município:**

| Variável | Significado |
|---|---|
| pct_nao_iniciado, pct_em_andamento, pct_aguardando, pct_concluido | Proporção de servidores em cada situação |
| pct_temporario | Proporção de vínculos temporários |
| pct_campo_indigena | Proporção de lotações em escola do campo ou indígena |
| log_servidores | Tamanho do município, em logaritmo |

## 3. Preparação

- **Logaritmo do número de servidores:** sem ele, Cuiabá (milhares de servidores) dominaria a distância entre municípios que têm dezenas.
- **Padronização (`StandardScaler`, média 0 e desvio 1):** todas as variáveis passam a pesar igual no K-means.
- **Nomes de município:** a análise usa os nomes da Bronze. A correção de nomes da Silver serve só para casar com o IBGE e não altera o agrupamento.

## 4. Modelagem

- K-means com `n_init=10` e semente fixa (42), para o resultado ser reprodutível.
- O número de grupos *k* foi escolhido entre 2 e 8 pela maior **silhueta**, que mede quanto cada município está mais perto do próprio grupo do que dos outros (vai de −1 a 1).

## 5. Avaliação

Resultado com a carga de **08/11/2026** (142 municípios, 39.249 servidores):

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| Silhueta | 0,159 | 0,200 | 0,202 | 0,204 | **0,219** | 0,211 | 0,205 |

Foi escolhido **k = 6**. A silhueta de 0,22 é **baixa**: os grupos se sobrepõem, e os perfis são tendências, não fronteiras rígidas. Os valores de *k* = 3 a 8 ficam próximos. Mesmo assim, os grupos têm interpretação clara:

| Grupo | Perfil | Municípios | Servidores | Não iniciado | Em andamento | Aguardando | Concluído | Temporários | Campo/indígena |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **Avançados** | 12 | 1.060 | 33,5% | 15,6% | 2,8% | **48,2%** | 60,4% | 17,4% |
| 1 | **Travados na validação** | 20 | 1.589 | 49,3% | 18,0% | **23,7%** | 8,9% | 58,8% | 8,2% |
| 2 | **Campo e indígena** | 29 | 5.428 | 57,9% | 15,9% | 11,4% | 14,8% | **68,0%** | **50,7%** |
| 3 | **Polos regionais** (média do estado) | 45 | 28.827 | 53,5% | 17,0% | 12,2% | 17,4% | 53,5% | 12,4% |
| 4 | **Parados** | 16 | 1.014 | **77,0%** | 7,6% | 7,5% | 7,8% | 45,1% | 5,9% |
| 5 | **Em andamento** | 20 | 1.331 | 51,2% | **24,2%** | 6,1% | 18,5% | 48,2% | 2,1% |

O script lista os municípios de cada grupo.

**Achados**

1. **Os atrasos têm causas diferentes.** No grupo 1, os servidores já enviaram, mas a validação não acompanha: 23,7% aguardam, contra 8,9% concluídos. O gargalo é da SEDUC e das DREs, não do servidor.
2. **Escolas do campo e indígenas se agrupam.** No grupo 2, metade das lotações é do campo ou indígena e 68% dos vínculos são temporários, com 57,9% ainda não iniciados. Isso sugere dificuldade de acesso ou de comunicação.
3. **Há um grupo parado.** No grupo 4, 77% não iniciaram. Em geral são municípios pequenos, onde uma ação local resolve.
4. **Os polos regionais concentram 73% dos servidores** e estão na média do estado. O % geral do painel é puxado por eles.
5. **Os municípios avançados (grupo 0)** podem servir de referência de boas práticas para os outros.

**Limitações**
- Os dados são de um único dia: os grupos mudam conforme o recadastramento avança, e o script deve ser rodado de novo.
- A separação entre os grupos é fraca (silhueta baixa).
- Associação não é causa: o grupo 2 indica onde investigar, não o motivo.

## 6. Implantação

| Perfil | Ação sugerida |
|---|---|
| Travados na validação | Reforçar a equipe de validação |
| Campo e indígena | Comunicação e apoio presencial nas escolas do campo e indígenas |
| Parados | Contato direto com as escolas |
| Avançados | Levantar o que fizeram de diferente |

Com `--gravar`, o script grava o perfil de cada município em `bronze.municipio_perfil` (`sql/04_perfil_municipio.sql`). O nome de cada perfil é a variável em que o grupo mais se destaca. A página **Perfis de adesão** do Power BI mostra os perfis no mapa e o resumo de cada um.
