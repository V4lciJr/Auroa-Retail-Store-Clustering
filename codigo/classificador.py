# Enquadra lojas novas nos clusters existentes usando o pipeline exportado; nada aqui ajusta o modelo.
import joblib
import numpy as np
import pandas as pd

from .configuracao import CAMINHO_MODELO, FEATURES
from .indicadores import calcular_indicadores

# limites de domínio: o log1p exige valor > -1 e os indicadores de porte não podem ser zero
DOMINIO = {'venda_media_dia': (0, False), 'ticket_medio': (0, False), 'efeito_promo': (-1, False),
           'volatilidade': (0, True), 'sazonalidade': (0, True), 'distancia_concorrente': (0, True)}
COLUNAS_SAIDA = ['loja', 'status', 'motivo', 'cluster', 'nome_cluster', 'segundo_cluster', 'margem', 'distancia_centroide',
                 'alertas', 'venda_media_dia', 'benchmark_cluster', 'gap_pct', 'meta_sugerida_pct', 'prioridade']


class ClassificadorLojas:
    def __init__(self, caminho_modelo=CAMINHO_MODELO):
        self.modelo = joblib.load(caminho_modelo)
        self.pipeline = self.modelo['pipeline']
        self.clusters = self.modelo['clusters']
        self.regras_uso = self.modelo['regras_uso']
        self.regras_meta = self.modelo['regras_meta']

    @property
    def versao(self):
        return self.modelo['versao']

    def classificar_historico(self, vendas, cadastro):
        indicadores = calcular_indicadores(vendas, cadastro, self.modelo['mediana_distancia_concorrente'])
        # loja cadastrada sem nenhum dia de operação continua no resultado, como não classificada
        sem_operacao = pd.DataFrame({'loja': sorted(set(cadastro['loja']) - set(indicadores['loja'])), 'meses_historico': 0})
        return self.classificar_indicadores(pd.concat([indicadores, sem_operacao], ignore_index=True))

    def classificar_indicadores(self, indicadores):
        obrigatorias = ['loja', 'meses_historico'] + [f for f in FEATURES if f != 'distancia_concorrente']
        faltando = [c for c in obrigatorias if c not in indicadores.columns]
        if faltando:
            raise ValueError(f'entrada sem as colunas obrigatórias: {faltando}')

        tabela = indicadores.copy().reset_index(drop=True)
        if 'distancia_concorrente' not in tabela.columns:
            tabela['distancia_concorrente'] = np.nan
        tabela[FEATURES + ['meses_historico']] = tabela[FEATURES + ['meses_historico']].apply(pd.to_numeric, errors='coerce')
        tabela['distancia_imputada'] = tabela['distancia_concorrente'].isna().astype(int)
        tabela['distancia_concorrente'] = tabela['distancia_concorrente'].fillna(self.modelo['mediana_distancia_concorrente'])

        motivo = self._validar(tabela)
        validas = motivo.eq('')
        resultado = pd.DataFrame({'loja': tabela['loja'], 'status': 'não classificada', 'motivo': motivo})

        if validas.any():
            entrada = tabela.loc[validas, FEATURES]
            distancias = np.asarray(self.pipeline.transform(entrada))
            ordem = np.argsort(distancias, axis=1)
            cluster = self.pipeline.predict(entrada)
            d1 = distancias[np.arange(len(entrada)), ordem[:, 0]]
            d2 = distancias[np.arange(len(entrada)), ordem[:, 1]]

            parte = pd.DataFrame(index=entrada.index)
            parte['cluster'] = cluster
            parte['nome_cluster'] = [self.clusters[c]['nome'] for c in cluster]
            parte['segundo_cluster'] = ordem[:, 1]
            parte['margem'] = (d2 - d1) / d2
            parte['distancia_centroide'] = d1
            meses = tabela.loc[validas, 'meses_historico']
            parte['status'] = np.where(meses >= self.regras_uso['meses_definitiva'], 'definitiva', 'provisória')
            parte['alertas'] = self._alertas(parte, tabela.loc[validas])
            parte = parte.join(self._meta(parte['cluster'], tabela.loc[validas, 'venda_media_dia']))
            resultado = resultado.join(parte.drop(columns='status'))
            resultado.loc[validas, 'status'] = parte['status']
        resultado = resultado.reindex(columns=COLUNAS_SAIDA)
        return resultado.astype({'cluster': 'Int64', 'segundo_cluster': 'Int64'})

    def _validar(self, tabela):
        curto = tabela['meses_historico'].fillna(0) < self.regras_uso['meses_minimos']
        motivo = pd.Series('', index=tabela.index).mask(curto, f"histórico menor que {self.regras_uso['meses_minimos']} meses")
        for feature, (minimo, aceita_igual) in DOMINIO.items():
            valor = tabela[feature]
            fora = valor.lt(minimo) if aceita_igual else valor.le(minimo)
            motivo = motivo.mask(motivo.eq('') & ~np.isfinite(valor), f'indicador ausente ou inválido: {feature}')
            motivo = motivo.mask(motivo.eq('') & fora, f'fora do domínio: {feature}')
        return motivo

    def _alertas(self, parte, tabela):
        limite = parte['cluster'].map(lambda c: self.clusters[c]['limite_distancia_atipica'])
        marcas = pd.DataFrame({
            'fronteira de cluster': parte['margem'] < self.regras_uso['limiar_margem_fronteira'],
            'perfil atípico': parte['distancia_centroide'] > limite,
            'distância ao concorrente imputada': tabela['distancia_imputada'].eq(1),
        })
        return marcas.apply(lambda linha: '; '.join(linha.index[linha]), axis=1)

    def _meta(self, cluster, venda_media_dia):
        r = self.regras_meta
        benchmark = cluster.map(lambda c: self.clusters[c]['benchmark_venda_media_dia'])
        gap = ((benchmark - venda_media_dia) / venda_media_dia).clip(lower=0)
        meta = np.minimum((r['meta_manutencao'] + r['captura_gap'] * gap) * r['fator_calibracao'], r['teto'])
        return pd.DataFrame({'venda_media_dia': venda_media_dia, 'benchmark_cluster': benchmark, 'gap_pct': gap,
                             'meta_sugerida_pct': meta,
                             'prioridade': np.where(gap >= r['limiar_acao'], 'Ação', 'Acompanhamento')})
