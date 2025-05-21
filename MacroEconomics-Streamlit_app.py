import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI

# Configura OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Función para obtener país y código desde dirección
def obtener_localizacion_completa(direccion):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': direccion, 'format': 'json', 'limit': 1, 'addressdetails': 1}
    headers = {'User-Agent': 'valoracion-ai/1.0'}
    response = requests.get(url, params=params, headers=headers)
    try:
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            address = data[0]['address']
            ciudad = address.get('city') or address.get('town') or address.get('village') or address.get('county')
            pais = address.get('country')
            codigo_pais = address.get('country_code', '').lower()
            return lat, lon, ciudad, pais, codigo_pais
    except Exception as e:
        st.error(f"Error al obtener localización: {e}")
    return None, None, None, None, None

# Función para extraer indicadores desde TradingEconomics
def obtener_datos_macro(codigo_pais):
    url = f"https://tradingeconomics.com/{codigo_pais}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    indicadores_te = {
        "Inflación": "Inflation Rate",
        "PIB": "GDP Growth Rate",
        "Desempleo": "Unemployment Rate",
        "Bonos 10 años": "Government Bond 10Y"
    }
    resultados = {}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True)
                valor = cols[1].get_text(strip=True)
                for kpi, label_te in indicadores_te.items():
                    if label_te.lower() in label.lower():
                        resultados[kpi] = valor
    except Exception as e:
        st.error(f"Error al acceder a TradingEconomics: {e}")
    return resultados

# Streamlit UI
st.set_page_config(page_title="Macroeconomía Automática", layout="centered")
st.title("📊 Generador de Capítulo de Macroeconomía")
st.markdown("Introduce una dirección y selecciona los indicadores económicos que deseas incluir en el resumen del informe.")

direccion = st.text_input("Dirección del inmueble")

if direccion:
    lat, lon, ciudad, pais, codigo_pais = obtener_localizacion_completa(direccion)

    if pais:
        st.success(f"Ubicación detectada: {ciudad}, {pais.upper()}")

        kpis_seleccionados = st.multiselect(
            "Selecciona los indicadores clave:",
            ["Inflación", "PIB", "Desempleo", "Bonos 10 años"],
            default=["Inflación", "PIB", "Desempleo"]
        )

        num_palabras = st.slider("Número de palabras por resumen:", 50, 300, 150, step=10)

        if st.button("🧠 Generar resumen macroeconómico"):
            datos = obtener_datos_macro(codigo_pais)
            if not datos:
                st.error("No se pudieron obtener datos macroeconómicos.")
            else:
                # Formatear solo los seleccionados
                indicadores = "\n".join(f"- {kpi}: {datos[kpi]}" for kpi in kpis_seleccionados if kpi in datos)

                # PROMPT español
                prompt_es = f"""
Redacta un resumen profesional, técnico y neutral de aproximadamente {num_palabras} palabras sobre la evolución macroeconómica reciente del país {pais} y la Unión Europea en conjunto.
Incluye exclusivamente estos indicadores del país:
{indicadores}
Finaliza con una visión sintética del contexto europeo actual.
"""

                # PROMPT inglés
                prompt_en = f"""
Write a professional, technical and neutral summary of approximately {num_palabras} words about the recent macroeconomic evolution of {pais} and the European Union as a whole.
Include only the following indicators for the country:
{indicadores}
End with a concise view of the current European context.
"""

                try:
                    resp_es = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt_es}],
                        temperature=0.6
                    )
                    resp_en = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt_en}],
                        temperature=0.6
                    )
                    st.subheader("📘 Resumen en Español")
                    st.write(resp_es.choices[0].message.content)
                    st.subheader("📗 Summary in English")
                    st.write(resp_en.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error al generar el resumen: {e}")
    else:
        st.error("No se pudo identificar país desde la dirección.")
