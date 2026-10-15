# Cálculo dos seis indicadores do modelo a partir do histórico diário, com as mesmas regras do treino (notebook 03, seção 14).
import pandas as pd

from .configuracao import COLUNAS_CADASTRO, COLUNAS_VENDAS


def _exigir_colunas(tabela, colunas, nome):
    faltando = [c for c in colunas if c not in tabela.columns]
    if faltando:
        raise ValueError(f'{nome} sem as colunas obrigatórias: {faltando}')


def calcular_indicadores(vendas, cadastro, mediana_distancia):
    _exigir_colunas(vendas, COLUNAS_VENDAS, 'vendas')
    _exigir_colunas(cadastro, COLUNAS_CADASTRO, 'cadastro')

    # só dias de operação: loja aberta e com faturamento
    operacao = vendas.loc[(vendas['aberta'] == 1) & (vendas['faturamento'] > 0), COLUNAS_VENDAS].copy()
    operacao['data'] = pd.to_datetime(operacao['data'])
    operacao['ano'] = operacao['data'].dt.year
    operacao['mes'] = operacao['data'].dt.month
    por_loja = operacao.groupby('loja')

    indicadores = pd.DataFrame({'venda_media_dia': por_loja['faturamento'].mean()})
    # ticket como razão de médias: cada cliente pesa igual
    indicadores['ticket_medio'] = indicadores['venda_media_dia'] / por_loja['clientes'].mean()

    media_promo = operacao.groupby(['loja', 'promo'])['faturamento'].mean().unstack().reindex(columns=[0, 1])
    indicadores['efeito_promo'] = media_promo[1] / media_promo[0] - 1
    indicadores['volatilidade'] = por_loja['faturamento'].std() / indicadores['venda_media_dia']

    # cada mês dividido pela média do próprio ano da loja; a sazonalidade é o desvio entre os 12 meses
    media_mes = operacao.groupby(['loja', 'ano', 'mes'])['faturamento'].mean()
    relativa = media_mes / media_mes.groupby(level=['loja', 'ano']).transform('mean')
    indicadores['sazonalidade'] = relativa.groupby(level=['loja', 'mes']).mean().groupby(level='loja').std()

    distancia = cadastro.drop_duplicates('loja').set_index('loja')['distancia_concorrente']
    distancia = distancia.reindex(indicadores.index)
    indicadores['distancia_imputada'] = distancia.isna().astype(int)
    indicadores['distancia_concorrente'] = distancia.fillna(mediana_distancia)

    indicadores['meses_historico'] = operacao.groupby('loja')[['ano', 'mes']].apply(lambda d: len(d.drop_duplicates()))
    indicadores['dias_operacao'] = por_loja.size()
    indicadores.index.name = 'loja'
    return indicadores.reset_index()
