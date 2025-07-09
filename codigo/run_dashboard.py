#!/usr/bin/env python3
"""
Dashboard Final para Sistema de Monitoramento
Com limpeza de arquivos antigos e geração automática de dados processados
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

# Caminhos
PROCESSED_DIR = Path("codigo/data/processed")
ADAPTED_FILE = Path("codigo/data/csv/monitoramento_adapted.csv")

# Inicializar app ANTES dos callbacks
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "🚰 Monitoramento de Esgotamento Sanitário"

# Funções auxiliares
def limpar_arquivos_antigos():
    """Apaga arquivos CSV antigos na pasta processed"""
    if PROCESSED_DIR.exists():
        for arquivo in PROCESSED_DIR.glob("data_processed_*.csv"):
            try:
                arquivo.unlink()
                logger.info(f"Arquivo antigo removido: {arquivo.name}")
            except Exception as e:
                logger.warning(f"Erro ao remover {arquivo.name}: {e}")

def gerar_arquivo_processado():
    """Gera arquivo processado novo a partir do arquivo adaptado"""
    if not ADAPTED_FILE.exists():
        logger.error(f"Arquivo adaptado não encontrado: {ADAPTED_FILE}")
        return None
    
    try:
        df = pd.read_csv(ADAPTED_FILE)
        
        # Exemplo simples: adicionar coluna processed_at com timestamp atual
        df['processed_at'] = datetime.now().isoformat()
        
        # Nome do arquivo novo com timestamp
        nome_arquivo = f"data_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        caminho_arquivo = PROCESSED_DIR / nome_arquivo
        
        # Criar pasta se não existir
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(caminho_arquivo, index=False)
        logger.info(f"Arquivo processado gerado: {nome_arquivo}")
        
        return caminho_arquivo
    except Exception as e:
        logger.error(f"Erro ao gerar arquivo processado: {e}")
        return None

def load_data():
    """Carrega o arquivo processado mais recente"""
    if PROCESSED_DIR.exists():
        arquivos = list(PROCESSED_DIR.glob("data_processed_*.csv"))
        if arquivos:
            mais_recente = max(arquivos, key=lambda f: f.stat().st_mtime)
            df = pd.read_csv(mais_recente)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"Dados carregados do arquivo: {mais_recente.name} ({len(df)} registros)")
            return df, "processados"
    logger.warning("Nenhum arquivo processado encontrado")
    return pd.DataFrame(), "vazio"

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

# Limpar arquivos antigos e gerar novo arquivo processado ANTES de iniciar o dashboard
limpar_arquivos_antigos()
novo_arquivo = gerar_arquivo_processado()

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
    
    # Selecionar colunas numéricas para correlação
    cols_numericas = df.select_dtypes(include='number').columns
    if len(cols_numericas) < 2:
        return px.imshow(title="🔗 Dados numéricos insuficientes para correlação")
    
    corr = df[cols_numericas].corr()
    
    fig = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        title="🔗 Matriz de Correlação dos Parâmetros"
    )
    return fig

# Executar app
if __name__ == "__main__":
    print("\nIniciando Dashboard...")
    app.run(debug=True, port=8050, host='127.0.0.1')

