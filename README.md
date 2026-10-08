# Retail Store Clustering

Segmentação de 1.115 lojas de varejo por **comparabilidade real**, para substituir a meta única de crescimento por metas definidas dentro de grupos de lojas parecidas.

> Projeto da pós-graduação em Data Analytics e IA Aplicada a Negócios (FNAT), conduzido pelas 6 fases do CRISP-DM.

## Problema

A rede aplicava o mesmo crescimento (+5%) a todas as lojas. Lojas em ponto favorável batiam a meta sem esforço, enquanto lojas pressionadas pela concorrência desistiam no primeiro trimestre. A pergunta de negócio passou a ser:

> Quais lojas são parecidas de verdade, e quem está performando mal em relação aos seus pares — não à rede inteira?

O resultado atende quatro áreas: **Comercial** (metas por grupo), **Trade marketing** (verba promocional), **Supply** (mix e reposição) e **Expansão** (enquadramento de lojas novas).

## Abordagem

- **Aprendizado não supervisionado (clusterização):** não existe rótulo verdadeiro de grupo.
- As categorias cadastrais (`tipo_loja`, `sortimento`) ficam **fora do modelo** e servem como **baseline** a ser superado.
- A solução só é aceita se for **interpretável, acionável, estável, melhor que o baseline e quantificada em R$**.

## Status

| Fase CRISP-DM | Status | Notebook |
|---|---|---|
| 1. Entendimento do Negócio | ✅ Concluída | — |
| 2. Entendimento dos Dados | ✅ Concluída | `02_entendimento_dados.ipynb` |
| 3. Preparação dos Dados | ✅ Concluída | `03_preparacao_dados.ipynb` |
| 4. Modelagem | ✅ Concluída | `04_modelagem.ipynb` |
| 5. Avaliação | ⏳ Em andamento | `05_avaliacao.ipynb` |
| 6. Deploy | — | — |

Decisões, descobertas e critérios de cada fase estão em **[docs/documentacao.md](docs/documentacao.md)**.

## Resultados até aqui

**Features do modelo (6):** venda média por dia (log), ticket médio, efeito da promoção, sazonalidade (log), pico de sábado e distância ao concorrente (log), padronizadas com `StandardScaler`.

**Modelo:** K-Means com k = 5 (`SEED = 42`), silhueta de 0,180.

| Cluster | Lojas | Venda média/dia (R$) | Ticket médio (R$) | Efeito da promoção | Distância mediana |
|---|---|---|---|---|---|
| 0 | 343 | 7.136 | 11,72 | 40,7% | 5.470 |
| 1 | 147 | 7.391 | 7,86 | 31,7% | 700 |
| 2 | 258 | 5.848 | 9,31 | 41,4% | 5.155 |
| 3 | 179 | 6.119 | 8,99 | 54,5% | 350 |
| 4 | 188 | 8.477 | 8,34 | 29,3% | 1.135 |
| Rede | 1.115 | 6.935 | 9,64 | 39,9% | 2.325 |

**Contra o baseline:** nas 6 métricas do modelo, os clusters explicam em média 36,0% da variância (η²), contra 13,2% do `tipo_loja`. Nas métricas fora do modelo o resultado é misto: ganham em volatilidade (38,8% contra 2,0%), empatam em clientes por dia e perdem em proporção de domingos abertos (3,7% contra 70,0%).

**Estabilidade:** ARI médio de 0,900 na troca de semente e 0,907 na reordenação das linhas; 0,754 em subamostras de 80%, abaixo do critério de 0,80.

**Em aberto na Fase 5:** nomear os clusters, montar a matriz cluster × área e quantificar o ganho em R$.

![Curva do cotovelo e silhueta média por k](relatorios/figuras/04_cotovelo_silhueta.png)

## Estrutura

```
retail-store-clustering/
├── dados/
│   ├── brutos/          # loja.csv e vendas.csv (não versionados)
│   └── processados/     # bases geradas pelo pipeline
├── notebooks/           # um notebook por fase do CRISP-DM
├── codigo/              # módulos Python reutilizáveis (usados no deploy)
├── modelos/             # artefatos treinados
├── relatorios/figuras/  # gráficos e entregáveis
├── docs/                # documentação do projeto
├── requirements.txt
└── README.md
```

## Dados

| Arquivo | Granularidade | Dimensão |
|---|---|---|
| `loja.csv` | uma linha por loja | 1.115 × 5 |
| `vendas.csv` | uma linha por loja por dia (01/2013 a 07/2015) | 1.017.209 × 9 |

Os arquivos originais não são versionados. Para reproduzir o projeto, coloque-os em `dados/brutos/`.

## Como executar

```bash
git clone https://github.com/V4lciJr/Auroa-Retail-Store-Clustering.git
cd Auroa-Retail-Store-Clustering
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
jupyter notebook notebooks/
```

## Tecnologias

Python 3.10 · pandas · numpy · scipy · scikit-learn · matplotlib · seaborn · Jupyter

## Autor

**Valci Júnior** — [LinkedIn](https://www.linkedin.com/in/valci-junior/)
