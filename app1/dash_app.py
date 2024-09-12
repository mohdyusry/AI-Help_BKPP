from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from django_plotly_dash import DjangoDash  # Use DjangoPlotlyDash instead of Dash
from app1.models import Ticket
from django.db.models import Count

from django_plotly_dash import DjangoDash

# Correct app name should match what is used in the template
app = DjangoDash('AdminDashboard')

# Fields available for analysis
fields = {
    'dprt': 'Department',
    'post': 'Post',
    'env': 'Environment',
    'report_type': 'Report Type',
    'hw_type': 'Hardware Type',
    'apps_sw': 'Software/Application',
    'act_stat': 'Action Status',
    'date_created': 'Date Created',
    'date_action': 'Date of Action',
    'taken_by': 'Taken By'
}

# Available chart types
chart_types = ['bar', 'pie', 'line']

# Layout for Dash
app.layout = html.Div([
    html.H1('Admin Dashboard Analysis'),

    # Dropdown for selecting a field to analyze
    html.Label('Select a field for analysis:'),
    dcc.Dropdown(
        id='field-dropdown',
        options=[{'label': name, 'value': field} for field, name in fields.items()],
        value='dprt'  # Default field
    ),

    # Radio items for selecting chart type
    html.Label('Select chart type:'),
    dcc.RadioItems(
        id='chart-type-radio',
        options=[{'label': chart.capitalize(), 'value': chart} for chart in chart_types],
        value='bar',  # Default chart type
        labelStyle={'display': 'inline-block'}
    ),

    # Output graph
    dcc.Graph(id='analysis-graph')
])

# Callback to update the graph based on selected field and chart type
@app.callback(
    Output('analysis-graph', 'figure'),
    [Input('field-dropdown', 'value'), Input('chart-type-radio', 'value')]
)
def update_graph(selected_field, selected_chart_type):
    # Fetch data from the database based on the selected field
    ticket_data = Ticket.objects.values(selected_field).annotate(count=Count('id'))

    # Prepare data for Plotly based on chart type
    if selected_chart_type == 'bar':
        fig = px.bar(
            x=[t[selected_field] for t in ticket_data],
            y=[t['count'] for t in ticket_data],
            title=f'{fields[selected_field]} Analysis - Bar Chart'
        )
    elif selected_chart_type == 'pie':
        fig = px.pie(
            names=[t[selected_field] for t in ticket_data],
            values=[t['count'] for t in ticket_data],
            title=f'{fields[selected_field]} Analysis - Pie Chart'
        )
    elif selected_chart_type == 'line':
        fig = px.line(
            x=[t[selected_field] for t in ticket_data],
            y=[t['count'] for t in ticket_data],
            title=f'{fields[selected_field]} Analysis - Line Chart'
        )

    return fig
