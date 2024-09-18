import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import seaborn as sns
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import matplotlib.pyplot as plt

# Load the CSV file
df = pd.read_csv('tickets.csv')

# Convert date columns to datetime with dayfirst=True
df['date_created'] = pd.to_datetime(df['date_created'], dayfirst=True)
df['date_action'] = pd.to_datetime(df['date_action'], dayfirst=True)

# Calculate resolution time in hours
df['resolution_time'] = (df['date_action'] - df['date_created']).dt.total_seconds() / 3600

# Extract unique years from `date_created` and `date_action`
years_created = df['date_created'].dt.year.unique()
years_action = df['date_action'].dt.year.unique()

# Fields available for analysis
fields = {
    'dprt': 'Department',
    'post': 'Jawatan',
    'env': 'Persekitaran',
    'report_type': 'Jenis Kategori Laporan',
    'hw_type': 'Jenis Perkaksasan',
    'apps_sw': 'Perisian/Aplikasi',
    'act_stat': 'Status Tindakan',
    'resolution_time': 'Resolution Time',
    'taken_by': 'Tindakan Oleh'
}

# Fields for correlation matrix
correlation_fields = ['dprt', 'post', 'env', 'report_type', 'hw_type', 'apps_sw', 'act_stat', 'taken_by']

# Available chart types
chart_types = ['bar', 'pie', 'line', 'box', 'histogram']

# Initialize the Dash app
app = Dash(__name__)

# Apply external stylesheets for Bootstrap and custom styling
app.css.append_css({'external_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'})

# Layout for the Dashboard
app.layout = html.Div([
    html.Div([
        html.H1('Dashboard Analisa', className='text-center text-white p-3 bg-dark mb-4'),

        # Dropdown for selecting a field to analyze
        html.Div([
            html.Label('Pilih Medan Analisa:', className='form-label'),
            dcc.Dropdown(
                id='field-dropdown',
                options=[{'label': name, 'value': field} for field, name in fields.items()],
                value='report_type',
                className='form-select'
            )
        ], className='mb-3'),

        # Dropdown for filtering by year of date_created
        html.Div([
            html.Label('Pilih Tahun (Date Created):', className='form-label'),
            dcc.Dropdown(
                id='year-dropdown-created',
                options=[{'label': str(year), 'value': year} for year in sorted(years_created)],
                value=None,
                className='form-select',
                placeholder="Semua Tahun"
            )
        ], className='mb-3'),

        # Dropdown for filtering by year of date_action
        html.Div([
            html.Label('Pilih Tahun (Date Action):', className='form-label'),
            dcc.Dropdown(
                id='year-dropdown-action',
                options=[{'label': str(year), 'value': year} for year in sorted(years_action)],
                value=None,
                className='form-select',
                placeholder="Semua Tahun"
            )
        ], className='mb-3'),

        # Radio items for selecting chart type
        html.Div([
            html.Label('Pilih Jenis Carta:', className='form-label'),
            dcc.RadioItems(
                id='chart-type-radio',
                options=[{'label': chart.capitalize(), 'value': chart} for chart in chart_types],
                value='bar',
                labelStyle={'display': 'inline-block', 'margin-right': '15px'},
                className='form-check form-check-inline'
            )
        ], className='mb-4'),

        # Hidden dropdown for histogram comparison fields (multiple)
        html.Div([
            html.Label('Pilih Medan Perbandingan untuk Histogram:', className='form-label'),
            dcc.Dropdown(
                id='comparison-dropdown',
                options=[{'label': name, 'value': field} for field, name in fields.items()],
                multi=True,
                className='form-select'
            )
        ], id='comparison-field-container', style={'display': 'none'}),

        # Output graph for field analysis
        dcc.Graph(id='analysis-graph', className='mb-4'),

        # Resolution time analysis
        html.H2('Analisis Masa Penyelesaian', className='mt-5 text-center text-secondary'),
        dcc.Graph(id='resolution-time-graph', className='mb-4'),

        # Monthly trend analysis
        html.H2('Analisis Trend Bulanan', className='text-center text-secondary'),
        dcc.Graph(id='monthly-trend-graph', className='mb-4'),

        # Correlation matrix
        html.H2('Matriks Korelasi', className='text-center text-secondary'),
        html.Div([
            dcc.Dropdown(
                id='correlation-dropdown',
                options=[{'label': name, 'value': field} for field, name in fields.items() if
                         field in correlation_fields],
                value=correlation_fields,
                multi=True,
                className='form-select'
            )
        ], className='mb-4'),
        dcc.Graph(id='correlation-matrix', className='mb-4'),

        # Regression analysis
        html.H2('Analisis Regresi', className='text-center text-secondary'),
        dcc.Graph(id='regression-scatter', className='mb-4'),
        html.Div(id='regression-summary', className='alert alert-info')
    ], className='container mt-5')
], className='bg-light')


# Filter data by year
def filter_by_year(df, year_created, year_action):
    filtered_df = df.copy()
    if year_created:
        filtered_df = filtered_df[filtered_df['date_created'].dt.year == year_created]
    if year_action:
        filtered_df = filtered_df[filtered_df['date_action'].dt.year == year_action]
    return filtered_df


# Show/hide the comparison dropdown based on chart type
@app.callback(
    Output('comparison-field-container', 'style'),
    [Input('chart-type-radio', 'value')]
)
def toggle_comparison_dropdown(selected_chart_type):
    if selected_chart_type == 'histogram':
        return {'display': 'block'}
    return {'display': 'none'}


# Update the analysis graph based on the selected field, chart type, and year
@app.callback(
    Output('analysis-graph', 'figure'),
    [Input('field-dropdown', 'value'), Input('chart-type-radio', 'value'), Input('year-dropdown-created', 'value'),
     Input('year-dropdown-action', 'value'), Input('comparison-dropdown', 'value')]
)
def update_graph(selected_field, selected_chart_type, year_created, year_action, comparison_fields):
    filtered_df = filter_by_year(df, year_created, year_action)
    grouped_data = filtered_df.groupby(selected_field).size().reset_index(name='count')

    if selected_chart_type == 'bar':
        fig = px.bar(grouped_data, x=selected_field, y='count', title=f'{fields[selected_field]} Analysis - Bar Chart')
    elif selected_chart_type == 'pie':
        fig = px.pie(grouped_data, names=selected_field, values='count',
                     title=f'{fields[selected_field]} Analysis - Pie Chart')
    elif selected_chart_type == 'line':
        fig = px.line(grouped_data, x=selected_field, y='count',
                      title=f'{fields[selected_field]} Analysis - Line Chart')
    elif selected_chart_type == 'box':
        fig = px.box(filtered_df, x=selected_field, y='resolution_time',
                     title=f'{fields[selected_field]} Resolution Time Analysis - Box Plot')
    elif selected_chart_type == 'histogram':
        # Use both selected field and comparison fields for the histogram if provided
        if comparison_fields:
            fig = px.histogram(filtered_df, x=selected_field, color=comparison_fields[0], barmode='overlay',
                               title=f'{fields[selected_field]} vs {", ".join([fields[comp] for comp in comparison_fields])} - Histogram')
        else:
            fig = px.histogram(filtered_df, x=selected_field, title=f'{fields[selected_field]} Analysis - Histogram')

    return fig


# Update the resolution time graph based on the selected year
@app.callback(
    Output('resolution-time-graph', 'figure'),
    [Input('field-dropdown', 'value'), Input('year-dropdown-created', 'value'), Input('year-dropdown-action', 'value')]
)
def update_resolution_time_graph(selected_field, year_created, year_action):
    filtered_df = filter_by_year(df, year_created, year_action)
    fig = px.box(filtered_df, x=selected_field, y='resolution_time',
                 title=f'Resolution Time Distribution by {fields[selected_field]}')
    return fig


# Update the monthly trend graph based on the selected field and year
@app.callback(
    Output('monthly-trend-graph', 'figure'),
    [Input('field-dropdown', 'value'), Input('year-dropdown-created', 'value'), Input('year-dropdown-action', 'value')]
)
def update_monthly_trend_graph(selected_field, year_created, year_action):
    filtered_df = filter_by_year(df, year_created, year_action)
    filtered_df['month'] = filtered_df['date_created'].dt.to_period('M').astype(str)
    monthly_data = filtered_df.groupby('month').agg({'ticket_no': 'count', 'resolution_time': 'mean'}).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly_data['month'], y=monthly_data['ticket_no'], name='Ticket Count', yaxis='y'))
    fig.add_trace(
        go.Scatter(x=monthly_data['month'], y=monthly_data['resolution_time'], name='Avg Resolution Time', yaxis='y2'))

    fig.update_layout(
        title='Monthly Trend: Ticket Count and Average Resolution Time',
        xaxis=dict(title='Month'),
        yaxis=dict(title='Ticket Count', side='left'),
        yaxis2=dict(title='Avg Resolution Time (hours)', side='right', overlaying='y'),
        legend=dict(x=0.1, y=1.1, orientation='h')
    )
    return fig

    # Update the correlation matrix based on the selected fields and year


@app.callback(
    Output('correlation-matrix', 'figure'),
    [Input('correlation-dropdown', 'value'), Input('year-dropdown-created', 'value'),
     Input('year-dropdown-action', 'value')]
)
def update_correlation_matrix(selected_fields, year_created, year_action):
    filtered_df = filter_by_year(df, year_created, year_action)

    # Create correlation matrix only for the selected fields
    corr_matrix = pd.get_dummies(filtered_df[selected_fields]).corr()

    # Create heatmap for correlation matrix
    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", title='Correlation Matrix')
    return fig


# Regression analysis callback based on the selected field and year
@app.callback(
    [Output('regression-scatter', 'figure'), Output('regression-summary', 'children')],
    [Input('field-dropdown', 'value'), Input('year-dropdown-created', 'value'), Input('year-dropdown-action', 'value')]
)
def perform_regression(selected_field, year_created, year_action):
    filtered_df = filter_by_year(df, year_created, year_action)

    X = filtered_df[['resolution_time']]
    y = filtered_df[selected_field]

    if y.dtype == 'object':
        y = pd.Categorical(y).codes

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    coefficients = model.coef_
    intercept = model.intercept_
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    fig = px.scatter(x=y_test, y=y_pred, labels={'x': 'Actual', 'y': 'Predicted'}, title='Regression Analysis')
    fig.add_shape(type='line', x0=y_test.min(), y0=y_test.min(), x1=y_test.max(), y1=y_test.max(),
                  line=dict(color='Red', dash='dash'))

    summary = f"""
        Intercept: {intercept}
        Coefficients: {coefficients}
        Mean Squared Error: {mse}
        R^2 Score: {r2}
        """

    return fig, summary


if __name__ == '__main__':
    app.run_server(debug=True)
