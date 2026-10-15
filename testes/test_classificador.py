import hashlib

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from codigo import ClassificadorLojas
from codigo.configuracao import CAMINHO_ESCALONADOR, CAMINHO_KMEANS, FEATURES, RAIZ

BASE_TREINO = RAIZ / 'dados' / 'processados' / 'base_lojas_clusters.parquet'
VENDAS = RAIZ / 'dados' / 'brutos' / 'vendas.csv'
CADASTRO = RAIZ / 'dados' / 'brutos' / 'loja.csv'
EXEMPLO = RAIZ / 'dados' / 'exemplos' / 'lojas_novas.csv'
sem_base = pytest.mark.skipif(not BASE_TREINO.exists(), reason='base processada ausente (dados não versionados)')
sem_brutos = pytest.mark.skipif(not VENDAS.exists(), reason='dados brutos ausentes (dados não versionados)')


@pytest.fixture(scope='module')
def classificador():
    return ClassificadorLojas()


def loja_valida(**alteracoes):
    linha = {'loja': 9999, 'venda_media_dia': 7000.0, 'ticket_medio': 9.5, 'efeito_promo': 0.4, 'volatilidade': 0.27,
             'sazonalidade': 0.09, 'distancia_concorrente': 2300.0, 'meses_historico': 30}
    return pd.DataFrame([{**linha, **alteracoes}])


def test_artefatos_treinados_nao_mudaram(classificador):
    origem = classificador.modelo['origem']
    assert hashlib.sha256(CAMINHO_ESCALONADOR.read_bytes()).hexdigest() == origem['escalonador_sha256']
    assert hashlib.sha256(CAMINHO_KMEANS.read_bytes()).hexdigest() == origem['kmeans_sha256']


def test_pipeline_usa_os_objetos_treinados(classificador):
    kmeans, escalonador = joblib.load(CAMINHO_KMEANS), joblib.load(CAMINHO_ESCALONADOR)
    passos = classificador.pipeline.named_steps
    np.testing.assert_array_equal(passos['kmeans'].cluster_centers_, kmeans.cluster_centers_)
    np.testing.assert_array_equal(passos['escalonador'].mean_, escalonador.mean_)
    np.testing.assert_array_equal(passos['escalonador'].scale_, escalonador.scale_)


def test_classificar_nao_chama_fit(classificador, monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError('o modelo não pode ser ajustado no deploy')
    for classe in (KMeans, StandardScaler):
        monkeypatch.setattr(classe, 'fit', proibido)
        monkeypatch.setattr(classe, 'fit_transform', proibido)
    monkeypatch.setattr(KMeans, 'fit_predict', proibido)
    assert classificador.classificar_indicadores(loja_valida())['status'].iloc[0] == 'definitiva'


def test_centroides_caem_no_proprio_cluster(classificador):
    passos = classificador.pipeline.named_steps
    centros = passos['escalonador'].inverse_transform(passos['kmeans'].cluster_centers_)
    entrada = pd.DataFrame(np.expm1(centros), columns=FEATURES).assign(loja=range(5), meses_historico=30)
    resultado = classificador.classificar_indicadores(entrada)
    assert resultado['cluster'].tolist() == [0, 1, 2, 3, 4]


@sem_base
def test_reproduz_os_clusters_do_treino(classificador):
    base = pd.read_parquet(BASE_TREINO).reset_index()
    resultado = classificador.classificar_indicadores(base.assign(meses_historico=30))
    assert (resultado['cluster'].to_numpy() == base['cluster'].to_numpy()).all()


@sem_brutos
def test_historico_bruto_reproduz_o_treino(classificador):
    vendas = pd.read_csv(VENDAS, dtype={'feriado_estadual': str})
    resultado = classificador.classificar_historico(vendas, pd.read_csv(CADASTRO)).set_index('loja')
    treino = pd.read_parquet(BASE_TREINO)['cluster'] if BASE_TREINO.exists() else None
    assert len(resultado) == 1115 and resultado['status'].eq('definitiva').all()
    if treino is not None:
        assert (resultado.loc[treino.index, 'cluster'] == treino).all()


def test_exemplo_de_lojas_novas(classificador):
    resultado = classificador.classificar_indicadores(pd.read_csv(EXEMPLO))
    assert len(resultado) == 3 and resultado['cluster'].notna().all()


def test_distancia_ausente_e_imputada_com_alerta(classificador):
    resultado = classificador.classificar_indicadores(loja_valida(distancia_concorrente=np.nan)).iloc[0]
    assert resultado['status'] == 'definitiva' and 'imputada' in resultado['alertas']


@pytest.mark.parametrize('alteracao, motivo', [
    ({'meses_historico': 6}, 'histórico menor'),
    ({'venda_media_dia': 0}, 'fora do domínio: venda_media_dia'),
    ({'efeito_promo': -1.2}, 'fora do domínio: efeito_promo'),
    ({'sazonalidade': np.nan}, 'indicador ausente ou inválido: sazonalidade'),
])
def test_entradas_invalidas_nao_sao_classificadas(classificador, alteracao, motivo):
    resultado = classificador.classificar_indicadores(loja_valida(**alteracao)).iloc[0]
    assert resultado['status'] == 'não classificada' and motivo in resultado['motivo'] and pd.isna(resultado['cluster'])


def test_historico_entre_12_e_23_meses_e_provisorio(classificador):
    assert classificador.classificar_indicadores(loja_valida(meses_historico=15))['status'].iloc[0] == 'provisória'


def test_coluna_obrigatoria_ausente(classificador):
    with pytest.raises(ValueError, match='colunas obrigatórias'):
        classificador.classificar_indicadores(loja_valida().drop(columns='ticket_medio'))
