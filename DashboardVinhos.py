## Bibliotecas
import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

## Funcoes
def format_number(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor<1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

## Titulo
st.title('Dashboard Exportações 🍷 ')


## Dados
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

# Filtrando dados de 2021
df_2021 = df_normalized[df_normalized['year'] == '2021']

# Calculando o total de exportações em 2021
total_exportacoes_2021 = df_2021['value'].sum()
total_liters_2021 = df_2021['liters'].sum()



coluna1, coluna2 = st.columns(2)
with coluna1:
    st.metric('Total Exportações (R$)', format_number(df_normalized['value'].sum(), 'R$'))
    st.metric('2021 (R$)', format_number(total_exportacoes_2021))

with coluna2:
    st.metric('Total Exportações (L)', format_number(df_normalized['liters'].sum()))
    st.metric('2021 (L)', format_number(total_liters_2021))
# Gráfico de linha: Total de value por ano
st.subheader('Total Exportações')

# Convertendo a coluna 'year' em valores numéricos
df_normalized['year'] = pd.to_numeric(df_normalized['year'])

plt.figure(figsize=(10, 6))
ax = sns.lineplot(x='year', y='value', data=df_normalized, estimator=sum, ci=None, color='#800020')
plt.xlabel('Ano')
plt.ylabel('Total Value')
plt.xticks(range(1970, 2022, 5), rotation=45, ha='right')

# Removendo a notação científica (1e7) acima do gráfico
ax.ticklabel_format(style='plain')

# Removendo as bordas direita e superior do gráfico
sns.despine(right=True, top=True)

# Alterando a escala do eixo y para milhões (M)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M'))

# Adicionando anotações apenas para os 3 maiores pontos
top_3 = df_normalized.nlargest(3, 'value')
for _, row in top_3.iterrows():
    plt.annotate(f'{row["value"]/1e6:.1f}M', xy=(row['year'], row['value']), xytext=(0, 80),
                 textcoords='offset points', ha='center', va='bottom')

st.pyplot(plt)



# Gráfico de barras: Soma dos valores por destino de país (Top 5)
st.subheader('Top 5 Destinos')
top_countries = df_normalized.groupby('country_destination')['value'].sum().nlargest(5) / 1e6  # Convertendo para milhões

# Criando uma paleta de cores personalizada em tons de vinho
custom_palette = ['#7C1938', '#9B2E4A', '#BA436C', '#D95E8F', '#F37AB2']

plt.figure(figsize=(8, 6))
sns.barplot(x=top_countries.values, y=top_countries.index, palette=custom_palette)
plt.xlabel('Soma dos Valores (em milhões de R$)')
plt.ylabel('Destino de País')

# Adicionando valores das séries próximos das barras
for i, value in enumerate(top_countries):
    plt.text(value, i, f'R$ {value:.2f} mi', va='center')

# Removendo borda direita e superior do gráfico
sns.despine(right=True, top=True)

st.pyplot(plt)
