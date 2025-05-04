import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from math import pi
import os

def get_dropdown_style(width="60%", margin="auto"):
    return {
        'width': width,
        'margin': margin,
        'color': 'black'
    }

def get_card_style(theme_value):
    dark_mode=theme_value
    return {
        'backgroundColor': '#000' if dark_mode else '#fff',
        'borderRadius': '15px',
        'boxShadow': '0 4px 8px rgba(0,0,0,0.2)' if dark_mode else '0 2px 5px rgba(0,0,0,0.1)',
        'padding': '20px',
        'margin': '15px',
        'flex': '1 1 300px',
        'minWidth': '280px',
        'color': 'white' if dark_mode else 'black',
        'transition': 'background-color 0.3s ease'
    }

# Load data
df_avg = pd.read_csv('./CSV/firm-averages.csv')
df_empat = pd.read_csv('./CSV/firm_empat_profile.csv')
#df_reviews = pd.read_csv('./CSV/df_reviews.csv')
df_yearly_ratings = pd.read_csv('./CSV/yearly_ratings.csv')
df_empat_time = pd.read_csv('./CSV/empat_time_series.csv')
df_topic_trends = pd.read_csv('./CSV/topic_trends.csv')
df_profile_fit = pd.read_csv('./CSV/profile_fit.csv')
df_empat_sentiment = pd.read_csv('./CSV/empat_sentdistrib.csv')
df_cooccurrence = pd.read_csv('./CSV/cooccurrence_network.csv')
df_neglect = pd.read_csv('./CSV/neglect_index.csv')

#Download df_reviews from Drive
file_id = '142TTxN-Se3Jc7_HdqAhAafwgeowQJ-yz'
gdrive_url = f'https://drive.google.com/uc?id={file_id}'
local_path = 'df_reviews.csv'
if not os.path.exists(local_path):
    try:
        import gdown
    except ImportError:
        import subprocess
        subprocess.check_call(['pip', 'install', 'gdown'])
        import gdown
    gdown.download(gdrive_url, local_path, quiet=False)
df_reviews = pd.read_csv(local_path)

firms = df_reviews['firm'].unique()

#Start dashboard
dashboard = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.themes.DARKLY])
server = dashboard.server
dashboard.title = "Glassdoor Insights Dashboard"

theme_toggle = html.Div([
    dbc.Label("Dark Mode", html_for='dark-mode-toggle', style={'marginRight': '10px', 'marginTop': '5px'}),
    dbc.Switch(id='dark-mode-toggle', value=False, persistence=True, persistence_type='local')
], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '20px', 'backgroundColor': 'transparent', 'boxShadow': 'none',
    'border': 'none' })

nav_links = html.Div([
    html.Div([
        html.A("Overview Panel", href="/", style={'marginRight': '20px'}),
        html.A("EmpAt Profile Panel", href="/empat", style={'marginRight': '20px'}),
        html.A("Temporal Trends Panel", href="/temporal", style={'marginRight': '20px'}),
    ], style={'textAlign': 'center', 'marginTop': '10px', 'marginBottom': '20px'}),
])

def overview_layout(theme_value):
    dark_mode=theme_value
    return html.Div([ 
        nav_links,
        html.H1("Overview Panel: Company Insights", style={'textAlign': 'center'}),

        html.Div([
            dcc.Dropdown(
                id='firm-dropdown',
                options=[{'label': firm, 'value': firm} for firm in firms],
                value=firms[0],
                clearable=False
            )
        ], id='firm-dropdown-container', style={'width': '60%', 'margin': 'auto'}),

        html.Div([
            html.Div(dcc.Graph(id='bar-chart'), style=get_card_style(dark_mode)),
            html.Div(dcc.Graph(id='radar-chart'), style=get_card_style(dark_mode))
        ], style={'display': 'flex', 'flexWrap': 'wrap'}),

        html.Div([
            html.H3("Top Review Phrases (Pros & Cons)"),
            html.Div([
                html.Div(dcc.Graph(id='pros-worddonut'), style=get_card_style(dark_mode)),
                html.Div(dcc.Graph(id='cons-worddonut'), style=get_card_style(dark_mode))
            ], style={'display': 'flex', 'justifyContent': 'space-between'})
        ], style={'marginTop': '40px'})

    ])

def temporal_layout(theme_value):
    dark_mode=theme_value
    return html.Div([
        nav_links,
        html.H1("Temporal Trends Panel", style={'textAlign': 'center'}),

        html.Div([
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id='ratings-firm-dropdown',
                        options=[{'label': firm, 'value': firm} for firm in firms],
                        value=firms[0],
                        clearable=False,
                        style={'width': '60%', 'margin': '0 auto 30px'}
                    ),
                    dcc.Graph(id='ratings-time-series')
                ])
            ], style={**get_card_style(dark_mode), 'flex': '1 1 500px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

        html.Div([
            html.Div(dcc.Graph(id='empat-time-series'),style=get_card_style(dark_mode)),
            html.Div(dcc.Graph(id='topic-trends'),style=get_card_style(dark_mode))
        ], )
    ])

def empat_layout(theme_value):
    dark_mode=theme_value
    return html.Div([
        nav_links,
        html.H1("EmpAT Profile Panel", style={'textAlign': 'center'}),

        #Dropdown to select empat category + Profile Fit Bar
        html.Div([ 
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        options=[{'label': cat, 'value': f'{cat}_fit'} for cat in ["Economic Value", "Interest Value", "Social Value", "Development Value", "Application Value"]],
                        value='Economic Value_fit', #default
                        id='category-selector',
                        style=get_dropdown_style(width="100%", margin="0 0 20px 0")
                    ),
                    dcc.Graph(id='profile-fit-bar')
                ])
            ], style={**get_card_style(dark_mode), 'flex': '1 1 500px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

        html.Div([  #Sentiment + Sunburst
            html.Div(dcc.Graph(id='empat-sentiment-bar'),style={**get_card_style(dark_mode), 'flex': '1 1 480px'}),
            html.Div(dcc.Graph(id='cooccurrence-network'),style={**get_card_style(dark_mode), 'flex': '1 1 480px', 'minWidth': '400px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

        html.Div([  # Radial chart full width
            html.Div(dcc.Graph(id='neglect-radial'),style={**get_card_style(dark_mode), 'maxWidth': '960px', 'margin': '20px auto'})
        ])
    ])

dashboard.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        theme_toggle
    ], style={'backgroundColor': 'transparent'}),
    html.Div(id='page-content')
])

@dashboard.callback(Output('page-content', 'children'),
                    Input('url', 'pathname'),
                    Input('dark-mode-toggle', 'value'))
def display_page(pathname, theme_value):
    if pathname == '/temporal':
        return temporal_layout(theme_value)
    elif pathname == '/empat':
        return empat_layout(theme_value)
    return overview_layout(theme_value)

@dashboard.callback(
    Output('firm-dropdown-container', 'style'),
    Input('dark-mode-toggle', 'value')
)
def update_dropdown_style(dark_mode):
    return get_dropdown_style(dark_mode)

@dashboard.callback(
    Output('ratings-firm-dropdown', 'style'),
    Input('dark-mode-toggle', 'value')
)
def update_ratings_dropdown_style(dark_mode):
    return get_dropdown_style(dark_mode)

@dashboard.callback(
    Output('category-selector', 'style'),
    Input('dark-mode-toggle', 'value')
)
def update_profile_dropdown_style(dark_mode):
    return get_dropdown_style(dark_mode)

@dashboard.callback(
    Output('bar-chart', 'figure'),
    Output('radar-chart', 'figure'),
    Output('pros-worddonut', 'figure'),
    Output('cons-worddonut', 'figure'),
    Input('firm-dropdown', 'value'),
    Input('dark-mode-toggle', 'value')
)
def update_overview(selected_firm, theme_value):
    dark_mode = theme_value
    # ==== BAR CHART ====
    row = df_avg[df_avg['firm'] == selected_firm].iloc[0]
    fig_bar = go.Figure([
        go.Bar(name='Overall Rating %', x=['Overall Rating'], y=[row['overall_rating'] * 20], marker_color='lightgoldenrodyellow'),
        go.Bar(name='Recommend %', x=['Recommend %'], y=[row['recommend_percent']], marker_color='lightcoral'),
        go.Bar(name='Outlook %', x=['Outlook %'], y=[row['outlook_percent']], marker_color='mediumvioletred')
    ])
    fig_bar.update_layout(
        template='plotly_dark' if dark_mode else 'plotly',
        title=f"{selected_firm} - Company Summary",
        yaxis=dict(title='Percentage %'),
        barmode='group',
        plot_bgcolor = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        font=dict(color='white' if dark_mode else 'black')
    )

    # ==== RADAR CHART ====
    row = df_empat[df_empat['firm'] == selected_firm]
    categories = ['Social Value', 'Interest Value', 'Development Value', 'Application Value', 'Economic Value']
    pros_values = [row[f'pros_{cat}'].values[0] for cat in categories]
    cons_values = [row[f'cons_{cat}'].values[0] for cat in categories]

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=pros_values,
        theta=categories,
        fill='toself',
        name='Pros',
        line=dict(color='forestgreen'),
        marker=dict(size=6),
        opacity=0.6
    ))

    fig_radar.add_trace(go.Scatterpolar(
        r=cons_values,
        theta=categories,
        fill='toself',
        name='Cons',
        line=dict(color='tomato'),
        marker=dict(size=6),
        opacity=0.6
    ))
    fig_radar.update_layout(
        template='plotly_dark' if dark_mode else 'plotly',
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 60], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11)),
            bgcolor='lightgray'
        ),
        showlegend=True,
        title=f"{selected_firm} EmpAt Radar",
        margin=dict(t=50, l=80, r=80, b=50),  # ← increased left & right margins
        height=500,
        width=500,  # ← optionally set fixed width to fit container better
        font=dict(color='white' if dark_mode else 'black'),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # ==== DONUT CHART ====       
    def get_top_words(text_series, num_words=10):
        text = " ".join(text_series.dropna().astype(str))
        words = text.lower().split()
        word_counts = Counter(words)
        most_common = word_counts.most_common(num_words)
        labels, values = zip(*most_common) if most_common else ([], [])
        return labels, values
    
    firm_text = df_reviews[df_reviews['firm'] == selected_firm]
    pros_labels, pros_values = get_top_words(firm_text['top_pros_text'])
    cons_labels, cons_values = get_top_words(firm_text['top_cons_text'])

    fig_pros_donut = go.Figure(data=[go.Pie(
        labels=pros_labels,
        values=pros_values,
        hole=.5,
        marker=dict(colors=px.colors.sequential.Tealgrn),
        textinfo='label+percent'
    )])
    fig_pros_donut.update_layout(
        title='Top Pros Phrases',
        template='plotly_dark' if dark_mode else 'plotly',
        font=dict(color='white' if dark_mode else 'black'),
        plot_bgcolor= "rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    fig_cons_donut = go.Figure(data=[go.Pie(
        labels=cons_labels,
        values=cons_values,
        hole=.5,
        marker=dict(colors=px.colors.sequential.Pinkyl),
        textinfo='label+percent'
    )])
    fig_cons_donut.update_layout(
        title='Top Cons Phrases',
        template='plotly_dark' if dark_mode else 'plotly',
        font=dict(color='white' if dark_mode else 'black'),
        plot_bgcolor= "rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig_bar, fig_radar, fig_pros_donut, fig_cons_donut

@dashboard.callback(
    Output('ratings-time-series', 'figure'),
    Input('ratings-firm-dropdown', 'value'),
    Input('dark-mode-toggle', 'value')
)
def update_temporal_ratings(selected_firm, theme_value):
    dark_mode = theme_value
    firm_data = df_yearly_ratings[df_yearly_ratings['firm'] == selected_firm]

    # ==== MULTI-LINE RATINGS PLOT ====
    fig = px.line(
        firm_data,
        x='year',
        y=['overall_rating', 'work_life_balance', 'culture_values', 'career_opp', 'comp_benefits', 'senior_mgmt'],
        title=f"{selected_firm} - Average Ratings Over Time",
        markers=True
    )
    fig.update_layout(
        template='plotly_dark' if dark_mode else 'plotly',
        xaxis_title="Year",
        yaxis_title="Rating",
        legend_title="Category",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color='white' if dark_mode else 'black')
    )
    return fig

@dashboard.callback(
    Output('empat-time-series', 'figure'),
    Output('topic-trends', 'figure'),
    Input('url', 'pathname'),  #Dummy trigger to render on load
    Input('dark-mode-toggle', 'value')
)
def update_temporal(pathname, theme_value):
    dark_mode = theme_value
    
    # ==== STACKED EMPAT AREA CHART ====
    empat_melt = df_empat_time.melt(id_vars='year_month', var_name='EmpAT Category', value_name='Count')
    fig2 = px.area(
        empat_melt,
        x='year_month',
        y='Count',
        color='EmpAT Category',
        title="EmpAT Category Mentions Over Time"
    )
    fig2.update_layout(
        template='plotly_dark' if dark_mode else 'plotly',
        xaxis_title="Year", 
        yaxis_title="Mentions",
        plot_bgcolor = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        font=dict(color='white' if dark_mode else 'black')
    )

    # ==== TOPIC TRENDS STACKED AREA ====
    topic_melt = df_topic_trends.melt(id_vars='year_month', var_name='Topic', value_name='Count')
    fig3 = px.area(
        topic_melt,
        x='year_month',
        y='Count',
        color='Topic',
        title="Buzzword/Topic Trends Over Time"
    )
    fig3.update_layout(
        template='plotly_dark' if dark_mode else 'plotly',
        xaxis_title="Year", 
        yaxis_title="Mentions",
        plot_bgcolor = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        font=dict(color='white' if dark_mode else 'black')
    )
    return fig2, fig3

@dashboard.callback(
    Output('profile-fit-bar', 'figure'),
    Input('category-selector', 'value'),
    Input('dark-mode-toggle', 'value')
)
def update_empat_profile(selected_category, theme_value):
    dark_mode = theme_value

    # ==== FIRM RANK HORIZONTAL BAR ====
    # Filter and get top 10 firms
    df_sorted = df_profile_fit[['firm', selected_category]].sort_values(by=selected_category, ascending=False).head(10)

    emp_fig1 = px.bar(
        df_sorted,
        x=selected_category,
        y='firm',
        orientation='h',
        title=f"Top 10 Firms by {selected_category.replace('_fit', '')}",
        color='firm',
        color_discrete_sequence=px.colors.qualitative.Bold,
        category_orders={"firm": df_sorted['firm'].tolist()}
    )
    emp_fig1.update_layout(
        template='plotly_dark' if dark_mode else 'plotly',
        xaxis_title="Percentage",
        yaxis_title="",
        showlegend=False,
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color='white' if dark_mode else 'black'),
        margin=dict(l=100, r=20, t=60, b=40)
    )
    return emp_fig1

@dashboard.callback(
    Output('empat-sentiment-bar','figure'),
    Output('cooccurrence-network','figure'),
    Output('neglect-radial','figure'),
    Input('url', 'pathname'),
    Input('dark-mode-toggle', 'value')
)
def update_empat(pathname, theme_value):
    dark_mode = theme_value

    # ==== SENTIMENT POLARITY DIVERGING BAR ====
    df_sent = df_empat_sentiment.melt(id_vars=['EmpAt Value'], 
                                    value_vars=['Positive %', 'Negative %'],
                                    var_name='Sentiment', 
                                    value_name='Percentage')
    df_sent['Percentage'] = df_sent.apply(
        lambda x: -x['Percentage'] if x['Sentiment'] == 'Negative %' else x['Percentage'], axis=1) #Create mirrored values for diverging effect
    
    emp_fig2 = px.bar(
        df_sent,
        x='Percentage',
        y='EmpAt Value',
        color='Sentiment',
        color_discrete_map={'Positive %': 'limegreen', 'Negative %': 'Tomato'},
        title="Sentiment Polarity Across EmpAT Values"
    )
    emp_fig2.update_layout(
        template= 'plotly_dark' if dark_mode else 'plotly',
        xaxis_title="Percentage", 
        yaxis_title="EmpAt Dimension",
        plot_bgcolor= "rgba(0,0,0,0)",
        paper_bgcolor= "rgba(0,0,0,0)",
        font= dict(color='white' if dark_mode else 'black')
    )

    # ==== CO-OCCURANCE SUNBURST DIAGRAM ==== 
    def create_sunburst_diagram(df_cooccurrence, dark_mode):
        parent_child_counts = (df_cooccurrence.groupby('Parent')['Child'].nunique().sort_values(ascending=False))
        ordered_dimensions = parent_child_counts.index.tolist()
        color_palette = px.colors.qualitative.Bold[:len(ordered_dimensions)]
        color_map = {dim: color for dim, color in zip(ordered_dimensions, color_palette)}
        
        labels = ["EmpAT"]
        parents = [""]
        values = [0] 
        colors = ["mediumvioletred"]
        ids = ["EmpAT"]  # Unique node IDs
        customdata = ["EmpAT"]
        dimension_values = {}
        for dim in ordered_dimensions:
            dim_rows = df_cooccurrence[df_cooccurrence['Parent'] == dim]
            total = dim_rows['Count'].sum()
            dimension_values[dim] = total
            labels.append(dim)
            parents.append("EmpAT")
            values.append(total)
            colors.append(color_map[dim])
            ids.append(dim)
            customdata.append(dim)
        
        for parent in ordered_dimensions: 
            child_rows = df_cooccurrence[df_cooccurrence['Parent'] == parent].sort_values('Child')
            for _, row in child_rows.iterrows(): #Add co-occurrence relationships(second layer)
                unique_id = f"{parent}|{row['Child']}"
                labels.append(row['Child'])
                parents.append(parent)
                values.append(row['Count'])
                colors.append(color_map[parent])
                ids.append(unique_id)
                customdata.append(f"{parent} → {row['Child']}")

        values[0] = sum(dimension_values.values())
          
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            ids=ids,  # Ensure uniqueness
            branchvalues='total',
            marker=dict(
                colors=colors,
                line=dict(width=1, color='black' if not dark_mode else 'white')
            ),
            hovertemplate='<b>%{customdata}</b><br>Count: %{value:,}<extra></extra>',
            customdata=customdata,
            textfont=dict(color='white' if dark_mode else 'black'),
            textinfo='label'  
        ))
        fig.update_layout(
            title='EmpAT Co-occurrence Sunburst',
            margin=dict(t=50, l=0, r=0, b=0),
            template='plotly_dark' if dark_mode else 'plotly',
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color='white' if dark_mode else 'black'),
            height=500
        )
        return fig
        
    emp_fig3 = create_sunburst_diagram(df_cooccurrence, dark_mode)

    # ==== EMPAT NEGLECT RADIAL CHART ====
    def create_radial_column_chart(df, dark_mode):
        categories = df['EmpAt Value'].tolist()
        values = df['Total Mentions'].tolist()
        
        #Create the radial bar chart using barpolar
        fig = go.Figure()
        #Add bars for each category
        for i, (category, value) in enumerate(zip(categories, values)):
            fig.add_trace(go.Barpolar(
                r=[value],  # Length of bar
                theta=[i * (360 / len(categories))],  # Position around circle
                width=[360 / len(categories) - 10], 
                name=category,
                marker_color=px.colors.qualitative.Bold[i % len(px.colors.qualitative.Bold)],
                opacity=0.8,
                hoverinfo='text',
                hovertext=f"{category}: {value} mentions"
            ))
        fig.update_layout(
            title="Neglected EmpAT Values - Radial Column Chart",
            template='plotly_dark' if dark_mode else 'plotly',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.1],  # Add padding
                    showticklabels=True,
                    tickfont=dict(color='white' if dark_mode else 'black', size=10),
                    gridcolor='rgba(255,255,255,0.2)' if dark_mode else 'rgba(0,0,0,0.2)'
                ),
                angularaxis=dict(
                    tickvals=[i * (360 / len(categories)) for i in range(len(categories))],
                    ticktext=categories,
                    direction="clockwise",
                    tickfont=dict(color='white' if dark_mode else 'black', size=12),
                    rotation=90,  # Rotate to match example
                    gridcolor='rgba(255,255,255,0.2)' if dark_mode else 'rgba(0,0,0,0.2)'
                ),
                bgcolor='rgba(0,0,0,0.1)' if dark_mode else 'rgba(240,240,240,0.5)'
            ),
            showlegend=False,
            height=500,
            margin=dict(t=80, b=80, l=80, r=80),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color='white' if dark_mode else 'black')
        )
        return fig
    emp_fig4 = create_radial_column_chart(df_neglect, dark_mode)

    return emp_fig2, emp_fig3, emp_fig4

@dashboard.callback(
    Output('page-content', 'style'),
    Input('dark-mode-toggle', 'value')
)
def update_theme(theme_value):
    if theme_value:
        return {'backgroundColor': '#2b2b2b', 'color': 'white', 'minHeight': '100vh'}
    return {'backgroundColor': 'whitesmoke', 'color': 'black', 'minHeight': '100vh'}

if __name__ == '__main__':
    debug = False if os.environ.get('PYTHONANYWHERE_DOMAIN') else True
    dashboard.run_server(
        debug=debug,
        host='0.0.0.0', 
        port=8080
    )
