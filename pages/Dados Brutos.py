## Bibliotecas

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import re

## Titulo
st.title('Dados Brutos')
st.header('Exportação de Vinhos - 1970 a 2021 🍷')

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

# Filtering 2021 
df_2021 = df_normalized[df_normalized['year'] == '2021']

# Filtering Last 15 years
df_wine_last_15_year = df_normalized[df_normalized['date'] >= '2007-01-01']

# Removing countries that didn't buy in the last 15y 
df_total_liters_per_country = df_wine_last_15_year[['country_destination','liters']].groupby('country_destination').sum()

# creating list of countries that sold
list_did_not_buy_last_15y = []
list_did_not_buy_last_15y = df_total_liters_per_country[df_total_liters_per_country['liters'] == 0].index.values.tolist()

# removing countries that did not buy wine last 15 years
df_wine_last_15_year = df_wine_last_15_year.drop(df_wine_last_15_year[df_wine_last_15_year['country_destination'].isin(list_did_not_buy_last_15y)].index)
df_wine_last_15_year['price_per_liter'] = ((df_wine_last_15_year['value']/df_wine_last_15_year['liters']).round(2)).fillna(0)


st.write(df_normalized)
st.divider()

st.header('Exportação de Vinhos - 2007 a 2021 🍷')
st.write(df_wine_last_15_year)

# style
# th_props = [
#   ('font-size', '16px'),
#   ('text-align', 'center'),
#   ('font-weight', 'bold'),
#   ('color', '#6d6d6d'),
#   ('background-color', '#EAE5E5')
#   ]
                               
# td_props = [
#   ('font-size', '14px')
#   ]
                                 
# styles = [
#   dict(selector="th", props=th_props),
#   dict(selector="td", props=td_props)
#   ]

# # table
# df2=df_normalized.style.set_properties(**{'text-align': 'left'}).set_table_styles(styles)
# st.table(df2)
