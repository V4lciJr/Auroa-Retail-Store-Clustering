# Documentação — Retail Store Clustering

Segmentação das lojas da Aurora Varejo por comparabilidade real, seguindo o CRISP-DM.

**Status em 07/10/2026:** Fase 5 (Avaliação) em andamento. O ponto exato e as pendências estão na [seção 7](#7-onde-o-projeto-está).

| Fase CRISP-DM | Status | Notebook |
|---|---|---|
| 1. Entendimento do Negócio | Concluída | — |
| 2. Entendimento dos Dados | Concluída | `02_entendimento_dados.ipynb` |
| 3. Preparação dos Dados | Concluída | `03_preparacao_dados.ipynb` |
| 4. Modelagem | Concluída: K-Means com k = 5 treinado e salvo | `04_modelagem.ipynb` |
| 5. Avaliação | Em andamento: estabilidade, baseline e perfil médio executados | `05_avaliacao.ipynb` |
| 6. Deploy | Não iniciada | — |

Todos os números deste documento saem das saídas executadas nos notebooks. As figuras ficam em `relatorios/figuras/`; as Fases 2 e 5 não geraram figura (as evidências delas são tabelas).

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

### Defeitos encontrados × decisões levadas para a Fase 3

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

## 3. Preparação dos Dados

Notebook: `notebooks/03_preparacao_dados.ipynb`. Saídas: `base_lojas.parquet`, `base_lojas_transformada.parquet`, `X_modelo.parquet` e `modelos/escalonador.joblib`.

### 3.1 Tratamentos

| Tratamento | Resultado |
|---|---|
| Imputação de `distancia_concorrente` pela mediana (2.325) | Lojas 291, 622 e 879, marcadas em `distancia_imputada` |
| Filtro de dias de operação (`aberta = 1` e faturamento > 0) | 844.338 de 1.017.209 linhas; 172.871 removidas (17,0%); as 1.115 lojas continuam presentes |

### 3.2 O buraco do 2º semestre de 2014 distorce as features temporais?

Teste: nas lojas completas, recalcular a feature sem o 2º semestre de 2014, que é o que as 180 lojas incompletas sofrem.

| Feature | Variação mediana sem o período | Spearman entre versões | Decisão |
|---|---|---|---|
| Volatilidade | −0,2% | 0,994 | Calculada no histórico inteiro |
| Sazonalidade | +8,3% | 0,921 | Calculada na janela comum (sem o 2º sem/2014 para todas as lojas) |

Na janela comum, todas as lojas têm os 12 meses do ano representados.

### 3.3 Features criadas (uma linha por loja)

| Bloco | Feature | Como é calculada |
|---|---|---|
| Porte | `venda_media_dia` | Faturamento médio por dia de operação |
| Porte | `clientes_medios_dia` | Clientes médios por dia de operação |
| Porte | `ticket_medio` | Venda média ÷ clientes médios (razão de médias) |
| Promoção | `efeito_promo` | Venda média com promo ÷ sem promo − 1, só de segunda a sexta |
| Ritmo | `volatilidade` | Coeficiente de variação da venda diária |
| Ritmo | `sazonalidade` | Coeficiente de variação entre as médias dos 12 meses |
| Formato | `prop_domingos_abertos` | Domingos abertos ÷ domingos registrados |
| Formato | `pico_sabado` | Venda média de sábado ÷ venda média de segunda a sexta |
| Concorrência | `distancia_concorrente` | Cadastro, com imputação e versão em log |

- `efeito_promo` é restrito a segunda–sexta porque a promoção nunca ocorre no fim de semana (0% dos sábados e domingos). Média da rede: +39,9%; faixa de +1,9% a +102,1%; nenhuma loja com efeito negativo.
- Base final: 1.115 lojas × 14 colunas, sem nulos (as 9 features acima mais `distancia_concorrente_log`, `distancia_imputada`, `promo_continua`, `tipo_loja` e `sortimento`).

### 3.4 Forma das distribuições

Critério: transformar quando |skew| > 1.

| Variável | Skew original | Transformação | Skew depois |
|---|---|---|---|
| `venda_media_dia` | 1,75 | log1p | 0,30 |
| `clientes_medios_dia` | 3,03 | log1p | 0,76 |
| `distancia_concorrente` | 2,93 | log1p | −0,35 |
| `sazonalidade` | 2,01 | log | 0,06 |
| `ticket_medio` | 0,28 | nenhuma | — |
| `efeito_promo` | 0,61 | nenhuma | — |
| `volatilidade` | 0,72 | nenhuma | — |
| `pico_sabado` | −0,07 | nenhuma | — |
| `prop_domingos_abertos` | 5,97 | nenhuma resolve | 5,56 a 5,97 |

![Histogramas de clientes, sazonalidade e proporção de domingos, antes e depois do log1p](../relatorios/figuras/03_histogramas_assimetria.png)

**Figura 1 — `03_histogramas_assimetria.png`.** Linha de cima: distribuição original; linha de baixo: após log1p.

- **Clientes médios por dia:** a cauda à direita some com o log1p (skew 3,03 → 0,76).
- **Sazonalidade:** o log1p quase não muda a forma (2,01 → 1,73). Os valores vão de 0,03 a 0,33, faixa em que log1p(x) ≈ x. Por isso a sazonalidade recebeu log puro (skew 0,06).
- **Proporção de domingos abertos:** 1.082 lojas (97,0%) estão em zero e só 33 abrem. Log1p, binarização, Yeo-Johnson e quantil deixam o skew entre 5,56 e 5,97: nenhuma transformação cria variação onde há um valor só. A coluna ficou fora do modelo e segue como descrição.

O Yeo-Johnson foi testado como alternativa ao log e ordena as lojas exatamente da mesma forma (Spearman 1,0 nas quatro variáveis).

### 3.5 Correlação entre as candidatas

![Matriz de correlação de Pearson entre as 10 features candidatas](../relatorios/figuras/03_matriz_correlacao.png)

**Figura 2 — `03_matriz_correlacao.png`.** Pares com |r| ≥ 0,4:

| Par | Pearson | Spearman |
|---|---|---|
| venda (log) × clientes (log) | 0,82 | 0,80 |
| efeito_promo × volatilidade | 0,63 | 0,66 |
| volatilidade × pico_sabado | −0,62 | −0,61 |
| clientes (log) × ticket_medio | −0,52 | −0,50 |
| volatilidade × sazonalidade (log) | 0,44 | 0,40 |
| ticket_medio × distância (log) | 0,44 | 0,47 |

Duas redundâncias foram confirmadas com teste próprio:

- **Clientes:** venda = clientes × ticket é identidade exata (erro máximo 0,0). Em log, clientes + ticket explicam 99,0% da venda (R²). Manter os três seria contar o porte duas vezes.
- **Volatilidade:** efeito_promo + pico_sabado + sazonalidade explicam 76,8% dela (R²). Dentro de cada regime de promoção, a volatilidade média de segunda a sexta cai de 0,255 para 0,192, e a correlação com `efeito_promo` cai de 0,63 para 0,27.

### 3.6 Features do modelo

| Candidata | Decisão | Motivo |
|---|---|---|
| `venda_media_dia_log` | **entra** | Porte |
| `ticket_medio` | **entra** | Modelo de negócio (correlação 0,05 com a venda) |
| `efeito_promo` | **entra** | Resposta à promoção |
| `sazonalidade_log` | **entra** | Variação ao longo do ano |
| `pico_sabado` | **entra** | Padrão semanal |
| `distancia_concorrente_log` | **entra** | Contexto competitivo |
| `clientes_medios_dia_log` | validação | Redundante com venda e ticket |
| `volatilidade` | validação | 76,8% explicada por três features que já entram |
| `prop_domingos_abertos` | descrição | 97,0% de zeros |
| `promo_continua` | descrição | Política da empresa (decisão da Fase 2) |

Decisão do Valci: seguir com estas 6 features, e não com o conjunto da apostila (que usa `volatilidade` no lugar de `pico_sabado`). O efeito dessa troca foi medido na Fase 4 (seção 4.4).

As 6 features foram padronizadas com `StandardScaler` (média 0, desvio 1). Matriz final: 1.115 × 6, sem nulos.

| Feature | Média aprendida | Desvio aprendido |
|---|---|---|
| `venda_media_dia_log` | 8,7934 | 0,3138 |
| `ticket_medio` | 9,6438 | 1,9860 |
| `efeito_promo` | 0,3995 | 0,1266 |
| `sazonalidade_log` | −2,3802 | 0,2603 |
| `pico_sabado` | 0,8173 | 0,2160 |
| `distancia_concorrente_log` | 7,6457 | 1,5495 |

---

## 4. Modelagem

Notebook: `notebooks/04_modelagem.ipynb`. Saídas: `modelos/kmeans_k5.joblib` e `base_lojas_clusters.parquet`.

### 4.1 K-Means de k = 2 a 10

`n_init = 20`, `random_state = 42`.

| k | Inércia | Silhueta | Menor cluster | Maior cluster |
|---|---|---|---|---|
| 2 | 5.500,9 | 0,178 | 513 | 602 |
| 3 | 4.707,0 | 0,176 | 344 | 417 |
| 4 | 4.238,8 | 0,183 | 181 | 397 |
| 5 | 3.890,5 | 0,180 | 147 | 343 |
| 6 | 3.583,7 | 0,175 | 129 | 274 |
| 7 | 3.364,2 | 0,177 | 77 | 263 |
| 8 | 3.190,9 | 0,159 | 97 | 206 |
| 9 | 3.033,8 | 0,159 | 65 | 181 |
| 10 | 2.905,5 | 0,158 | 64 | 179 |

![Curva do cotovelo (inércia) e silhueta média para k de 2 a 10](../relatorios/figuras/04_cotovelo_silhueta.png)

**Figura 3 — `04_cotovelo_silhueta.png`.**

- **Cotovelo (esquerda):** a inércia cai de forma suave, sem dobra evidente. O cotovelo geométrico (ponto mais distante da reta entre k = 2 e k = 10) é k = 5, com distância 0,245; k = 4 (0,236) e k = 6 (0,239) ficam muito próximos.
- **Silhueta (direita):** praticamente plana, entre 0,158 e 0,183. Ela não separa os candidatos de k = 2 a 7 e só cai a partir de k = 8.
- **Contra o acaso:** na mesma base com cada coluna embaralhada, a silhueta fica entre 0,117 e 0,125. O ganho da base real é de 0,036 a 0,066, e a inércia real fica de 6,7% a 19,4% abaixo da referência. A estrutura existe, mas a separação entre os grupos é baixa.

### 4.2 Segunda opinião: clusterização hierárquica (Ward)

![Dendrograma de Ward truncado nos últimos 30 grupos](../relatorios/figuras/04_dendrograma.png)

**Figura 4 — `04_dendrograma.png`.** Cada folha é um grupo, com o número de lojas entre parênteses. Quanto maior o trecho vertical sem fusão, mais natural é cortar ali.

| Corte em | Altura em que os grupos se formam | Altura da próxima fusão | Salto relativo |
|---|---|---|---|
| 2 grupos | 37,31 | 44,68 | 19,8% |
| 3 grupos | 27,65 | 37,31 | 34,9% |
| 4 grupos | 26,00 | 27,65 | 6,4% |
| 5 grupos | 20,63 | 26,00 | 26,0% |
| 6 grupos | 20,07 | 20,63 | 2,8% |

- Os maiores saltos estão nos cortes em 3 grupos (34,9%) e em 5 grupos (26,0%). De 6 a 14 grupos, nenhum salto passa de 10%.
- O hierárquico não reproduz o K-Means: o ARI entre os dois métodos vai de 0,32 a 0,56 (0,412 em k = 5), e a silhueta do hierárquico é menor em todos os k (0,124 contra 0,180 em k = 5).
- Custo: a matriz de distâncias cresce com n². Medido nesta máquina: 0,011 s para 1.115 lojas e 2,44 s para 10.000. Calculado: 0,4 GB de memória para 10.000 pontos e 40 GB para 100.000.

### 4.3 Candidatos de k contra os critérios da Fase 1

Candidatos: k = 2, 3, 5 e 8. Estabilidade medida em 30 repetições de cada teste (ARI médio).

| k | Clusters sem traço forte | Menor cluster | ARI semente | ARI reordenação | ARI subamostra 80% |
|---|---|---|---|---|---|
| 2 | 1 | 513 | 0,982 | 0,975 | 0,879 |
| 3 | 0 | 344 | 0,992 | 0,993 | 0,937 |
| 5 | 0 | 147 | 0,900 | 0,907 | 0,754 |
| 8 | 1 | 97 | 0,852 | 0,844 | 0,734 |

"Traço forte" = centroide com |z| ≥ 0,75 em pelo menos uma feature.

Variância explicada (η², em %, médias sobre as métricas transformadas) e prévia do gap até a mediana dos pares:

| Segmentação | η² no modelo | η² fora do modelo | Gap anual (R$ mi) | CV da venda no grupo |
|---|---|---|---|---|
| Rede inteira | — | — | 228,10 | 0,34 |
| `tipo_loja` | 14,1 | 30,4 | 232,40 | 0,35 |
| Cluster k = 2 | 17,8 | 5,4 | 226,80 | 0,34 |
| Cluster k = 3 | 29,6 | 23,4 | 197,99 | 0,30 |
| Cluster k = 5 | 41,8 | 23,5 | 212,53 | 0,31 |
| Cluster k = 8 | 52,3 | 34,5 | 176,31 | 0,26 |

- Faturamento anual estimado da rede: R$ 2.346 mi. Em k = 5, capturar 25% do gap equivale a R$ 53,13 mi.
- Tipo b (17 lojas): fica em 1 cluster em k = 2, em 2 clusters em k = 3 (16 de 17 juntas) e em 3 clusters em k = 5 (12 de 17 juntas, num cluster de 188 lojas).
- k = 3 é o mais estável; k = 5 explica mais variância (41,8% contra 29,6%) e mantém todos os clusters com traço forte, ao custo de estabilidade menor. k = 8 explica ainda mais (52,3%), mas tem um cluster sem traço forte e a menor estabilidade dos quatro.

### 4.4 Teste: `pico_sabado` × `volatilidade` (conjunto da apostila), em k = 5

| Conjunto | Silhueta | ARI semente | ARI subamostra 80% | Menor cluster |
|---|---|---|---|---|
| Nosso (com `pico_sabado`) | 0,180 | 0,900 | 0,754 | 147 |
| Apostila (com `volatilidade`) | 0,181 | 0,977 | 0,755 | 154 |
| Os dois (7 features) | 0,165 | 0,803 | 0,639 | 156 |
| Nenhum dos dois (5 features) | 0,186 | 0,954 | 0,826 | 153 |

- Em k = 5, o conjunto da apostila é mais estável à troca de semente (0,977 contra 0,900) e empata na subamostra (0,755 contra 0,754).
- O resultado depende do k: o nosso conjunto é mais estável em k = 3 (subamostra 0,937 contra 0,853) e em k = 4 (0,906 contra 0,817); o da apostila, em k = 6 (0,937 contra 0,821).
- Retirando uma feature por vez do nosso conjunto, a que mais pesa na instabilidade é `efeito_promo`: sem ela, o ARI de subamostra sobe para 0,942.
- O conjunto com `pico_sabado` foi mantido.

### 4.5 Modelo final: K-Means com k = 5

Inércia 3.890,5 e silhueta 0,180. O maior cluster tem 2,33× o tamanho do menor.

| Cluster | Lojas | % da rede | Silhueta média | % com silhueta negativa |
|---|---|---|---|---|
| 0 | 343 | 30,8 | 0,229 | 0,9 |
| 1 | 147 | 13,2 | 0,092 | 22,4 |
| 2 | 258 | 23,1 | 0,224 | 0,0 |
| 3 | 179 | 16,1 | 0,129 | 12,3 |
| 4 | 188 | 16,9 | 0,146 | 11,2 |

Centroides em desvios-padrão da rede (z):

| Feature | C0 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|
| `venda_media_dia_log` | 0,16 | 0,19 | −0,50 | −0,36 | 0,58 |
| `ticket_medio` | 1,04 | −0,90 | −0,17 | −0,33 | −0,66 |
| `efeito_promo` | 0,06 | −0,65 | 0,12 | 1,15 | −0,84 |
| `sazonalidade_log` | −0,02 | 1,21 | 0,20 | 0,06 | −1,23 |
| `pico_sabado` | 0,70 | 0,55 | −1,07 | −0,33 | 0,07 |
| `distancia_concorrente_log` | 0,59 | −0,53 | 0,66 | −1,15 | −0,47 |

O maior cluster (0) não é um "resto": tem a maior silhueta média e menos de 1% das lojas com silhueta negativa. Os clusters 1 e 3 são os menos coesos.

Variáveis binárias que ficaram fora do modelo:

| Cluster | `promo_continua` (%) | Lojas que abrem domingo | Distância imputada |
|---|---|---|---|
| 0 | 62,4 | 3 | 0 |
| 1 | 46,3 | 13 | 0 |
| 2 | 43,0 | 4 | 3 |
| 3 | 68,2 | 0 | 0 |
| 4 | 29,8 | 13 | 0 |
| Rede | 51,2 | 33 | 3 |

Associação com os clusters: V de Cramér 0,269 para `promo_continua` e 0,190 para abrir domingo.

---

## 5. Avaliação (em andamento)

Notebook: `notebooks/05_avaliacao.ipynb`. Os critérios da Fase 1 são cobrados um por vez sobre o K-Means com k = 5. Executados até aqui: estabilidade, comparação com o baseline e perfil médio. Esta fase ainda não gerou figura.

### 5.1 Estabilidade

Reexecutar com a mesma semente e a mesma base devolve exatamente os mesmos grupos (ARI 1,0 em 5 reexecuções).

| Teste (30 execuções) | ARI médio | ARI mínimo | Execuções abaixo de 0,80 | % de lojas que trocam (média) |
|---|---|---|---|---|
| Troca de semente | 0,900 | 0,742 | 3 | 5,1 |
| Reordenação das linhas | 0,907 | 0,706 | 2 | 4,8 |
| Subamostra de 80% | 0,754 | 0,502 | 16 | 14,2 |

Contra o critério da Fase 1 (ARI médio ≥ 0,80): atendido na troca de semente e na reordenação; **não atendido na subamostra de 80%** (0,754).

Estabilidade por loja, em 100 subamostras de 80%:

| Permanência no mesmo cluster | Lojas | % |
|---|---|---|
| Acima de 95% | 548 | 49,1 |
| 80% a 95% | 292 | 26,2 |
| 50% a 80% | 194 | 17,4 |
| Até 50% | 81 | 7,3 |

| Cluster | Permanência média | % de lojas abaixo de 80% |
|---|---|---|
| 0 | 0,930 | 12,2 |
| 1 | 0,777 | 36,1 |
| 2 | 0,868 | 27,5 |
| 3 | 0,746 | 42,5 |
| 4 | 0,888 | 16,0 |

- A instabilidade se concentra nos clusters 1 e 3, os mesmos de menor silhueta na Fase 4.
- Lojas instáveis são as de fronteira: silhueta média de 0,085 nas instáveis (< 80%) contra 0,241 nas estáveis (> 95%); Spearman entre silhueta e permanência de 0,585.

O modelo salvo não é a solução de menor inércia que o K-Means encontra:

| Solução | Inércia | Tamanhos dos clusters |
|---|---|---|
| Referência (semente 42, `n_init = 20`) | 3.890,5 | 343, 147, 258, 179, 188 |
| `n_init = 500` | 3.884,0 | 345, 152, 269, 164, 185 |

A diferença de inércia é de 0,17%, o ARI entre as duas é 0,908 e 53 lojas mudam de cluster. Medida contra a solução de menor inércia, a estabilidade sobe para ARI 0,950 na troca de semente e 0,792 na subamostra de 80%.

### 5.2 Os clusters são melhores que o cadastro?

**Teste A — concordância com o cadastro**

| Categoria | ARI | NMI |
|---|---|---|
| `tipo_loja` | 0,152 | 0,174 |
| `sortimento` | 0,038 | 0,045 |

Os clusters não reconstroem o cadastro. As maiores concentrações: 71,0% das lojas do tipo d estão no cluster 0 e 70,6% das lojas do tipo b estão no cluster 4.

**Teste B — variância explicada (η², em %, métricas em unidade original)**

| Métrica | Origem | `tipo_loja` | `sortimento` | Cluster | Aleatório |
|---|---|---|---|---|---|
| `venda_media_dia` | no modelo | 2,8 | 2,5 | 14,5 | 0,4 |
| `ticket_medio` | no modelo | 42,3 | 11,1 | 54,1 | 0,3 |
| `efeito_promo` | no modelo | 6,0 | 6,9 | 39,2 | 0,3 |
| `sazonalidade` | no modelo | 2,9 | 5,0 | 41,3 | 0,4 |
| `pico_sabado` | no modelo | 22,4 | 5,4 | 47,6 | 0,3 |
| `distancia_concorrente` | no modelo | 2,5 | 2,4 | 19,6 | 0,3 |
| `clientes_medios_dia` | fora | 25,5 | 10,9 | 25,3 | 0,4 |
| `volatilidade` | fora | 2,0 | 1,5 | 38,8 | 0,4 |
| `prop_domingos_abertos` | fora | 70,0 | 37,4 | 3,7 | 0,4 |

| Média de η² | `tipo_loja` | Cluster |
|---|---|---|
| Métricas no modelo | 13,2 | 36,0 |
| Métricas fora do modelo | 32,5 | 22,6 |

- Nas métricas do modelo, os clusters explicam 36,0% contra 13,2% do `tipo_loja`.
- Fora do modelo, o resultado é misto: os clusters ganham com folga em volatilidade (38,8 contra 2,0), empatam em clientes (25,3 contra 25,5) e perdem em domingos abertos (3,7 contra 70,0). É a perda em domingos que puxa a média fora do modelo para baixo do `tipo_loja`.
- Com o mesmo número de grupos do `tipo_loja` (k = 4), o padrão se repete: os clusters ganham em 7 das 9 métricas, empatam em clientes (25,1 contra 25,5) e perdem em domingos (1,8 contra 70,0).
- Os valores diferem dos da seção 4.3 porque lá o η² foi calculado sobre as métricas transformadas (log).

### 5.3 Perfil médio de cada cluster

Médias por cluster; a distância é a mediana.

| Métrica | C0 | C1 | C2 | C3 | C4 | Rede |
|---|---|---|---|---|---|---|
| Lojas | 343 | 147 | 258 | 179 | 188 | 1.115 |
| Venda média/dia (R$) | 7.136 | 7.391 | 5.848 | 6.119 | 8.477 | 6.935 |
| Clientes/dia | 616 | 968 | 631 | 701 | 1.060 | 755 |
| Ticket médio (R$) | 11,72 | 7,86 | 9,31 | 8,99 | 8,34 | 9,64 |
| Efeito da promoção | 40,7% | 31,7% | 41,4% | 54,5% | 29,3% | 39,9% |
| Volatilidade | 0,250 | 0,265 | 0,314 | 0,313 | 0,218 | 0,272 |
| Sazonalidade | 0,093 | 0,131 | 0,099 | 0,095 | 0,069 | 0,096 |
| Pico de sábado | 0,969 | 0,936 | 0,587 | 0,744 | 0,833 | 0,817 |
| Distância mediana | 5.470 | 700 | 5.155 | 350 | 1.135 | 2.325 |
| `promo_continua` | 62,4% | 46,3% | 43,0% | 68,2% | 29,8% | 51,2% |
| Lojas que abrem domingo | 3 | 13 | 4 | 0 | 13 | 33 |

Os clusters ainda não têm nome: a nomeação faz parte do critério "interpretável", ainda não executado.

---

## 6. Deploy

Não iniciado. A pasta `codigo/` (funções reutilizáveis de preparação, features, modelo e inferência) ainda está vazia.

---

## 7. Onde o projeto está

**Ponto atual:** Fase 5, com três blocos executados (estabilidade, comparação com o baseline e perfil médio).

Situação de cada critério de sucesso da Fase 1:

| Critério | Situação | Evidência até aqui |
|---|---|---|
| Estável | Parcial | ARI 0,900 (semente) e 0,907 (reordenação); 0,754 na subamostra de 80%, abaixo de 0,80 |
| Melhor que o baseline | Executado | η² médio de 36,0% contra 13,2% nas métricas do modelo; 22,6% contra 32,5% fora do modelo |
| Interpretável | Em andamento | Perfil médio e centroides prontos; clusters sem nome |
| Acionável | Pendente | Matriz cluster × área não construída |
| Quantificado | Pendente | Só a prévia da Fase 4 (gap de R$ 212,53 mi/ano em k = 5); faltam os cenários de captura e as metas somando +5% |

Pontos em aberto, sem decisão registrada nos notebooks:

- O teste de subamostra não atinge o ARI de 0,80 definido na Fase 1.
- Existe uma solução de inércia 0,17% menor (`n_init = 500`) que move 53 lojas em relação ao modelo salvo.

Pendências fora da análise:

- **Versionamento:** o último commit cobre as Fases 1 e 2. Ainda não foram commitados os notebooks 04 e 05, a versão atual do notebook 03, as 4 figuras e os 2 artefatos em `modelos/`. Enquanto as figuras não forem commitadas, as imagens deste documento não aparecem no GitHub.
- **README:** a tabela de status ainda indica a Fase 3 como próxima.

### Artefatos gerados

| Arquivo | Fase | Conteúdo |
|---|---|---|
| `dados/processados/base_lojas.parquet` | 3 | 1.115 lojas × 14 colunas, antes das transformações |
| `dados/processados/base_lojas_transformada.parquet` | 3 | Base com as colunas em log |
| `dados/processados/X_modelo.parquet` | 3 | 6 features padronizadas |
| `modelos/escalonador.joblib` | 3 | `StandardScaler` ajustado |
| `modelos/kmeans_k5.joblib` | 4 | K-Means com k = 5 |
| `dados/processados/base_lojas_clusters.parquet` | 4 | Base com o cluster de cada loja |
| `relatorios/figuras/03_histogramas_assimetria.png` | 3 | Figura 1 |
| `relatorios/figuras/03_matriz_correlacao.png` | 3 | Figura 2 |
| `relatorios/figuras/04_cotovelo_silhueta.png` | 4 | Figura 3 |
| `relatorios/figuras/04_dendrograma.png` | 4 | Figura 4 |

Os dados em `dados/` não são versionados (`.gitignore`).

---

## 8. Ambiente

Python 3.10 · pandas 2.3.3 · numpy 2.2.6 · scipy 1.15.3 · scikit-learn 1.7.2 · matplotlib 3.10.9 · seaborn 0.13.2 · `SEED = 42`
