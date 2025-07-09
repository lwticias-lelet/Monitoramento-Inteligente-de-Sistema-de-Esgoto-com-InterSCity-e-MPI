import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Monitoramento de Esgoto", layout="wide")

st.title("📡 Monitoramento de Esgoto - Dados em Tempo Real (InterSCity)")

# 🔗 UUID do recurso (substitua pelo correto, se necessário)
RESOURCE_ID = "sensor_01"  # ou o UUID real cadastrado
COLLECTOR_URL = f"https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/collector/resources/{RESOURCE_ID}/data"

# 📥 Carrega dados do InterSCity
@st.cache_data
def carregar_dados():
    try:
        payload = {
            "capabilities": ["flow_rate", "ph_level", "turbidity", "temperature"]
        }
        response = requests.post(COLLECTOR_URL, json=payload)
        response.raise_for_status()
        dados = response.json().get("data", [])

        if not dados:
            return pd.DataFrame()

        df = pd.DataFrame(dados)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(by="timestamp")
        return df

    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do InterSCity: {e}")
        return pd.DataFrame()

# ▶️ Carrega os dados
df = carregar_dados()

# 📅 Filtros por data
if not df.empty:
    data_inicio = st.date_input("Data inicial:", df["timestamp"].min().date())
    data_fim = st.date_input("Data final:", df["timestamp"].max().date())

    df_filtrado = df[
        (df["timestamp"] >= pd.to_datetime(data_inicio)) &
        (df["timestamp"] <= pd.to_datetime(data_fim + pd.Timedelta(days=1)))
    ]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado no intervalo selecionado.")
    else:
        st.success(f"✅ {len(df_filtrado)} registros encontrados.")
        st.write("📋 Amostra dos dados:", df_filtrado.head())

        # 📈 Vazão
        fig_vazao = px.line(df_filtrado, x="timestamp", y="flow_rate", title="Vazão do Esgoto (L/s)")
        st.plotly_chart(fig_vazao, use_container_width=True)

        # 📉 pH
        fig_ph = px.line(df_filtrado, x="timestamp", y="ph_level", title="pH do Esgoto")
        st.plotly_chart(fig_ph, use_container_width=True)

        # 🌫️ Turbidez
        if "turbidity" in df_filtrado.columns:
            fig_turbidez = px.line(df_filtrado, x="timestamp", y="turbidity", title="Turbidez (NTU)")
            st.plotly_chart(fig_turbidez, use_container_width=True)

        # 🌡️ Temperatura
        if "temperature" in df_filtrado.columns:
            fig_temp = px.line(df_filtrado, x="timestamp", y="temperature", title="Temperatura do Efluente (°C)")
            st.plotly_chart(fig_temp, use_container_width=True)
else:
    st.warning("⚠️ Nenhum dado recebido do InterSCity. Execute o adaptador para enviar dados.")
