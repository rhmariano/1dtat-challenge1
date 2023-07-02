## Libraries
import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker


st.set_page_config(layout='wide')

## Functions
def format_number(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor<1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

## Title
st.title('Dashboard Exportações 🍷 ')

## Data
df = pd.read_csv('./data/ExpVinho.csv',sep=';')

pattern = r'\d{4}\.1'
def rename_columns(column_name):
    if re.match(pattern, column_name):
        return column_name.replace('.1','_value')
    else:
        return column_name

# renaming the year.1 to year_value
df = df.rename(columns=rename_columns)


pattern = r'^(\d{4})$'
def rename_columns(column_name):
    if re.match(pattern, column_name):
        return column_name.replace(column_name,column_name + '_liters')
    else:
        return column_name

# renaming the year to year_liters
df = df.rename(columns=rename_columns)

df_temp = df
dict_normalized = {
    'country_origin' : [],
    'country_destination' : [],
    'year' : [],
    'liters' : [],
    'value' : []
}

def normalize_table(row):
    country_origin = 'Brasil'
    country_destination,current_year,current_liters,current_value = [None] * 4
    for column_name, value in row.items():
        if(column_name == 'País' and country_destination is None):
            country_destination = value
            continue
        if('_' in column_name):
            year,datatype = column_name.split('_')
            if(current_year != year):
                current_liters, current_value = [None] * 2
                current_year = year
            if('value' == datatype):
                current_value = value
            elif('liters' == datatype):
                current_liters = value
            if(current_liters is not None and current_value is not None):
                dict_normalized['country_origin'].append(country_origin)
                dict_normalized['country_destination'].append(country_destination)
                dict_normalized['year'].append(current_year)
                dict_normalized['liters'].append(current_liters)
                dict_normalized['value'].append(current_value)

df_temp.apply(lambda x:normalize_table(x),axis=1)
df_normalized = pd.DataFrame(dict_normalized)


df_normalized['year'] = df_normalized['year'].astype(str)
df_normalized['date_string'] = df_normalized['year'] + '-01-01'
df_normalized['date'] = pd.to_datetime(df_normalized['date_string'])

# Filtering 2021 
df_2021 = df_normalized[df_normalized['year'] == '2021']

# Filtering Last 15 years
df_wine_last_15_year = df_normalized[df_normalized['date'] > '2007-01-01']

# Removing countries that didn't buy in the last 15y 
df_total_liters_per_country = df_wine_last_15_year[['country_destination','liters']].groupby('country_destination').sum()

# creating list of countries that sold
list_did_not_buy_last_15y = []
list_did_not_buy_last_15y = df_total_liters_per_country[df_total_liters_per_country['liters'] == 0].index.values.tolist()

# removing countries that did not buy wine last 15 years
df_wine_last_15_year = df_wine_last_15_year.drop(df_wine_last_15_year[df_wine_last_15_year['country_destination'].isin(list_did_not_buy_last_15y)].index)
df_wine_last_15_year['price_per_liter'] = ((df_wine_last_15_year['value']/df_wine_last_15_year['liters']).round(2)).fillna(0)


df_2021_data = df_wine_last_15_year[df_wine_last_15_year['year'] == '2021']
df_2021_data = df_2021_data.sort_values('value', ascending=False)

df_21_sum = df_2021_data['value'].sum()
df_21_liters = df_2021_data['liters'].sum()


aba1, aba2, aba3 = st.tabs(['Dashboard Últimos 15 anos', 'Dashboard 2021', 'Sobre'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total Exportações (USD) 2007-2021', format_number(df_wine_last_15_year['value'].sum(), 'USD'))
       

        # Line chart: Total value per year
        st.subheader('Total Exportações (2007-2021)')

        df_wine_last_15_year['year'] = pd.to_numeric(df_wine_last_15_year['year'])

        plt.figure(figsize=(10, 6))
        ax = sns.lineplot(x='year', y='value', data=df_wine_last_15_year, estimator=sum, errorbar=None, color='#800020')
        plt.ylabel('Total USD')
        plt.xlabel('Ano')
        plt.xticks(range(2007, 2022, 1), rotation=90, ha='right')
        ax.ticklabel_format(style='plain')
        sns.despine(right=True, top=True)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M'))

        top_3 = df_wine_last_15_year.nlargest(3, 'value')
        for _, row in top_3.iterrows():
            plt.annotate(f'{row["value"]/1e6:.1f}M', xy=(row['year'], row['value']), xytext=(0, 80), textcoords='offset points', ha='center', va='bottom')
        st.pyplot(plt)

    with coluna2:
        st.metric('Total Exportações (L) 2007-2021', format_number(df_wine_last_15_year['liters'].sum()))
       
        st.subheader('Variação de Preços (2007-2021)')
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=df_wine_last_15_year, x="year", y="price_per_liter", marker='o', ax=ax, color='#800020')
        plt.xticks(range(2007, 2022, 1), rotation=90, ha='right')
        plt.ylabel('Preço (USD x Liter)')
        plt.xlabel('Ano')
        plt.title('Variação de Preços ao Longo dos Anos')
        sns.despine(right=True, top=True)
        st.pyplot(fig)



    # Bar: Top 5 countries LTD
    st.subheader('Top 5 Destinos (2007-2021)')
    top_countries = df_wine_last_15_year.groupby('country_destination')['value'].sum().nlargest(5) / 1e6 # Convertendo para milhões

    custom_palette = ['#7C1938', '#9B2E4A', '#BA436C', '#D95E8F', '#F37AB2']
    plt.figure(figsize=(8, 6))
    sns.barplot(x=top_countries.values, y=top_countries.index, palette=custom_palette)
    plt.xlabel('Soma dos Valores (em milhões de USD)')
    plt.ylabel('Destino')
    sns.despine(right=True, top=True)

    for i, value in enumerate(top_countries):
        plt.text(value, i, f'USD {value:.2f} mi', va='center')

    st.pyplot(plt)

with aba2:
    st.subheader('Tendências do mercado brasileiro de vinhos')

    df = pd.DataFrame(
    {
        "col1": ["Aumento do consumo dos sucos de uva;", "Crescimento da demanda interna de vinhos;", "Aumento dos custos de produção;", "Desvalorização do Real"],
        "col2": ["Patamar elevado das importações de vinhos;", "Preços competitivos dos vinhos importados;","Aumento da produção mundial de vinhos em 2018.", "desfavorável às importações."],
    }
    )
    st.dataframe(
        df,
        column_config={
            "col1": "FATORES DE ALTA DOS PREÇOS",
            "col2": "FATORES DE BAIXA DOS PREÇOS",
        },
        hide_index=True,
    )

    st.divider()


    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('2021 (USD)', format_number(df_21_sum, 'USD'))

    with coluna2:
        st.metric('2021 (L)', format_number(df_21_liters))

    # Bar: Top 5 countries 2021
    st.subheader('Top 5 Destinos (2021)')
    top_countries2021 = df_2021_data.groupby('country_destination')['value'].sum().nlargest(5) / 1e6 # Convertendo para milhões

    custom_palette2 = ['#7C1938', '#9B2E4A', '#BA436C', '#D95E8F', '#F37AB2']
    plt.figure(figsize=(8, 6))
    sns.barplot(x=top_countries2021.values, y=top_countries2021.index, palette=custom_palette2)
    plt.xlabel('Soma dos Valores (em milhões de USD)')
    plt.ylabel('Destino')
    sns.despine(right=True, top=True)

    for i, value in enumerate(top_countries2021):
        plt.text(value, i, f'USD {value:.2f} mi', va='center')

    st.pyplot(plt)    

with aba3:
    st.subheader('Grupo 53')
    st.subheader('Participantes:')
    st.caption('''
    - Gustavo Rodrigues
    - Rafael H Mariano
    - Renê B L de Salles
    ''')

    st.divider()
    st.subheader('Referências:')
    st.caption('''
    🍷 Wine and Health: A Review
    (https://www.ajevonline.org/content/ajev/62/4/471.full.pdf)
    
    🍷 Dados da Vitivinicultura: Banco de dados de uva, vinho e derivados
    (http://vitibrasil.cnpuv.embrapa.br/)

    🍷 International Organisation of Vine and Wine
    (https://www.oiv.int/)

    🍷 Análise Uva Industrial - Conab 
    ([https://www.conab.gov.br](https://www.conab.gov.br/info-agro/analises-do-mercado-agropecuario-e-extrativista/analises-do-mercado/historico-mensal-de-uva/item/download/28637_368368b143e5af72831076dc5c06ecbb))

    ''')
    
