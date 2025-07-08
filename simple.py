#!/usr/bin/env python3
"""
Dashboard de Visualização para o Sistema de Monitoramento - CORRIGIDO
Interface web interativa usando Dash/Plotly
"""

import json
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
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
        self.app.title = "Sistema de Monitoramento"
        
        # Caminhos de dados
        self.data_path = Path(self.config['data']['processed_output_path'])
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Cache de dados
        self.data_cache = None
        self.last_update = None
        
        # Configurar layout e callbacks
        self.setup_layout()
        self.setup_callbacks()
        
        self.logger.info("Dashboard inicializado")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configurações do arquivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Arquivo de configuração não encontrado: {config_path}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Retorna configuração padrão"""
        return {
            "system": {"debug": True},
            "data": {"processed_output_path": "data/processed/"},
            "visualization": {
                "dashboard_port": 8050,
                "update_interval": 5000
            }
        }
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO if self.config.get('system', {}).get('debug', True) else logging.WARNING,
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
                return self._generate_sample_data()
            
            latest_file = max(processed_files, key=lambda f: f.stat().st_mtime)
            
            # Verificar se é mais recente que o cache
            file_mtime = latest_file.stat().st_mtime
            
            if (self.last_update is None or file_mtime > self.last_update):
                df = pd.read_csv(latest_file)
                
                # Converter timestamp se existir
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                
                self.data_cache = df
                self.last_update = file_mtime
                
                self.logger.info(f"Dados atualizados: {len(df)} registros de {latest_file}")
            
            return self.data_cache
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            return self._generate_sample_data()
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Gera dados de exemplo para demonstração"""
        import numpy as np
        
        # Gerar dados de exemplo
        n_records = 100
        n_sensors = 5
        
        data = []
        base_time = datetime.now() - timedelta(hours=2)
        
        for i in range(n_records):
            for sensor_id in range(1, n_sensors + 1):
                timestamp = base_time + timedelta(minutes=i*2)
                
                record = {
                    'timestamp': timestamp,
                    'sensor_id': f'S{sensor_id:03d}',
                    'flow_rate': np.random.normal(50, 10),
                    'pressure': np.random.normal(2.5, 0.5),
                    'temperature': np.random.normal(25, 3),
                    'ph_level': np.random.normal(7.2, 0.5),
                    'turbidity': np.random.normal(20, 5),
                    'location_x': -46.731386 + np.random.normal(0, 0.01),
                    'location_y': -23.559616 + np.random.normal(0, 0.01),
                    'is_anomaly': np.random.choice([True, False], p=[0.1, 0.9]),
                    'processed_at': datetime.now()
                }
                data.append(record)
        
        df = pd.DataFrame(data)
        self.logger.info("Dados de exemplo gerados")
        return df
    
    def setup_layout(self):
        """Configura o layout do dashboard"""
        
        # Header
        header = dbc.Row([
            dbc.Col([
                html.H1("🚰 Sistema de Monitoramento - Esgotamento Sanitário", 
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
                    dbc.CardHeader("🔧 Controles"),
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
                    dbc.CardHeader("📊 Vazão vs Pressão"),
                    dbc.CardBody([
                        dcc.Graph(id="flow-pressure-chart")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🌡️ Temperatura e pH"),
                    dbc.CardBody([
                        dcc.Graph(id="temp-ph-chart")
                    ])
                ])
            ], width=6)
        ], className="mb-4")
        
        # Gráfico de séries temporais
        time_series = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Série Temporal - Parâmetros"),
                    dbc.CardBody([
                        dcc.Graph(id="time-series-chart")
                    ])
                ])
            ])
        ], className="mb-4")
        
        # Alertas
        alerts_section = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("⚠️ Alertas Recentes"),
                    dbc.CardBody([
                        html.Div(id="alerts-list")
                    ])
                ])
            ])
        ], className="mb-4")
        
        # Auto-refresh
        auto_refresh = dcc.Interval(
            id='interval-component',
            interval=self.config.get('visualization', {}).get('update_interval', 5000),
            n_intervals=0
        )
        
        # Layout final
        self.app.layout = dbc.Container([
            auto_refresh,
            header,
            stats_cards,
            controls,
            main_charts,
            time_series,
            alerts_section
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
                try:
                    last_update = pd.to_datetime(df['processed_at']).max().strftime("%H:%M:%S")
                except:
                    last_update = datetime.now().strftime("%H:%M:%S")
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
                return self._create_empty_figure("Sem dados disponíveis")
            
            # Filtrar dados
            filtered_df = self.filter_data(df, selected_sensors, time_range)
            
            if filtered_df.empty:
                return self._create_empty_figure("Nenhum dado para os filtros selecionados")
            
            # Verificar se temos as colunas necessárias
            if 'pressure' not in filtered_df.columns or 'flow_rate' not in filtered_df.columns:
                return self._create_empty_figure("Dados de pressão ou vazão não disponíveis")
            
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
                return self._create_empty_figure("Sem dados disponíveis")
            
            # Filtrar dados
            filtered_df = self.filter_data(df, selected_sensors, time_range)
            
            if filtered_df.empty or 'timestamp' not in filtered_df.columns:
                return self._create_empty_figure("Nenhum dado para os filtros selecionados")
            
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
            Output('time-series-chart', 'figure'),
            [Input('sensor-dropdown', 'value'),
             Input('time-range-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_time_series_chart(selected_sensors, time_range, n):
            df = self.load_latest_data()
            
            if df is None or df.empty or 'timestamp' not in df.columns:
                return self._create_empty_figure("Sem dados disponíveis")
            
            # Filtrar dados
            filtered_df = self.filter_data(df, selected_sensors, time_range)
            
            if filtered_df.empty:
                return self._create_empty_figure("Nenhum dado para os filtros selecionados")
            
            # Criar gráfico de séries temporais
            fig = go.Figure()
            
            # Adicionar cada parâmetro como linha
            parameters = [
                ('flow_rate', 'Vazão (L/s)', 'blue'),
                ('pressure', 'Pressão (bar)', 'red'),
                ('temperature', 'Temperatura (°C)', 'green'),
                ('ph_level', 'pH', 'orange'),
                ('turbidity', 'Turbidez (NTU)', 'purple')
            ]
            
            for param, label, color in parameters:
                if param in filtered_df.columns:
                    fig.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df[param],
                        name=label,
                        line=dict(color=color)
                    ))
            
            fig.update_layout(
                title="Série Temporal - Parâmetros de Monitoramento",
                xaxis_title="Tempo",
                yaxis_title="Valores",
                hovermode="x unified"
            )
            
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
                return dbc.Alert("✅ Nenhum alerta ativo - Sistema funcionando normalmente", color="success")
            
            # Criar lista de alertas
            alerts_list = []
            
            for _, row in alerts_df.head(10).iterrows():  # Últimos 10 alertas
                sensor_id = row.get('sensor_id', 'N/A')
                alert_text = f"🚨 Sensor {sensor_id}"
                
                if 'timestamp' in row and pd.notna(row['timestamp']):
                    try:
                        timestamp = pd.to_datetime(row['timestamp']).strftime("%H:%M:%S")
                        alert_text += f" - {timestamp}"
                    except:
                        pass
                
                # Determinar cor do alerta
                alert_color = "warning"
                if any(col in row and row[col] for col in ['flow_rate_anomaly', 'pressure_anomaly']):
                    alert_color = "danger"
                
                alerts_list.append(
                    dbc.Alert(alert_text, color=alert_color, className="mb-2")
                )
            
            return alerts_list
    
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
    
    def _create_empty_figure(self, message: str):
        """Cria figura vazia com mensagem"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
        )
        return fig
    
    def run(self, debug: bool = False, host: str = "127.0.0.1"):
        """Executa o dashboard"""
        port = self.config.get('visualization', {}).get('dashboard_port', 8050)
        
        self.logger.info(f"🚀 Iniciando dashboard em http://{host}:{port}")
        
        try:
            self.app.run(
                debug=debug,
                host=host,
                port=port,
                dev_tools_hot_reload=debug
            )
        except Exception as e:
            self.logger.error(f"Erro ao executar dashboard: {e}")
            raise

if __name__ == "__main__":
    dashboard = MonitoringDashboard()
    dashboard.run(debug=True)