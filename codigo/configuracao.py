from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_MODELO = RAIZ / 'modelos' / 'modelo_clusterizacao.joblib'
CAMINHO_ESCALONADOR = RAIZ / 'modelos' / 'escalonador.joblib'
CAMINHO_KMEANS = RAIZ / 'modelos' / 'kmeans_k5.joblib'

FEATURES = ['venda_media_dia', 'ticket_medio', 'efeito_promo', 'volatilidade', 'sazonalidade', 'distancia_concorrente']
COLUNAS_VENDAS = ['loja', 'data', 'faturamento', 'clientes', 'aberta', 'promo']
COLUNAS_CADASTRO = ['loja', 'distancia_concorrente']
