import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import numpy as np
import requests
from dash.dependencies import Output, Input, State
from bs4 import BeautifulSoup
import plotly.graph_objs as go
from worldometer import Worldometer
import worldometer
from dash import dash_table
import plotly.subplots as sp


app = dash.Dash(__name__)
server = app.server
w = Worldometer()

pop = worldometer.current_world_population()["current_world_population"]
all_matrics = w.metrics_with_labels()



metric_df = pd.DataFrame(list(all_matrics.items()), columns=['Metrics', 'Value'])

################################
# BAR Chart
################################
# Generate top 20 countries data
url = 'https://www.worldometers.info/world-population/population-by-country/'
response = requests.get(url)
html_content = response.content

soup = BeautifulSoup(html_content, 'html.parser')
table = soup.find('table', {'id': 'example2'})
rows = table.find_all('tr')[1:]

countries = []
populations = []

for row in rows[:20]:
    data = row.find_all('td')
    country = data[1].text.strip()
    population = int(data[2].text.strip().replace(',', ''))
    countries.append(country)
    populations.append(population)


top_countries= dict()
for i in range(20):
    top_countries[countries[i]] = populations[i]
bar_data = pd.DataFrame(list(top_countries.items()), columns=['Country', 'population'])
bar_fig = px.bar(bar_data, x='Country', y='population')
bar_fig.update_layout(template="plotly_dark")

################################
# Scatter plot
################################
df = pd.read_html('https://www.worldometers.info/world-population/population-by-country/')[0]
country_col = df['Country (or dependency)']
migrants_col = df['Migrants (net)']
population_col = df['Population (2020)']

colors = ['red' if x < 0 else 'green' for x in migrants_col]
data = list(zip(country_col, migrants_col, population_col))
data_sorted = sorted(data, key=lambda x: x[2], reverse=True)
country_sorted, migrants_sorted, population_sorted = zip(*data_sorted)

scatter = go.Scatter(x=country_sorted, y=migrants_sorted, mode='markers', 
                     marker=dict(size=10, color=colors))

layout = go.Layout(yaxis=dict(title='Net Migration'))
scatter_fig = go.Figure(data=[scatter], layout=layout)
scatter_fig.update_layout(template="plotly_dark")

################################
# Pie chart
################################
# Data preprocessing
df['World Share'] = df['World Share'].str.rstrip('%').astype(float) / 100.0
df['Urban Pop %'] = pd.to_numeric(df['Urban Pop %'].str.rstrip('%'), errors='coerce').fillna(0)
df = df.sort_values(by='World Share', ascending=False).head(10)

# Create two pie charts
pie_fig = sp.make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]])

pie_fig.add_trace(go.Pie(values=df['World Share'], labels=df['Country (or dependency)'],title="Overall population share",
                     hovertemplate='<b>%{label}</b><br>World Share: %{value:.2%}<br>Population: %{customdata}<extra></extra>',
                     customdata=df['Population (2020)']), 1, 1)

df = df.sort_values(by='Urban Pop %', ascending=False).head(10)

pie_fig.add_trace(go.Pie(values=df['Urban Pop %'], labels=df['Country (or dependency)'],title="Urban population precentage",
                     hovertemplate='<b>%{label}</b><br>Urban Pop %: %{value:.2%}<br>Population: %{customdata}<extra></extra>',
                     customdata=df['Population (2020)']), 1, 2)

# Update the layout
pie_fig.update_layout(template="plotly_dark")



# Define the layout
app.layout = html.Div(children=[
    html.H1('Population Data visualization'),
    dcc.RadioItems(
        id='theme-selector',
        options=[
            {'label': 'Light', 'value': 'light'},
            {'label': 'Dark', 'value': 'dark'}
        ],
        value='light',
        labelStyle={'display': 'inline-block'}
    ),
    html.Hr(),
    html.Center(children=[
    html.H2("World population some basic information"),
    html.P("In the following table the Metrics and values shows real time data with current world updates"),
	html.Div([
        dash_table.DataTable(
            id='table',
            columns=[{'name': i, 'id': i} for i in metric_df.columns],
            data=metric_df.head(5).to_dict('records'),
            style_header={
                'backgroundColor': 'deepskyblue',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'left',
                'backgroundColor': 'lightblue'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                }
            ]
        )
    ],
    style={
        'margin': '50px',
        'padding': '20px',
        'border': 'thin lightgrey solid',
        "width":"60%"
    })]),
	html.Hr(),

	html.Center(children=[
    html.Div([
        html.H2("Population of world in top 20 countries"),
        html.P("X axis in the following figure shows country names and y axis shows Total population",
        	style={"width":"60%"}),
        html.Hr(style={"width":"60%"}),
        html.Div([
            dcc.Graph(id='bar-plot', figure=bar_fig)
        ], className='two columns', style={'text-align': 'center'}),
        html.Hr(),
        html.H2("Scatter plot to show migrants from different countries"),
        html.P("Green points in the sccatter plot shows incomming migrants to country\nwhile the red color sccatter points represents those who left particular country",
        	style={"width":"60%"}),
        html.Hr(style={"width":"60%"}),
        html.Div([
            dcc.Graph(id='scatter-plot', figure=scatter_fig)
        ], className='two columns', style={'text-align': 'center', "backgroundColor":"red"})
    ], className='row',style={"width":"80%"}),
    ]),



    html.Hr(),
    html.Center(children=[
    html.Div([
        html.H2("Pie chart diagram"),
        html.P("The pie chart diagram on the left shows the percentage population share of specific country in the whole world and the pie chart diagram on the right shows each countries which have higher population precentage of urban life",
        	style={"width":"60%"}),
        html.Div([
        	dcc.Graph(id='pie-chart', figure=pie_fig)
        ], className='two columns', style={'text-align': 'center'})
    ], className='row'),
    ]),

],id="graph_main", style={
        'color': 'black',
        'backgroundColor': 'white'
    },
)

# Define the callback function to update the figure color scheme
@app.callback(
    [dash.dependencies.Output('graph_main', 'style'),
     dash.dependencies.Output('bar-plot', 'figure'),
     dash.dependencies.Output('scatter-plot', 'figure'),
     dash.dependencies.Output('pie-chart', 'figure')],
    [dash.dependencies.Input('theme-selector', 'value')]
)
def update_figure_theme(theme):
    if theme == 'light':
        style={"color":"black",
        "backgroundColor":"white"}
        color_scheme = 'plotly_white'
    else:
        style={"color":"white",
       	"backgroundColor":"black"}
        color_scheme = 'plotly_dark'
    
    
    bar_fig.update_layout(template=color_scheme)
    
    
    scatter_fig.update_layout(template=color_scheme)
    
    pie_fig.update_layout(template=color_scheme)

    #style_cell={'backgroundColor': 'cadetblue',}
    
    return style,bar_fig, scatter_fig, pie_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
