# Documentação — Retail Store Clustering

Segmentação das lojas da Aurora Varejo por comparabilidade real, seguindo o CRISP-DM.

**Status:** Fase 2 (Entendimento dos Dados) concluída.

---

## 1. Entendimento do Negócio

**Problema:** a meta única de +5% para as 1.115 lojas deixou de funcionar. Lojas em ponto favorável batem a meta sem esforço; lojas pressionadas (concorrente a poucos metros) desistem no primeiro trimestre.

**Pedido da diretoria:** identificar quais lojas são parecidas de verdade e quem performa mal em relação aos seus pares, não à rede inteira.

**Quem usa o resultado**

| Área | Uso |
|---|---|
| Comercial | Meta por grupo de lojas comparáveis |
| Trade marketing | Onde a verba de promoção gera retorno |
| Supply | Mix de produto e reposição |
| Expansão | Enquadrar uma loja nova antes de ter histórico |

### Decisões de enquadramento

- **Clusterização:** não há rótulo verdadeiro de grupo (não é classificação) e não se pede previsão de venda (não é regressão).
- `tipo_loja` e `sortimento` ficam fora do modelo e são o **baseline** a ser superado.
- O projeto **não** é: previsão de vendas, busca do k matematicamente ótimo, maximização de silhueta.

### Critérios de sucesso e como serão provados

| Critério | Prova |
|---|---|
| Interpretável | Tabela de perfil (medianas e z-score vs rede) por cluster; nome derivado das 2–3 variáveis mais distantes da rede. A validação final é humana. |
| Acionável | Sem medida objetiva. Matriz cluster × área com uma decisão concreta por célula; linhas iguais ⇒ fundir clusters. |
| Estável | ARI médio ≥ 0,80 em 30 reordenações, 30 `random_state` e 30 subamostras de 80%; reportar mínimo e % de lojas que trocam de grupo. |
| Melhor que o baseline | η² dos clusters vs `tipo_loja`/`sortimento` em métricas de negócio, incluindo métricas fora do modelo, partição aleatória e k = 4; ARI/NMI clusters × `tipo_loja`. |
| Quantificado | Gap vs mediana do cluster × dias abertos × % de captura (10/25/50%) em R$/ano; metas ponderadas somando exatamente +5%. |

---

## 2. Entendimento dos Dados

| Indicador | Valor |
|---|---|
| Lojas (`loja.csv`) | 1.115 × 5 colunas |
| Registros diários (`vendas.csv`) | 1.017.209 × 9 colunas |
| Período | 01/01/2013 a 31/07/2015 (942 dias) |
| Venda média por dia aberto | R$ 6.956 |

### Dicionário resumido

| Coluna | Base | Significado | Observação |
|---|---|---|---|
| `loja` | ambas | Identificador, chave de junção | Integridade 100% entre as bases |
| `tipo_loja` / `sortimento` | lojas | Categorias cadastrais | Significado das letras não documentado |
| `distancia_concorrente` | lojas | Distância ao concorrente mais próximo | Unidade não documentada; de 20 a 75.860 |
| `promo_continua` | lojas | Adesão a programa de promoção contínua (fixo por loja) | Sem relação com a promoção diária |
| `dia_semana` | vendas | 1 = segunda … 7 = domingo | Conferido contra a data |
| `faturamento` / `clientes` | vendas | Venda (R$) e clientes do dia | — |
| `aberta` / `promo` | vendas | Loja abriu / promoção ativa no dia | `promo` é calendário da rede (~38% dos dias em todas as lojas) |
| `feriado_estadual` / `feriado_escolar` | vendas | Tipo de feriado (0, a, b, c) / feriado escolar | Significado de a, b, c não documentado |

### Principais descobertas

- **Dias fechados zeram a média:** média sobre todos os dias = média em dia aberto × % de dias abertos (identidade exata). Mede funcionamento, não capacidade de venda; lojas que abrem domingo sobem em média 108 posições no ranking só por isso.
- **Buraco sistemático:** 180 lojas sem nenhuma linha de 01/07/2014 a 31/12/2014 (184 dias, mesmo intervalo em todas). Não aparece como nulo nem zero: as linhas não existem.
- **Soma distorce, média não:** no ranking por soma, 98 das 180 lojas incompletas caem no pior quartil (esperado: 45; p ≈ 10⁻²⁰). Pela média em dia aberto, exatamente 45 (p = 0,54).
- **Registro inconsistente:** 54 linhas com `aberta = 1` e faturamento 0 (52 também com 0 clientes), em 41 lojas. Nenhuma loja fechada com venda.
- **Domingo é raro:** só 33 lojas abrem aos domingos; 17 delas são do tipo `b`.
- **Distância muito assimétrica:** skew 2,93; as 5% lojas mais isoladas concentram 59,6% da variância; após padronização, a mais distante fica a 9,19 desvios. Com log1p: skew −0,35.
- **Distância não explica venda** (Spearman −0,028): é uma dimensão própria de contexto competitivo.
- **3 nulos de distância** (lojas 291, 622, 879) sem perfil comum nem código especial: tratados como falta real.
- **`tipo_loja` é baseline fraco:** os tipos a, c e d vendem praticamente o mesmo (R$ 6.824–6.917 por dia aberto) e a dispersão interna é alta (CV da venda 0,26–0,45).
- **Tipo b é outro negócio:** 17 lojas (1,5%), 2,6× os clientes da rede, ticket de R$ 5,17 (o menor), abrem 98% dos domingos. O modelo deve mantê-las juntas, sem que distorçam as referências dos grupos grandes.

### Colunas do cadastro no modelo

| Coluna | Decisão | Motivo (pergunta de negócio) |
|---|---|---|
| `distancia_concorrente` | **entra** | Contexto competitivo que a loja não escolhe; conhecido antes da abertura (útil para Expansão). |
| `tipo_loja`, `sortimento` | baseline | São a segmentação a superar; no modelo, seriam reconstruídas. |
| `promo_continua` | descrição | Política decidida pela empresa, não comportamento; usá-la tornaria circular a decisão do Trade. |
| `loja` | fora | Identificador. |

---

## 3. Defeitos × decisões para a Fase 3

| Defeito | Decisão de engenharia |
|---|---|
| Dias fechados (17% das linhas) zeram as médias | Métricas de desempenho calculadas só sobre dias abertos |
| 54 linhas abertas sem venda | Tratar como dia sem operação: excluir das métricas |
| 180 lojas sem o 2º semestre de 2014 | Só médias, proporções e taxas, nunca somas; métricas temporais devem ser robustas ao período ausente |
| Loja 988 sem 01/01/2013 | Nenhum tratamento específico (coberto pela regra das médias) |
| `promo` igual para toda a rede | Não usar % de dias em promoção; medir a resposta à promoção |
| Proporção de domingos extrema (33 lojas) | Não entra bruta; decidir entre transformar ou manter só como descrição |
| 3 nulos de distância | Imputar e registrar quais lojas foram imputadas |
| Distância com cauda longa | log1p antes de padronizar |
| Escalas diferentes entre variáveis | Padronização (StandardScaler) depois das transformações |
| Extremos do tipo b (clientes, ticket) | Não remover como outlier: é um modelo de negócio real; checar assimetria das novas features |
| `feriado_estadual` com 0 e letras misturados | Ler como texto; se usado, codificar feriado × não feriado |
| `tipo_loja`, `sortimento`, `promo_continua` | Fora da matriz do modelo; preservados para baseline e descrição |

---

## 4. Ambiente

Python 3.10 · pandas 2.3.3 · numpy 2.2.6 · scipy 1.15.3 · scikit-learn 1.7.2 · matplotlib 3.10.9 · seaborn 0.13.2 · `SEED = 42`
