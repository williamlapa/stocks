import streamlit as st
import pandas as pd
import numpy as np
from pandas_datareader import data as web
from datetime import datetime, timedelta
from workadays import workdays as wd
import seaborn as sns
import matplotlib.pyplot as plt

st.title('Análise de Ações')

dataInicio = '18/06/2017'
datas = ['21/01/2022','18/02/2022','18/03/2022','15/04/2022','20/05/2022','17/06/2022','15/07/2022','19/08/2022','16/09/2022','21/10/2022','18/11/2022','16/12/2022']

# Escolha das datas
data1 = st.sidebar.selectbox('Escolha o PRIMEIRO vencimento da opção:', datas)
data2 = st.sidebar.selectbox('Escolha o PRÓXIMO vencimento da opção:', datas[datas.index(data1)+1:])

# criando a sidebar
st.sidebar.header('Escolha os ações')

def pegar_dados_acoes():
    path = './acoes.csv'
    return pd.read_csv(path, delimiter=';')

df = pegar_dados_acoes()

acao = df['snome']

#nome_acao_escolhida = st.sidebar.selectbox('Escolha uma ação:', acao)
nome_acao_escolhida = st.sidebar.multiselect(
    'Escolha ativos:',
    acao,
     ['VALE3-VALE', 'PETR4-PETROBRAS'])

#st.sidebar.write('Você escolheu:', nome_acao_escolhida)


# usa a ação definida no sidebar - AQUI TRANSFORME A ESCOLHA EM UMA LISTA
df_acao = df[df['snome'].isin(nome_acao_escolhida)]
acao_escolhida = df_acao.iloc[:,0]

#st.write(acao_escolhida)

#### FUNÇÕES NOVAS ####
@st.cache(allow_output_mutation=True)
def cotacoes_acoes(tickers, dataInicio):
    """Baixa todos os dados de fechamento de mercado passando os tickers em
    lista e a data de inicio no formato mm/dd/aaaa
    Como padrão: Ínidce Bovespa e 01/01/2017
    Consultar o nome dos tickers no site do Yahoo"""
    
    #Garantindo todos os tickers em maiusculo
    #tickers = [x.upper() for x in tickers] + ['USDBRL=X', '^BVSP']
    tickers = [x.upper() for x in tickers] + ['^BVSP']
    
    prices = pd.DataFrame()
    
    for i in tickers:
        if '^BVSP' in i:
            prices[i] = web.get_data_yahoo(i,dataInicio)['Adj Close']
        elif 'USDBRL=X' in i:
            prices[i] = web.get_data_yahoo(i,dataInicio)['Adj Close']
        elif '.SA' in i:
            prices[i] = web.get_data_yahoo(i,dataInicio)['Adj Close']
        else:
            i = i+'.SA'
            prices[i] = web.get_data_yahoo(i,dataInicio)['Adj Close']
    
    #arredondar os valores para 2 casas decimais
    prices = np.round(prices, decimals=2)
    
    if "^BVSP" in tickers:
        prices['^BVSP'] = prices['^BVSP']/1000
    
    #prices.rename(columns = {'USDBRL=X':'Dolar', '^BVSP':'Bovespa'}, inplace = True)
    prices.rename(columns = { '^BVSP':'Bovespa'}, inplace = True)

    prices = prices.dropna()
    
    return prices

def desvios(cotacao, start, end) -> list:
  
  cotacao.index = pd.to_datetime(cotacao.index)

  nomes = cotacao.columns

  # Converte em data 1º vencimento opção
  d1 = datetime.strptime(start, '%d/%m/%Y').date()

  # Converte em data 2º vencimento opção
  d2 = datetime.strptime(end, '%d/%m/%Y').date()

  # Obtém 1 dia útil 1 ano antes do valor de início
  d0 = d1 - timedelta(days=365)
  offset = pd.tseries.offsets.BusinessDay(n=1)
  res = (d0 - offset).date()

  dados = pd.DataFrame(index=['2DvP', '1,5Dvp', '1Dvp', '0,5Dvp', f'Preço Calculado na Data {d2}','-0,5Dvp', '-1Dvp', '-1,5Dvp', '-2Dvp' ])
  ind = pd.DataFrame(index=['Volatilidade Histórica', 'Volatilidade no Período', 'Retorno Diário', 
                            'Dias úteis Data Inicial a Data final', f'Preço Cotação na Data {d1}', f'Preço Calculado na Data {d2}', 'Data Início Leitura'])

  for nome in nomes:
    # Dias uteis entre as datas de vencimento das opções
    du = wd.networkdays(d1, d2, country='BR')

    # Volatilidade Histórica Anualizada
    sth = cotacao[f'{nome}'][res:d1].pct_change().mul(100).std()*(252**0.5)

    # Converte volatilidade histórica em dias uteis úteis entre vencimento opções
    st = sth/(du**0.5)
    
    # Calcula retorno acumulado no último ano:
    retorn = cotacao[f'{nome}'][res:d1].pct_change().mul(100)
    retorn_acumulado = (1 + retorn.div(100)).cumprod()
    retorn_acumulado.iloc[0] = 1
    retorn = np.round(retorn, decimals=4)
    retorn_acumulado = np.round(retorn_acumulado, decimals=2)
    ret = retorn_acumulado[-1]**(1/retorn.count())

    # Preço na data d1 (1º vencimento opção)
    p1 = cotacao[f'{nome}'][f'{d1}']
    
   
    # calcula o preço projetado na data final definida (2º vencimento opção)
    pf = cotacao[f'{nome}'][f'{d1}']*((ret)**du)
    dados[nome] = [pf*(2*st/100+ret), pf*(1.5*st/100+ret), pf*(st/100+ret),pf*(0.5*st/100+ret), pf,pf*(-0.5*st/100+ret),pf*(-st/100+ret),pf*(-1.5*st/100+ret),pf*(-2*st/100+ret)]
    ind[nome] = [sth, st, ret, du, p1, pf, res]
  
  return dados, ind

#### fim ####
pd.set_option('display.float_format', '{:.2f}'.format)

df_cotacao = cotacoes_acoes(acao_escolhida, dataInicio)
df_cotacao.index = df_cotacao.index.strftime('%d/%m/%Y')
st.subheader('Tabela de valores - Preço das ações')
st.write(df_cotacao.tail(30))

df_desvios = desvios(df_cotacao, data1, data2)
st.subheader('Tabela de valores - Análise Desvios')
st.write(df_desvios[0])

fig, ax = plt.subplots()
sns.heatmap(df_desvios[0].corr(), ax=ax, annot = True)
st.write(fig)