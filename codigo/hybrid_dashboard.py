#!/usr/bin/env python3
"""
Dashboard Híbrido: Local + FIWARE
Mostra dados do CSV local E do FIWARE Orion Context Broker
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime
from pathlib import Path
import requests
import json
import logging
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "🌐 Dashboard Híbrido: Local + FIWARE"

def load_local_data():
    """Carregar dados CSV locais"""
    try:
        # Tentar dados processados primeiro
        processed_path = Path("data/processed")
        if processed_path.exists():
            csv_files = list(processed_path.glob("*.csv"))
            if csv_files:
                latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest_file)
                df['source'] = 'local'
                df['source_file'] = latest_file.name
                logger.info(f"✅ Dados locais carregados: {len(df)} registros de {latest_file.name}")
                return df
        
        # Tentar dados adaptados
        adapted_file = Path("data/csv/monitoramento_adapted.csv")
        if adapted_file.exists():
            df = pd.read_csv(adapted_file)
            df['source'] = 'local'
            df['source_file'] = 'monitoramento_adapted.csv'
            logger.info(f"✅ Dados adaptados carregados: {len(df)} registros")
            return df
        
        logger.warning("❌ Nenhum arquivo CSV local encontrado")
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados locais: {e}")
        return pd.DataFrame()

def load_fiware_data():
    """Carregar dados do FIWARE Orion Context Broker"""
    try:
        response = requests.get("http://localhost:1026/v2/entities", timeout=10)
        
        if response.status_code == 200:
            entities = response.json()
            
            records = []
            for entity in entities:
                record = {
                    'sensor_id': entity['id'].replace('WaterSensor_', '').replace('Sensor_', ''),
                    'flow_rate': entity.get('flow_rate', {}).get('value', 0),
                    'pressure': entity.get('pressure', {}).get('value', 0),
                    'temperature': entity.get('temperature', {}).get('value', 0),
                    'ph_level': entity.get('ph_level', {}).get('value', 7),
                    'status': entity.get('status', {}).get('value', 'UNKNOWN'),
                    'timestamp': entity.get('timestamp', {}).get('value', datetime.now().isoformat()),
                    'source': 'fiware',
                    'entity_id': entity['id'],
                    'entity_type': entity['type']
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            logger.info(f"✅ Dados FIWARE carregados: {len(df)} entidades")
            return df
        else:
            logger.warning(f"❌ FIWARE respondeu com status {response.status_code}")
            return pd.DataFrame()
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"❌ FIWARE não disponível: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao carregar dados FIWARE: {e}")
        return pd.DataFrame()

def combine_data_sources(local_df, fiware_df):
    """Combinar dados locais + FIWARE"""
    if local_df.empty and fiware_df.empty:
        return pd.DataFrame(), "sem dados"
    elif local_df.empty:
        return fiware_df, "apenas FIWARE"
    elif fiware_df.empty:
        return local_df, "apenas local"
    else:
        # Combinar ambos
        combined_df = pd.concat([local_df, fiware_df], ignore_index=True)
        return combined_df, "híbrido"

def get_system_status():
    """Verificar status dos sistemas"""
    status = {
        'local': False,
        'fiware': False,
        'total_sensors': 0,
        'total_alerts': 0
    }
    
    # Verificar dados locais
    local_df = load_local_data()
    if not local_df.empty:
        status['local'] = True
        status['total_sensors'] += local_df['sensor_id'].nunique() if 'sensor_id' in local_df.columns else 0
    
    # Verificar FIWARE
    try:
        response = requests.get("http://localhost:1026/version", timeout=5)
        if response.status_code == 200:
            status['fiware'] = True
            
            # Contar entidades
            entities_response = requests.get("http://localhost:1026/v2/entities", timeout=5)
            if entities_response.status_code == 200:
                entities = entities_response.json()
                status['total_sensors'] += len(entities)
                
                # Contar alertas
                for entity in entities:
                    if entity.get('status', {}).get('value', 'NORMAL') != 'NORMAL':
                        status['total_alerts'] += 1
    except:
        pass
    
    return status

# Layout do Dashboard
app.layout = dbc.Container([
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🌐 Dashboard Híbrido: Local + FIWARE", 
                   className="text-center text-primary mb-3"),
            html.P("Sistema de Monitoramento de Esgotamento Sanitário - São Luís, MA", 
                   className="text-center text-muted mb-4"),
            html.Hr()
        ])
    ]),
    
    # Status dos sistemas
    dbc.Row([
        dbc.Col([
            dbc.Alert(id="system-status", color="info", className="mb-4")
        ])
    ]),
    
    # Cards de estatísticas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="total-entities", className="text-info"),
                    html.P("Total de Sensores", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="local-count", className="text-success"),
                    html.P("Dados Locais", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="fiware-count", className="text-primary"),
                    html.P("Dados FIWARE", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="alerts-count", className="text-warning"),
                    html.P("Alertas Ativos", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3)
    ], className="mb-4"),
    
    # Controles
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎛️ Filtros"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Fonte de Dados:"),
                            dcc.Dropdown(
                                id="source-filter",
                                options=[
                                    {"label": "🌐 Todos", "value": "all"},
                                    {"label": "📁 Local apenas", "value": "local"},
                                    {"label": "☁️ FIWARE apenas", "value": "fiware"}
                                ],
                                value="all"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Sensor:"),
                            dcc.Dropdown(id="sensor-filter", multi=True, placeholder="Todos os sensores")
                        ], width=4),
                        dbc.Col([
                            html.Label("Status:"),
                            dcc.Dropdown(
                                id="status-filter",
                                options=[
                                    {"label": "Todos", "value": "all"},
                                    {"label": "✅ Normal", "value": "NORMAL"},
                                    {"label": "🔴 Entupimento", "value": "ENTUPIMENTO"},
                                    {"label": "⚠️ Vazamento", "value": "VAZAMENTO"}
                                ],
                                value="all"
                            )
                        ], width=4)
                    ])
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # Gráficos principais
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Comparação de Fontes de Dados"),
                dbc.CardBody([
                    dcc.Graph(id="source-comparison")
                ])
            ], className="shadow-sm")
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🌊 Vazão vs Pressão"),
                dbc.CardBody([
                    dcc.Graph(id="flow-pressure-scatter")
                ])
            ], className="shadow-sm")
        ], width=6)
    ], className="mb-4"),
    
    # Segunda linha de gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🌡️ Distribuição de Temperatura"),
                dbc.CardBody([
                    dcc.Graph(id="temperature-distribution")
                ])
            ], className="shadow-sm")
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚗️ Níveis de pH"),
                dbc.CardBody([
                    dcc.Graph(id="ph-levels")
                ])
            ], className="shadow-sm")
        ], width=6)
    ], className="mb-4"),
    
    # Tabela de dados
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 Dados Detalhados"),
                dbc.CardBody([
                    html.Div(id="data-table")
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # Auto-refresh
    dcc.Interval(id='interval', interval=30000, n_intervals=0)
    
], fluid=True)

# Callbacks
@app.callback(
    [Output('system-status', 'children'),
     Output('system-status', 'color'),
     Output('total-entities', 'children'),
     Output('local-count', 'children'), 
     Output('fiware-count', 'children'),
     Output('alerts-count', 'children'),
     Output('sensor-filter', 'options')],
    [Input('interval', 'n_intervals')]
)
def update_status(n):
    # Carregar dados
    local_df = load_local_data()
    fiware_df = load_fiware_data()
    combined_df, data_type = combine_data_sources(local_df, fiware_df)
    
    # Contadores
    local_count = len(local_df) if not local_df.empty else 0
    fiware_count = len(fiware_df) if not fiware_df.empty else 0
    total_count = local_count + fiware_count
    
    # Alertas
    alerts_count = 0
    if not combined_df.empty and 'status' in combined_df.columns:
        alerts_count = len(combined_df[combined_df['status'] != 'NORMAL'])
    
    # Status message
    if data_type == "híbrido":
        status_msg = f"✅ Sistema híbrido ativo - Local: {local_count} registros, FIWARE: {fiware_count} entidades"
        status_color = "success"
    elif data_type == "apenas FIWARE":
        status_msg = f"☁️ Apenas FIWARE ativo - {fiware_count} entidades disponíveis"
        status_color = "info"
    elif data_type == "apenas local":
        status_msg = f"📁 Apenas dados locais - {local_count} registros disponíveis"
        status_color = "warning"
    else:
        status_msg = "❌ Nenhuma fonte de dados disponível"
        status_color = "danger"
    
    # Opções de sensores
    sensor_options = []
    if not combined_df.empty and 'sensor_id' in combined_df.columns:
        unique_sensors = combined_df['sensor_id'].unique()
        sensor_options = [{"label": f"📍 {sensor}", "value": sensor} for sensor in sorted(unique_sensors)]
    
    return (status_msg, status_color, str(total_count), str(local_count), 
            str(fiware_count), str(alerts_count), sensor_options)

@app.callback(
    Output('source-comparison', 'figure'),
    [Input('source-filter', 'value'),
     Input('interval', 'n_intervals')]
)
def update_source_comparison(source_filter, n):
    local_df = load_local_data()
    fiware_df = load_fiware_data()
    combined_df, _ = combine_data_sources(local_df, fiware_df)
    
    if combined_df.empty:
        return px.bar(title="📊 Sem dados disponíveis")
    
    # Filtrar por fonte
    if source_filter == "local":
        filtered_df = combined_df[combined_df['source'] == 'local']
    elif source_filter == "fiware":
        filtered_df = combined_df[combined_df['source'] == 'fiware']
    else:
        filtered_df = combined_df
    
    if filtered_df.empty:
        return px.bar(title="📊 Nenhum dado para o filtro selecionado")
    
    # Contar por fonte
    source_counts = filtered_df['source'].value_counts()
    
    fig = px.bar(
        x=source_counts.index,
        y=source_counts.values,
        title="📊 Distribuição por Fonte de Dados",
        labels={'x': 'Fonte', 'y': 'Número de Registros'},
        color=source_counts.index,
        color_discrete_map={'local': '#28a745', 'fiware': '#007bff'}
    )
    
    return fig

@app.callback(
    Output('flow-pressure-scatter', 'figure'),
    [Input('source-filter', 'value'),
     Input('sensor-filter', 'value'),
     Input('status-filter', 'value'),
     Input('interval', 'n_intervals')]
)
def update_flow_pressure_scatter(source_filter, sensor_filter, status_filter, n):
    local_df = load_local_data()
    fiware_df = load_fiware_data()
    combined_df, _ = combine_data_sources(local_df, fiware_df)
    
    if combined_df.empty:
        return px.scatter(title="🌊 Sem dados disponíveis")
    
    # Aplicar filtros
    filtered_df = combined_df.copy()
    
    if source_filter != "all":
        filtered_df = filtered_df[filtered_df['source'] == source_filter]
    
    if sensor_filter:
        filtered_df = filtered_df[filtered_df['sensor_id'].isin(sensor_filter)]
    
    if status_filter != "all" and 'status' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if filtered_df.empty:
        return px.scatter(title="🌊 Nenhum dado para os filtros selecionados")
    
    # Verificar se temos as colunas necessárias
    if 'flow_rate' not in filtered_df.columns or 'pressure' not in filtered_df.columns:
        return px.scatter(title="🌊 Colunas de vazão/pressão não disponíveis")
    
    fig = px.scatter(
        filtered_df,
        x='pressure',
        y='flow_rate',
        color='source',
        symbol='status' if 'status' in filtered_df.columns else None,
        hover_data=['sensor_id', 'temperature'] if 'temperature' in filtered_df.columns else ['sensor_id'],
        title="🌊 Vazão vs Pressão",
        labels={'pressure': 'Pressão (bar)', 'flow_rate': 'Vazão (L/s)'}
    )
    
    return fig

@app.callback(
    Output('temperature-distribution', 'figure'),
    [Input('source-filter', 'value'),
     Input('interval', 'n_intervals')]
)
def update_temperature_distribution(source_filter, n):
    local_df = load_local_data()
    fiware_df = load_fiware_data()
    combined_df, _ = combine_data_sources(local_df, fiware_df)
    
    if combined_df.empty or 'temperature' not in combined_df.columns:
        return px.histogram(title="🌡️ Dados de temperatura não disponíveis")
    
    # Filtrar por fonte
    if source_filter != "all":
        filtered_df = combined_df[combined_df['source'] == source_filter]
    else:
        filtered_df = combined_df
    
    fig = px.histogram(
        filtered_df,
        x='temperature',
        color='source',
        title="🌡️ Distribuição de Temperatura",
        labels={'temperature': 'Temperatura (°C)', 'count': 'Frequência'},
        nbins=20
    )
    
    return fig

@app.callback(
    Output('ph-levels', 'figure'),
    [Input('source-filter', 'value'),
     Input('interval', 'n_intervals')]
)
def update_ph_levels(source_filter, n):
    local_df = load_local_data()
    fiware_df = load_fiware_data()
    combined_df, _ = combine_data_sources(local_df, fiware_df)
    
    if combined_df.empty or 'ph_level' not in combined_df.columns:
        return px.box(title="⚗️ Dados de pH não disponíveis")
    
    # Filtrar por fonte
    if source_filter != "all":
        filtered_df = combined_df[combined_df['source'] == source_filter]
    else:
        filtered_df = combined_df
    
    fig = px.box(
        filtered_df,
        x='source',
        y='ph_level',
        color='source',
        title="⚗️ Níveis de pH por Fonte",
        labels={'ph_level': 'Nível de pH', 'source': 'Fonte de Dados'}
    )
    
    # Adicionar linhas de referência para pH ideal
    fig.add_hline(y=6.0, line_dash="dash", line_color="red", 
                  annotation_text="pH Mínimo (6.0)")
    fig.add_hline(y=8.5, line_dash="dash", line_color="red", 
                  annotation_text="pH Máximo (8.5)")
    
    return fig

@app.callback(
    Output('data-table', 'children'),
    [Input('source-filter', 'value'),
     Input('sensor-filter', 'value'),
     Input('status-filter', 'value'),
     Input('interval', 'n_intervals')]
)
def update_data_table(source_filter, sensor_filter, status_filter, n):
    local_df = load_local_data()
    fiware_df = load_fiware_data()
    combined_df, _ = combine_data_sources(local_df, fiware_df)
    
    if combined_df.empty:
        return html.P("📋 Nenhum dado disponível", className="text-muted")
    
    # Aplicar filtros
    filtered_df = combined_df.copy()
    
    if source_filter != "all":
        filtered_df = filtered_df[filtered_df['source'] == source_filter]
    
    if sensor_filter:
        filtered_df = filtered_df[filtered_df['sensor_id'].isin(sensor_filter)]
    
    if status_filter != "all" and 'status' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if filtered_df.empty:
        return html.P("📋 Nenhum dado para os filtros selecionados", className="text-muted")
    
    # Mostrar apenas últimos 10 registros
    display_df = filtered_df.tail(10)
    
    # Colunas para mostrar
    columns_to_show = ['sensor_id', 'source', 'flow_rate', 'pressure', 'temperature', 'ph_level', 'status']
    available_columns = [col for col in columns_to_show if col in display_df.columns]
    
    table_data = []
    for _, row in display_df[available_columns].iterrows():
        table_row = []
        for col in available_columns:
            value = row[col]
            if isinstance(value, float):
                value = f"{value:.2f}"
            table_row.append(html.Td(str(value)))
        table_data.append(html.Tr(table_row))
    
    # Headers
    headers = [html.Th(col.replace('_', ' ').title()) for col in available_columns]
    
    table = dbc.Table([
        html.Thead([html.Tr(headers)]),
        html.Tbody(table_data)
    ], striped=True, bordered=True, hover=True, size="sm")
    
    return [
        html.P(f"📊 Mostrando últimos {len(display_df)} de {len(filtered_df)} registros"),
        table
    ]

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌐 DASHBOARD HÍBRIDO: LOCAL + FIWARE")
    print("📍 São Luís, Maranhão, Brasil")
    print("="*70)
    print("🌐 Iniciando dashboard em http://localhost:8051")
    print("📊 Dados locais + FIWARE Orion Context Broker")
    print("🔄 Atualizações automáticas a cada 30 segundos")
    print("⏹️  Pressione Ctrl+C para parar")
    print("="*70 + "\n")
    
    try:
        app.run(debug=True, port=8051, host='127.0.0.1')
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar dashboard: {e}")