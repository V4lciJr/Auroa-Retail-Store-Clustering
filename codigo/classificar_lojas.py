# Uso:
#   python -m codigo.classificar_lojas --indicadores dados/exemplos/lojas_novas.csv
#   python -m codigo.classificar_lojas --vendas vendas_lojas_novas.csv --cadastro cadastro_lojas_novas.csv --saida resultado.csv
import argparse

import pandas as pd

from .classificador import ClassificadorLojas


def main():
    parser = argparse.ArgumentParser(description='Enquadra lojas novas nos clusters da rede sem retreinar o modelo.')
    entrada = parser.add_mutually_exclusive_group(required=True)
    entrada.add_argument('--indicadores', help='CSV com os seis indicadores e meses_historico por loja')
    entrada.add_argument('--vendas', help='CSV diário no formato de vendas.csv (exige --cadastro)')
    parser.add_argument('--cadastro', help='CSV no formato de loja.csv')
    parser.add_argument('--saida', help='caminho do CSV de resultado')
    args = parser.parse_args()

    classificador = ClassificadorLojas()
    if args.indicadores:
        resultado = classificador.classificar_indicadores(pd.read_csv(args.indicadores))
    else:
        if not args.cadastro:
            parser.error('--vendas exige --cadastro')
        vendas = pd.read_csv(args.vendas, dtype={'feriado_estadual': str})
        resultado = classificador.classificar_historico(vendas, pd.read_csv(args.cadastro))

    print(f'modelo {classificador.versao} | {len(resultado)} lojas\n')
    print(resultado.set_index('loja').round(4).T.to_string())
    if args.saida:
        resultado.to_csv(args.saida, index=False)
        print(f'\nresultado salvo em {args.saida}')


if __name__ == '__main__':
    main()
