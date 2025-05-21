import streamlit as st
import requests
import os
from openai import OpenAI

# ✅ Configurar cliente OpenAI desde secrets
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Función para obtener lat/lon + ciudad + país
def obtener_localizacion_completa(direccion):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': direccion, 'format': 'json', 'limit': 1, 'addressdetails': 1}
    headers = {'User-Agent': 'valorador-ai/1.0'}
    response = requests.get(url, params=params, headers=headers)
    try:
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            address = data[0]['address']
            ciudad = address.get('city') or address.get('town') or address.get('village') or address.get('county')
            pais = address.get('country')
            codigo_pais = address.get('country_code', '').upper()
            return lat, lon, ciudad, pais, codigo_pais
        else:
            return None, None, None, None, None
    except Exception as e:
        st.error(f"Error al buscar localización: {e}")
        return None, None, None, None, None

# ✅ Interfaz de usuario
st.set_page_config(page_title="Resumen Macroeconómico Automático", layout="centered")
st.title("📊 Generador de Capítulo de Macroeconomía")
st.markdown("Introduce una dirección y selecciona los indicadores clave para construir automáticamente el resumen macroeconómico del informe de valoración.")

direccion_macro = st.text_input("Introduce la dirección del inmueble")

if direccion_macro:
    lat, lon, ciudad, pais, codigo_pais = obtener_localizacion_completa(direccion_macro)

    if pais:
        st.success(f"Ubicación detectada: {ciudad}, {pais} ({codigo_pais})")

        kpis_seleccionados = st.multiselect(
            "Selecciona los indicadores clave a incluir:",
            ["Inflación", "PIB", "Desempleo", "Bonos 10 años"],
            default=["Inflación", "PIB", "Desempleo"]
        )

        num_palabras = st.slider(
            "Número aproximado de palabras del resumen:",
            min_value=50, max_value=300, value=150, step=10
        )

        if st.button("🧠 Generar resumen macroeconómico"):
            # Simulación de datos macroeconómicos fijos (por ahora)
            datos = {
                "Inflación": "1.5% en abril de 2025",
                "PIB": "0.3% de crecimiento interanual en el primer trimestre de 2025",
                "Desempleo": "3.6% en marzo de 2025",
                "Bonos 10 años": "2.8% de rendimiento en abril de 2025"
            }

            datos_seleccionados = [f"{kpi}: {datos[kpi]}" for kpi in kpis_seleccionados if kpi in datos]
            contenido_prompt = "\n".join(datos_seleccionados)

            prompt = f"""
Redacta un resumen profesional, técnico y neutral de aproximadamente {num_palabras} palabras que describa la evolución económica reciente del país {pais} y de la Unión Europea en su conjunto.
Incluye únicamente estos indicadores macroeconómicos del país:
{contenido_prompt}
Finaliza con un párrafo contextual que mencione brevemente la situación europea general.
"""

            try:
                respuesta = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6
                )
                texto_resumen = respuesta.choices[0].message.content
                st.subheader("📝 Resumen generado")
                st.write(texto_resumen)
            except Exception as e:
                st.error(f"Error al generar resumen: {e}")
    else:
        st.error("No se pudo determinar el país desde la dirección.")
