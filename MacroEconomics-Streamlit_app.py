import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from openai import OpenAI

# Configura tu clave OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def obtener_codigo_pais(direccion):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': direccion, 'format': 'json', 'limit': 1, 'addressdetails': 1}
    headers = {'User-Agent': 'valoracion-ai/1.0'}
    try:
        resp = requests.get(url, params=params, headers=headers)
        data = resp.json()
        if data:
            address = data[0]["address"]
            return address.get("country_code", "").upper()
    except:
        return None
    return None

# --- UI ---
st.title("📍 Resumen de Inflación Armonizada (HICP) con GPT")
direccion = st.text_input("Introduce una dirección europea:")
longitud = st.slider("Número deseado de palabras en el resumen:", 100, 300, 150, step=25)

if st.button("Generar resumen") and direccion:
    codigo_pais = obtener_codigo_pais(direccion)

    if not codigo_pais:
        st.error("No se pudo detectar el país a partir de la dirección.")
    else:
        paises_nombre = {
            "NL": "Países Bajos", "ES": "España", "FR": "Francia",
            "IT": "Italia", "DE": "Alemania", "BE": "Bélgica",
            "PT": "Portugal", "AT": "Austria"
        }
        nombre_pais = paises_nombre.get(codigo_pais, f"País ({codigo_pais})")

        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_midx"
        params = {
            "format": "JSON",
            "lang": "EN",
            "geo": codigo_pais,
            "coicop": "CP00",
            "unit": "I15"
        }

        try:
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

            # --- GRÁFICO ---
            st.subheader("📊 Evolución de la inflación armonizada (HICP)")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(resultado["Trimestre"].astype(str), resultado["HICP promedio trimestral"], color='#DAA520', linewidth=2)
            ax.set_facecolor("#F5F5F5")
            fig.patch.set_facecolor("#F5F5F5")
            ax.tick_params(axis='x', rotation=45)
            ax.set_ylabel("Índice HICP (base 2015=100)")
            ax.set_xlabel("Trimestre")
            ax.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig)

            # --- GPT prompts ---
            prompt_es = f"""
Eres un economista que debe analizar la evolución de la inflación armonizada (HICP) de los últimos 5 años para el país: {nombre_pais}.

Tienes la siguiente tabla de promedios trimestrales del índice HICP:
{datos_texto}

Redacta un comentario profesional, técnico y claro de aproximadamente {longitud} palabras, describiendo la tendencia de la inflación, incluyendo etapas de aceleración o estabilización, y vinculándolo al contexto económico general cuando sea relevante. Termina con una frase que sitúe al lector en el momento actual. El texto debe estar en español.
"""

            prompt_en = f"""
You are an economist analyzing the evolution of the Harmonized Index of Consumer Prices (HICP) over the past 5 years for the country: {nombre_pais}.

You have the following table with quarterly average HICP values:
{datos_texto}

Write a professional, technical, and clear summary of approximately {longitud} words describing the inflation trend over these 5 years, including periods of acceleration or stabilization, and linking it to the general economic context when relevant. End with a sentence that situates the reader in the current moment. The text must be in English.
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
            st.error(f"❌ Error al obtener datos: {e}")
