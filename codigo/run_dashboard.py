#!/usr/bin/env python3
"""
Dashboard Final para Sistema de Monitoramento
Otimizado para seus dados existentes
Execute com: python run_dashboard.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime
from pathlib import Path
import logging
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "🚰 Monitoramento de Esgotamento Sanitário"

def load_data():
    """Carrega os dados mais recentes disponíveis"""
    try:
        # 1. Primeiro tentar dados processados (melhor qualidade)
        processed_path = Path("data/processed")
        if processed_path.exists():
            csv_files = list(processed_path.glob("data_processed_*.csv"))
            if csv_files:
                latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest_file)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                logger.info(f"✅ Dados processados carregados: {len(df)} registros de {latest_file.name}")
                return df, "processados"
        
        # 2. Tentar dados adaptados
        adapted_file = Path("data/csv/monitoramento_adapted.csv")
        if adapted_file.exists():
            df = pd.read_csv(adapted_file)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"✅ Dados adaptados carregados: {len(df)} registros")
            return df, "adaptados"
        
        # 3. Tentar dados originais
        original_file = Path("data/csv/monitoramento.csv")
        if original_file.exists():
            df = pd.read_csv(original_file)
            # Mapear colunas para formato padrão
            if 'tempo_min' in df.columns:
                base_time = datetime.now() - pd.Timedelta(hours=24)
                df['timestamp'] = [base_time + pd.Timedelta(minutes=float(t)) for t in df['tempo_min']]
            if 'sensorId' in df.columns:
                df['sensor_id'] = df['sensorId']
            if 'vazao' in df.columns:
                df['flow_rate'] = df['vazao']
            if 'temperatura' in df.columns:
                df['temperature'] = df['temperatura']
            if 'pH' in df.columns:
                df['ph_level'] = df['pH']
            if 'turbidez' in df.columns:
                df['turbidity'] = df['turbidez']
            logger.info(f"✅ Dados originais carregados: {len(df)} registros")
            return df, "originais"
        
        logger.warning("❌ Nenhum arquivo encontrado")
        return pd.DataFrame(), "vazio"
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), "erro"

def get_data_info(df, data_type):
    """Obtém informações sobre os dados carregados"""
    if df.empty:
        return "Sem dados", 0, [], "N/A"
    
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else 'sensorId'
    if sensor_col not in df.columns:
        sensor_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    sensors = df[sensor_col].unique() if sensor_col in df.columns else []
    records = len(df)
    status_info = f"Tipo: {data_type}, Sensores: {len(sensors)}, Registros: {records}"
    
    return status_info, records, sensors, sensor_col

# Layout do Dashboard
app.layout = dbc.Container([
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🚰 Sistema de Monitoramento de Esgotamento Sanitário", 
                   className="text-center text-primary mb-3"),
            html.P("Dashboard em Tempo Real - São Luís, MA", className="text-center text-muted mb-4"),
            html.Hr()
        ])
    ]),
    
    # Status dos dados
    dbc.Row([
        dbc.Col([
            dbc.Alert(id="data-status", color="info", className="mb-4")
        ])
    ]),
    
    # Cards de Status
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="total-sensores", className="text-info"),
                    html.P("Sensores Ativos", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="total-registros", className="text-success"),
                    html.P("Total de Registros", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="alertas-criticos", className="text-warning"),
                    html.P("Status Críticos", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="ultima-atualizacao", className="text-secondary"),
                    html.P("Última Atualização", className="card-text")
                ])
            ], className="shadow-sm")
        ], width=3)
    ], className="mb-4"),
    
    # Controles
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎛️ Filtros e Controles"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Sensor:"),
                            dcc.Dropdown(id="filtro-sensor", multi=True, placeholder="Todos os sensores")
                        ], width=4),
                        dbc.Col([
                            html.Label("Parâmetro Principal:"),
                            dcc.Dropdown(
                                id="parametro-principal",
                                options=[
                                    {"label": "💧 Vazão", "value": "flow_rate"},
                                    {"label": "🌡️ Temperatura", "value": "temperature"},
                                    {"label": "⚗️ pH", "value": "ph_level"},
                                    {"label": "🌊 Turbidez", "value": "turbidity"},
                                    {"label": "📊 Pressão", "value": "pressure"}
                                ],
                                value="flow_rate"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Status:"),
                            dcc.Dropdown(
                                id="filtro-status",
                                options=[
                                    {"label": "Todos", "value": "ALL"},
                                    {"label": "✅ Normal", "value": "NORMAL"},
                                    {"label": "⚠️ Alerta", "value": "ALERTA"},
                                    {"label": "🚨 Crítico", "value": "CRITICO"}
                                ],
                                value="ALL"
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
                dbc.CardHeader("📈 Série Temporal do Parâmetro Selecionado"),
                dbc.CardBody([
                    dcc.Graph(id="grafico-tempo")
                ])
            ], className="shadow-sm")
        ], width=8),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Distribuição por Sensor"),
                dbc.CardBody([
                    dcc.Graph(id="grafico-boxplot")
                ])
            ], className="shadow-sm")
        ], width=4)
    ], className="mb-4"),
    
    # Segunda linha de gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🗺️ Mapa dos Sensores"),
                dbc.CardBody([
                    dcc.Graph(id="mapa-sensores")
                ])
            ], className="shadow-sm")
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 Status por Sensor"),
                dbc.CardBody([
                    dcc.Graph(id="status-sensores")
                ])
            ], className="shadow-sm")
        ], width=6)
    ], className="mb-4"),
    
    # Gráfico de correlação
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔗 Matriz de Correlação dos Parâmetros"),
                dbc.CardBody([
                    dcc.Graph(id="correlacao-parametros")
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # Auto-refresh
    dcc.Interval(id='interval', interval=30000, n_intervals=0)
    
], fluid=True)

# Callbacks
@app.callback(
    [Output('data-status', 'children'),
     Output('filtro-sensor', 'options'),
     Output('total-sensores', 'children'),
     Output('total-registros', 'children'),
     Output('alertas-criticos', 'children'),
     Output('ultima-atualizacao', 'children')],
    [Input('interval', 'n_intervals')]
)
def atualizar_stats(n):
    df, data_type = load_data()
    
    if df.empty:
        return "❌ Nenhum dado encontrado", [], "0", "0", "0", "Sem dados"
    
    status_info, records, sensors, sensor_col = get_data_info(df, data_type)
    
    # Opções de sensores
    opcoes_sensores = [{"label": f"📍 {s}", "value": s} for s in sensors]
    
    # Contar alertas críticos
    alertas = 0
    if 'status' in df.columns:
        alertas = df[df['status'].isin(['VAZAMENTO', 'ENTUPIMENTO', 'CONTAMINACAO'])].shape[0]
    
    ultima_atualizacao = datetime.now().strftime("%H:%M:%S")
    
    status_msg = f"✅ Dados carregados: {status_info}"
    
    return status_msg, opcoes_sensores, str(len(sensors)), str(records), str(alertas), ultima_atualizacao

@app.callback(
    Output('grafico-tempo', 'figure'),
    [Input('filtro-sensor', 'value'),
     Input('parametro-principal', 'value'),
     Input('filtro-status', 'value'),
     Input('interval', 'n_intervals')]
)
def atualizar_grafico_tempo(sensores_selecionados, parametro, status_filtro, n):
    df, _ = load_data()
    
    if df.empty:
        return px.line(title="📊 Sem dados disponíveis")
    
    # Filtrar dados
    df_filtrado = df.copy()
    
    # Filtrar por sensores
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else 'sensorId'
    if sensores_selecionados and sensor_col in df.columns:
        df_filtrado = df_filtrado[df_filtrado[sensor_col].isin(sensores_selecionados)]
    
    # Filtrar por status
    if status_filtro != "ALL" and 'status' in df.columns:
        if status_filtro == "CRITICO":
            df_filtrado = df_filtrado[df_filtrado['status'].isin(['VAZAMENTO', 'ENTUPIMENTO', 'CONTAMINACAO'])]
        else:
            df_filtrado = df_filtrado[df_filtrado['status'] == status_filtro]
    
    # Verificar se parâmetro existe
    if parametro not in df_filtrado.columns:
        return px.line(title=f"📊 Parâmetro {parametro} não disponível")
    
    # Criar gráfico
    if 'timestamp' in df_filtrado.columns:
        fig = px.line(
            df_filtrado, 
            x='timestamp', 
            y=parametro,
            color=sensor_col if sensor_col in df_filtrado.columns else None,
            title=f"📈 {parametro.replace('_', ' ').title()} ao Longo do Tempo"
        )
        fig.update_layout(xaxis_title="⏰ Tempo", yaxis_title=f"📊 {parametro.replace('_', ' ').title()}")
    else:
        # Se não tem timestamp, fazer gráfico de índice
        fig = px.line(
            df_filtrado.reset_index(), 
            x='index', 
            y=parametro,
            color=sensor_col if sensor_col in df_filtrado.columns else None,
            title=f"📈 {parametro.replace('_', ' ').title()} por Registro"
        )
        fig.update_layout(xaxis_title="📝 Registro", yaxis_title=f"📊 {parametro.replace('_', ' ').title()}")
    
    return fig

@app.callback(
    Output('grafico-boxplot', 'figure'),
    [Input('parametro-principal', 'value'),
     Input('filtro-status', 'value'),
     Input('interval', 'n_intervals')]
)
def atualizar_boxplot(parametro, status_filtro, n):
    df, _ = load_data()
    
    if df.empty or parametro not in df.columns:
        return px.box(title="📊 Dados não disponíveis")
    
    # Filtrar por status
    df_filtrado = df.copy()
    if status_filtro != "ALL" and 'status' in df.columns:
        if status_filtro == "CRITICO":
            df_filtrado = df_filtrado[df_filtrado['status'].isin(['VAZAMENTO', 'ENTUPIMENTO', 'CONTAMINACAO'])]
        else:
            df_filtrado = df_filtrado[df_filtrado['status'] == status_filtro]
    
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else 'sensorId'
    
    fig = px.box(
        df_filtrado, 
        x=sensor_col if sensor_col in df_filtrado.columns else None, 
        y=parametro,
        title=f"📊 Distribuição de {parametro.replace('_', ' ').title()} por Sensor"
    )
    fig.update_layout(xaxis_title="📍 Sensor", yaxis_title=f"📊 {parametro.replace('_', ' ').title()}")
    fig.update_xaxes(tickangle=45)
    
    return fig

@app.callback(
    Output('mapa-sensores', 'figure'),
    [Input('filtro-sensor', 'value'),
     Input('interval', 'n_intervals')]
)
def atualizar_mapa(sensores_selecionados, n):
    df, _ = load_data()
    
    if df.empty:
        return px.scatter(title="🗺️ Sem dados disponíveis")
    
    # Verificar coordenadas
    lat_col = 'location_y' if 'location_y' in df.columns else 'latitude'
    lon_col = 'location_x' if 'location_x' in df.columns else 'longitude'
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else 'sensorId'
    
    if lat_col not in df.columns or lon_col not in df.columns:
        return px.scatter(title="🗺️ Coordenadas não disponíveis")
    
    # Filtrar sensores
    df_mapa = df.copy()
    if sensores_selecionados and sensor_col in df.columns:
        df_mapa = df_mapa[df_mapa[sensor_col].isin(sensores_selecionados)]
    
    # Agrupar por sensor para pegar posição média
    if sensor_col in df_mapa.columns:
        df_posicoes = df_mapa.groupby(sensor_col).agg({
            lat_col: 'mean',
            lon_col: 'mean',
            'flow_rate': 'mean' if 'flow_rate' in df_mapa.columns else 'first'
        }).reset_index()
    else:
        df_posicoes = df_mapa
    
    # Criar mapa
    fig = px.scatter_mapbox(
        df_posicoes,
        lat=lat_col,
        lon=lon_col,
        color=sensor_col if sensor_col in df_posicoes.columns else None,
        size='flow_rate' if 'flow_rate' in df_posicoes.columns else None,
        hover_name=sensor_col if sensor_col in df_posicoes.columns else None,
        mapbox_style="open-street-map",
        zoom=11,
        title="🗺️ Localização dos Sensores em São Luís, MA"
    )
    
    fig.update_layout(height=400)
    
    return fig

@app.callback(
    Output('status-sensores', 'figure'),
    [Input('interval', 'n_intervals')]
)
def atualizar_status_sensores(n):
    df, _ = load_data()
    
    if df.empty or 'status' not in df.columns:
        return px.pie(title="📋 Status não disponível")
    
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else 'sensorId'
    
    # Contar status por sensor
    if sensor_col in df.columns:
        status_counts = df.groupby([sensor_col, 'status']).size().reset_index(name='count')
        fig = px.bar(
            status_counts, 
            x=sensor_col, 
            y='count', 
            color='status',
            title="📋 Distribuição de Status por Sensor"
        )
        fig.update_xaxes(tickangle=45)
    else:
        # Status geral
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig = px.pie(
            status_counts, 
            values='count', 
            names='status',
            title="📋 Distribuição Geral de Status"
        )
    
    return fig

@app.callback(
    Output('correlacao-parametros', 'figure'),
    [Input('filtro-sensor', 'value'),
     Input('interval', 'n_intervals')]
)
def atualizar_correlacao(sensores_selecionados, n):
    df, _ = load_data()
    
    if df.empty:
        return px.imshow(title="🔗 Sem dados para correlação")
    
    # Filtrar sensores
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else 'sensorId'
    if sensores_selecionados and sensor_col in df.columns:
        df = df[df[sensor_col].isin(sensores_selecionados)]
    
    # Selecionar colunas numéricas
    numeric_cols = ['flow_rate', 'temperature', 'ph_level', 'turbidity', 'pressure', 'vazao', 'temperatura', 'pH', 'turbidez']
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    if len(available_cols) < 2:
        return px.imshow(title="🔗 Dados insuficientes para correlação")
    
    # Calcular matriz de correlação
    corr_matrix = df[available_cols].corr()
    
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="🔗 Matriz de Correlação dos Parâmetros",
        color_continuous_scale="RdBu"
    )
    
    return fig

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚰 SISTEMA DE MONITORAMENTO DE ESGOTAMENTO SANITÁRIO")
    print("📍 São Luís, MaranhãPTK, Brasil")
    print("="*70)
    print("🌐 Iniciando dashboard em http://localhost:8050")
    print("📊 Atualizações automáticas a cada 30 segundos")
    print("⏹️  Pressione Ctrl+C para parar")
    print("="*70 + "\n")
    
    try:
        app.run(debug=True, port=8050, host='127.0.0.1')
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar dashboard: {e}")