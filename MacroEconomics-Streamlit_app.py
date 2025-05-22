import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from openai import OpenAI

# --- Configura la API KEY (ocúltala en producción con st.secrets) ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Configurada desde secrets.toml

# --- Interfaz de usuario ---
st.title("📈 Resumen de Inflación Armonizada (HICP)")
pais = st.selectbox("Selecciona un país europeo:", ["NL", "ES", "FR", "IT", "DE"])
nombre_pais = {
    "NL": "Países Bajos",
    "ES": "España",
    "FR": "Francia",
    "IT": "Italia",
    "DE": "Alemania"
}[pais]

if st.button("Generar resumen"):
    try:
        # --- Consulta a la API de Eurostat ---
        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_midx"
        params = {
            "format": "JSON",
            "lang": "EN",
            "geo": pais,
            "coicop": "CP00",
            "unit": "I15"
        }
        response = requests.get(url, params=params)
        data = response.json()

        time_labels = data["dimension"]["time"]["category"]["label"]
        periodos = list(time_labels.values())
        valores = list(data["value"].values())

        df = pd.DataFrame({"Periodo": periodos, "Valor": valores})
        df = df[df["Periodo"].str[:4].astype(int) >= 2018]
        df["Fecha"] = pd.to_datetime(df["Periodo"], format="%Y-%m")
        df["Trimestre"] = df["Fecha"].dt.to_period("Q")
        resultado = df.groupby("Trimestre")["Valor"].mean().reset_index()
        resultado.columns = ["Trimestre", "HICP promedio trimestral"]
        datos_texto = resultado.to_string(index=False)

        # --- Prompts GPT ---
        prompt_es = f"""
        Eres un economista que debe analizar la evolución de la inflación armonizada (HICP) de los últimos 5 años para el país: {nombre_pais}.
        Tienes la siguiente tabla de promedios trimestrales del índice HICP:
        {datos_texto}
        Redacta un comentario de entre 100 y 150 palabras, profesional, técnico y claro, describiendo la tendencia de la inflación a lo largo de estos 5 años, incluyendo las etapas de aceleración o estabilización y vinculándolo al contexto económico general cuando sea relevante. Termina con una frase que sitúe al lector en el momento actual. El texto debe estar en idioma español.
        """

        prompt_en = f"""
        You are an economist analyzing the evolution of the Harmonized Index of Consumer Prices (HICP) over the past 5 years for the country: {nombre_pais}.
        You have the following table with quarterly average HICP values:
        {datos_texto}
        Write a professional, technical, and clear summary of about 100 to 150 words describing the inflation trend over these 5 years, including periods of acceleration or stabilization, and linking it to the general economic context when relevant. End with a sentence that situates the reader in the current moment. The text must be written in English.
        """

        respuesta_es = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_es}],
            temperature=0.6
        )

        respuesta_en = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_en}],
            temperature=0.6
        )

        st.subheader("🧠 Resumen en español")
        st.write(respuesta_es.choices[0].message.content.strip())

        st.subheader("🧠 Summary in English")
        st.write(respuesta_en.choices[0].message.content.strip())

    except Exception as e:
        st.error(f"❌ Ha ocurrido un error: {e}")
