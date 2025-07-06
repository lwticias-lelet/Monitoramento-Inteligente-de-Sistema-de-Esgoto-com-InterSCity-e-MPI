#!/usr/bin/env python3
"""
Dashboard de Visualização para o Sistema de Monitoramento
Interface web interativa usando Dash/Plotly
"""

import json
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

class MonitoringDashboard:
    """Dashboard principal para monitoramento em tempo real"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Configurar Dash app
        self.app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Sistema de Monitoramento - Esgotamento Sanitário"
        
        # Caminhos de dados
        self.data_path = Path(self.config['data']['processed_output_path'])
        
        # Cache de dados
        self.data_cache = {}
        self.last_update = None
        
        # Configurar layout
        self.setup_layout()
        self.setup_callbacks()
        
        self.logger.info("Dashboard inicializado")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configurações do arquivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO if self.config['system']['debug'] else logging.WARNING,
            format='%(asctime)s - Dashboard - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_latest_data(self) -> Optional[pd.DataFrame]:
        """Carrega os dados mais recentes"""
        try:
            # Buscar arquivo mais recente
            processed_files = list(self.data_path.glob("data_processed_*.csv"))
            
            if not processed_files:
                self.logger.warning("Nenhum arquivo processado encontrado")
                return None
            
            latest_file = max(processed_files, key=lambda f: f.stat().st_mtime)
            
            # Verificar se é mais recente que o cache
            file_mtime = latest_file.stat().st_mtime
            
            if (self.last_update is None or file_mtime > self.last_update):
                df = pd.read_csv(latest_file)
                
                # Converter timestamp
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                self.data_cache = df
                self.last_update = file_mtime
                
                self.logger.info(f"Dados atualizados: {len(df)} registros de {latest_file}")
            
            return self.data_cache if not isinstance(self.data_cache, dict) else None
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            return None
    
    def setup_layout(self):
        """Configura o layout do dashboard"""
        
        # Header
        header = dbc.Row([
            dbc.Col([
                html.H1("Sistema de Monitoramento - Esgotamento Sanitário", 
                       className="text-center text-primary mb-4"),
                html.Hr()
            ])
        ])
        
        # Cards de estatísticas
        stats_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="total-sensors", children="0", className="text-info"),
                        html.P("Sensores Ativos", className="card-text")
                    ])
                ], className="h-100")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="total-alerts", children="0", className="text-warning"),
                        html.P("Alertas Ativos", className="card-text")
                    ])
                ], className="h-100")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="total-records", children="0", className="text-success"),
                        html.P("Registros Processados", className="card-text")
                    ])
                ], className="h-100")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="last-update", children="--", className="text-secondary"),
                        html.P("Última Atualização", className="card-text")
                    ])
                ], className="h-100")
            ], width=3)
        ], className="mb-4")
        
        # Controles
        controls = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Controles"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Sensor:"),
                                dcc.Dropdown(
                                    id="sensor-dropdown",
                                    placeholder="Selecione um sensor...",
                                    multi=True
                                )
                            ], width=6),
                            
                            dbc.Col([
                                html.Label("Período:"),
                                dcc.Dropdown(
                                    id="time-range-dropdown",
                                    options=[
                                        {"label": "Última Hora", "value": "1H"},
                                        {"label": "Últimas 6 Horas", "value": "6H"},
                                        {"label": "Último Dia", "value": "1D"},
                                        {"label": "Última Semana", "value": "7D"},
                                        {"label": "Todos", "value": "ALL"}
                                    ],
                                    value="6H"
                                )
                            ], width=6)
                        ])
                    ])
                ])
            ])
        ], className="mb-4")
        
        # Gráficos principais
        main_charts = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Vazão vs Pressão"),
                    dbc.CardBody([
                        dcc.Graph(id="flow-pressure-chart")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Temperatura e pH"),
                    dbc.CardBody([
                        dcc.Graph(id="temp-ph-chart")
                    ])
                ])
            ], width=6)
        ], className="mb-4")
        
        # Gráfico de mapa e alertas
        map_alerts = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Mapa de Sensores"),
                    dbc.CardBody([
                        dcc.Graph(id="sensor-map")
                    ])
                ])
            ], width=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Alertas Recentes"),
                    dbc.CardBody([
                        html.Div(id="alerts-list")
                    ])
                ])
            ], width=4)
        ], className="mb-4")
        
        # Gráfico de séries temporais
        time_series = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Série Temporal - Parâmetros"),
                    dbc.CardBody([
                        dcc.Graph(id="time-series-chart")
                    ])
                ])
            ])
        ], className="mb-4")
        
        # Auto-refresh
        auto_refresh = dcc.Interval(
            id='interval-component',
            interval=self.config['visualization']['update_interval'],
            n_intervals=0
        )
        
        # Layout final
        self.app.layout = dbc.Container([
            auto_refresh,
            header,
            stats_cards,
            controls,
            main_charts,
            map_alerts,
            time_series
        ], fluid=True)
    
    def setup_callbacks(self):
        """Configura os callbacks do dashboard"""
        
        @self.app.callback(
            [Output('sensor-dropdown', 'options'),
             Output('total-sensors', 'children'),
             Output('total-alerts', 'children'),
             Output('total-records', 'children'),
             Output('last-update', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_stats(n):
            df = self.load_latest_data()
            
            if df is None or df.empty:
                return [], "0", "0", "0", "--"
            
            # Opções de sensores
            sensors = df['sensor_id'].unique() if 'sensor_id' in df.columns else []
            sensor_options = [{"label": f"Sensor {s}", "value": s} for s in sorted(sensors)]
            
            # Estatísticas
            total_sensors = len(sensors)
            total_alerts = df['is_anomaly'].sum() if 'is_anomaly' in df.columns else 0
            total_records = len(df)
            
            # Última atualização
            if 'processed_at' in df.columns:
                last_update = pd.to_datetime(df['processed_at']).max().strftime("%H:%M:%S")
            else:
                last_update = datetime.now().strftime("%H:%M:%S")
            
            return sensor_options, str(total_sensors), str(total_alerts), str(total_records), last_update
        
        @self.app.callback(
            Output('flow-pressure-chart', 'figure'),
            [Input('sensor-dropdown', 'value'),
             Input('time-range-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_flow_pressure_chart(selected_sensors, time_range, n):
            df = self.load_latest_data()
            
            if df is None or df.empty:
                return px.scatter(title="Sem dados disponíveis")
            
            # Filtrar dados
            filtered_df = self.filter_data(df, selected_sensors, time_range)
            
            if filtered_df.empty:
                return px.scatter(title="Nenhum dado para os filtros selecionados")
            
            # Criar gráfico
            fig = px.scatter(
                filtered_df,
                x='pressure',
                y='flow_rate',
                color='sensor_id' if 'sensor_id' in filtered_df.columns else None,
                size='temperature' if 'temperature' in filtered_df.columns else None,
                hover_data=['timestamp'] if 'timestamp' in filtered_df.columns else None,
                title="Vazão vs Pressão por Sensor"
            )
            
            fig.update_layout(
                xaxis_title="Pressão (bar)",
                yaxis_title="Vazão (L/s)"
            )
            
            return fig
        
        @self.app.callback(
            Output('temp-ph-chart', 'figure'),
            [Input('sensor-dropdown', 'value'),
             Input('time-range-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_temp_ph_chart(selected_sensors, time_range, n):
            df = self.load_latest_data()
            
            if df is None or df.empty:
                return px.line(title="Sem dados disponíveis")
            
            # Filtrar dados
            filtered_df = self.filter_data(df, selected_sensors, time_range)
            
            if filtered_df.empty or 'timestamp' not in filtered_df.columns:
                return px.line(title="Nenhum dado para os filtros selecionados")
            
            # Criar gráfico com dois eixos Y
            fig = go.Figure()
            
            # Temperatura
            if 'temperature' in filtered_df.columns:
                fig.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=filtered_df['temperature'],
                    name='Temperatura (°C)',
                    line=dict(color='red'),
                    yaxis='y'
                ))
            
            # pH
            if 'ph_level' in filtered_df.columns:
                fig.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=filtered_df['ph_level'],
                    name='pH',
                    line=dict(color='blue'),
                    yaxis='y2'
                ))
            
            # Layout com dois eixos Y
            fig.update_layout(
                title="Temperatura e pH ao Longo do Tempo",
                xaxis=dict(title="Tempo"),
                yaxis=dict(title="Temperatura (°C)", side="left"),
                yaxis2=dict(title="pH", side="right", overlaying="y"),
                hovermode="x unified"
            )
            
            return fig
        
        @self.app.callback(
            Output('sensor-map', 'figure'),
            [Input('sensor-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_sensor_map(selected_sensors, n):
            df = self.load_latest_data()
            
            if df is None or df.empty:
                return px.scatter_mapbox(title="Sem dados disponíveis")
            
            # Verificar se temos coordenadas
            if 'location_x' not in df.columns or 'location_y' not in df.columns:
                return px.scatter(title="Coordenadas não disponíveis")
            
            # Filtrar sensores se selecionados
            if selected_sensors:
                df = df[df['sensor_id'].isin(selected_sensors)]
            
            # Agrupar por sensor para pegar última posição
            latest_positions = df.groupby('sensor_id').last().reset_index()
            
            # Criar mapa
            fig = px.scatter_mapbox(
                latest_positions,
                lat='location_y',
                lon='location_x',
                color='sensor_id',
                size='flow_rate' if 'flow_rate' in latest_positions.columns else None,
                hover_name='sensor_id',
                hover_data=['flow_rate', 'pressure', 'temperature'] if all(col in latest_positions.columns for col in ['flow_rate', 'pressure', 'temperature']) else None,
                mapbox_style="open-street-map",
                zoom=10,
                title="Localização dos Sensores"
            )
            
            fig.update_layout(height=400)
            
            return fig
        
        @self.app.callback(
            Output('alerts-list', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_alerts_list(n):
            df = self.load_latest_data()
            
            if df is None or df.empty or 'is_anomaly' not in df.columns:
                return html.P("Nenhum alerta disponível")
            
            # Filtrar apenas anomalias
            alerts_df = df[df['is_anomaly'] == True]
            
            if alerts_df.empty:
                return dbc.Alert("Nenhum alerta ativo", color="success")
            
            # Criar lista de alertas
            alerts_list = []
            
            for _, row in alerts_df.head(10).iterrows():  # Últimos 10 alertas
                alert_text = f"Sensor {row['sensor_id']}"
                
                if 'timestamp' in row:
                    timestamp = pd.to_datetime(row['timestamp']).strftime("%H:%M:%S")
                    alert_text += f" - {timestamp}"
                
                # Determinar tipo de alerta
                alert_color = "warning"
                if row.get('flow_rate_anomaly', False):
                    alert_color = "danger"
                elif row.get('pressure_anomaly', False):
                    alert_color = "warning"
                
                alerts_list.append(
                    dbc.Alert(alert_text, color=alert_color, className="mb-2")
                )
            
            return alerts_list
        
        @self.app.callback(
            Output('time-series-chart', 'figure'),
            [Input('sensor-dropdown', 'value'),
             Input('time-range-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_time_series_chart(selected_sensors, time_range, n):
            df = self.load_latest_data()
            
            if df is None or df.empty or 'timestamp' not in df.columns:
                return px.line(title="Sem dados disponíveis")
            
            # Filtrar dados
            filtered_df = self.filter_data(df, selected_sensors, time_range)
            
            if filtered_df.empty:
                return px.line(title="Nenhum dado para os filtros selecionados")
            
            # Criar gráfico de séries temporais
            fig = go.Figure()
            
            # Adicionar cada parâmetro como linha
            parameters = ['flow_rate', 'pressure', 'temperature', 'ph_level']
            colors = ['blue', 'red', 'green', 'orange']
            
            for param, color in zip(parameters, colors):
                if param in filtered_df.columns:
                    fig.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df[param],
                        name=param.replace('_', ' ').title(),
                        line=dict(color=color)
                    ))
            
            fig.update_layout(
                title="Série Temporal - Parâmetros de Monitoramento",
                xaxis_title="Tempo",
                yaxis_title="Valores",
                hovermode="x unified"
            )
            
            return fig
    
    def filter_data(self, df: pd.DataFrame, selected_sensors: List[str], time_range: str) -> pd.DataFrame:
        """Filtra dados baseado nos controles selecionados"""
        filtered_df = df.copy()
        
        # Filtrar por sensores
        if selected_sensors and 'sensor_id' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sensor_id'].isin(selected_sensors)]
        
        # Filtrar por tempo
        if time_range != "ALL" and 'timestamp' in filtered_df.columns:
            now = datetime.now()
            
            if time_range == "1H":
                cutoff = now - timedelta(hours=1)
            elif time_range == "6H":
                cutoff = now - timedelta(hours=6)
            elif time_range == "1D":
                cutoff = now - timedelta(days=1)
            elif time_range == "7D":
                cutoff = now - timedelta(days=7)
            else:
                cutoff = None
            
            if cutoff:
                filtered_df = filtered_df[filtered_df['timestamp'] >= cutoff]
        
        return filtered_df
    
    def run(self, debug: bool = False, host: str = "127.0.0.1"):
        """Executa o dashboard"""
        port = self.config['visualization']['dashboard_port']
        
        self.logger.info(f"Iniciando dashboard em http://{host}:{port}")
        
        self.app.run_server(
            debug=debug,
            host=host,
            port=port
        )

if __name__ == "__main__":
    dashboard = MonitoringDashboard()
    dashboard.run(debug=True)