# Empacota o modelo vencedor e suas regras de uso em um único artefato, sem novo ajuste.
# Uso: python -m codigo.exportar_modelo
import hashlib
import json
from datetime import date

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from .configuracao import CAMINHO_ESCALONADOR, CAMINHO_KMEANS, CAMINHO_MODELO, FEATURES, RAIZ

VERSAO = '1.0.0'

NOMES_CLUSTER = {0: 'Bairro competitivo de cesta pequena', 1: 'Destino de cesta grande', 2: 'Sazonal',
                 3: 'Dependente de promoção', 4: 'Alto fluxo, cesta pequena'}

# notebook 06, seções 1 a 6
REGRAS_META = {'meta_manutencao': 0.02, 'captura_gap': 0.25, 'limiar_acao': 0.10,
               'fator_calibracao': 1.220191699246372, 'teto': 0.20}

# notebook 06, seção 8
REGRAS_USO = {'meses_minimos': 12, 'meses_definitiva': 24, 'limiar_margem_fronteira': 0.10, 'percentil_atipico': 0.99}


def sha256(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def montar_pipeline(escalonador, kmeans):
    # saída em DataFrame no escalonador para o K-Means receber os nomes das features com que foi treinado
    return Pipeline([
        ('log1p', FunctionTransformer(np.log1p)),
        ('escalonador', escalonador.set_output(transform='pandas')),
        ('kmeans', kmeans),
    ])


def exportar():
    escalonador = joblib.load(CAMINHO_ESCALONADOR)
    kmeans = joblib.load(CAMINHO_KMEANS)
    pipeline = montar_pipeline(escalonador, kmeans)

    base = pd.read_parquet(RAIZ / 'dados' / 'processados' / 'base_lojas_clusters.parquet')
    plano = pd.read_csv(RAIZ / 'dados' / 'processados' / 'plano_metas.csv')
    cadastro = pd.read_csv(RAIZ / 'dados' / 'brutos' / 'loja.csv')

    # trava: o pipeline montado tem de devolver exatamente os rótulos do treino
    rotulos = pipeline.predict(base[FEATURES])
    if not np.array_equal(rotulos, base['cluster'].to_numpy()):
        raise RuntimeError('o pipeline não reproduz os clusters do treino')

    distancias = np.asarray(pipeline.transform(base[FEATURES]))
    distancia_propria = pd.Series(distancias[np.arange(len(base)), rotulos], index=base.index)
    limites = distancia_propria.groupby(base['cluster']).quantile(REGRAS_USO['percentil_atipico'])
    benchmarks = base.groupby('cluster')['venda_media_dia'].median()

    # trava: a regra de meta exportada reproduz a coluna meta_pct do plano
    r = REGRAS_META
    meta = np.minimum((r['meta_manutencao'] + r['captura_gap'] * plano['gap_pct']) * r['fator_calibracao'], r['teto'])
    if not np.allclose(meta, plano['meta_pct'], atol=1e-9):
        raise RuntimeError('a regra de meta não reproduz o plano de metas')

    definicoes = {
        'versao': VERSAO,
        'data_exportacao': date.today().isoformat(),
        'features': FEATURES,
        'transformacao': 'log1p nas seis features -> StandardScaler -> KMeans (k=5)',
        'mediana_distancia_concorrente': float(cadastro['distancia_concorrente'].median()),
        'clusters': {int(c): {'nome': NOMES_CLUSTER[c],
                              'lojas_no_treino': int((base['cluster'] == c).sum()),
                              'benchmark_venda_media_dia': float(benchmarks[c]),
                              'limite_distancia_atipica': float(limites[c])} for c in sorted(NOMES_CLUSTER)},
        'regras_meta': REGRAS_META,
        'regras_uso': REGRAS_USO,
        'origem': {'escalonador_sha256': sha256(CAMINHO_ESCALONADOR), 'kmeans_sha256': sha256(CAMINHO_KMEANS),
                   'scikit_learn': sklearn.__version__, 'pandas': pd.__version__, 'numpy': np.__version__},
    }
    joblib.dump({'pipeline': pipeline, **definicoes}, CAMINHO_MODELO)
    CAMINHO_MODELO.with_suffix('.json').write_text(json.dumps(definicoes, ensure_ascii=False, indent=2), encoding='utf-8')
    return definicoes


if __name__ == '__main__':
    definicoes = exportar()
    print(f"modelo {definicoes['versao']} exportado em {CAMINHO_MODELO.relative_to(RAIZ)}")
