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

| Fase CRISP-DM | Status |
|---|---|
| 1. Entendimento do Negócio | ✅ Concluída |
| 2. Entendimento dos Dados | ✅ Concluída |
| 3. Preparação dos Dados | ⏳ Próxima |
| 4. Modelagem | — |
| 5. Avaliação | — |
| 6. Deploy | — |

Decisões, descobertas e critérios de cada fase estão em **[docs/documentacao.md](docs/documentacao.md)**.

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
git clone <url-do-repositorio>
cd retail-store-clustering
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
