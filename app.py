from datetime import datetime
import io
import re
import urllib.parse
from fpdf import FPDF
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gastos", page_icon="🎉", layout="centered")

# --- CSS LIMPIO (Solo lo necesario) ---
st.markdown("""
    <style>
    /* Asegurar que las columnas siempre queden lado a lado en celular */
    [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
    
    /* Botón Cargar Datos */
    div.stButton > button { width: 100%; height: 45px; background-color: #2563EB; color: white; font-weight: 800; border-radius: 8px; border: none; }
    
    /* Botones de acción (WhatsApp/PDF) - Cuadrados y centrados */
    .btn-square { 
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 65px; height: 65px; border: 1px solid #E2E8F0; border-radius: 12px;
        background: white; text-decoration: none; color: #0F172A; margin: 0 auto;
    }
    
    /* Ajuste de título */
    .main .block-container { padding-top: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA ---
if "participants" not in st.session_state: st.session_state.participants = []
if "expenses" not in st.session_state: st.session_state.expenses = []

def calculate_settlements(balances):
    debtors = sorted([[k, -v] for k, v in balances.items() if v < -0.01], key=lambda x: x[1], reverse=True)
    creditors = sorted([[k, v] for k, v in balances.items() if v > 0.01], key=lambda x: x[1], reverse=True)
    settlements = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        d_n, d_a = debtors[i]; c_n, c_a = creditors[j]
        amount = min(d_a, c_a)
        settlements.append((d_n, c_n, amount))
        debtors[i][1] -= amount; creditors[j][1] -= amount
        if debtors[i][1] < 0.01: i += 1
        if creditors[j][1] < 0.01: j += 1
    return settlements

def generate_pdf(name, date, total, per_p, exps, bals, sets):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Evento: {name}", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Fecha: {date}", ln=True, align="C")
    return bytes(pdf.output())

# --- UI ---
st.markdown("### 🥳 Cuentas del Evento")

c_date, c_event = st.columns(2)
date = c_date.date_input("Fecha:", datetime.now())
event = c_event.text_input("Evento:", value="Asado")

with st.form("input", clear_on_submit=True):
    val = st.text_input("Ej: Nico | Nico 1500 Carne")
    if st.form_submit_button("⚡ Cargar Datos"):
        # Lógica simple de carga
        parts = val.split("|")
        name = parts[0].strip().capitalize()
        if name and name not in st.session_state.participants:
            st.session_state.participants.append(name)
            st.rerun()

st.markdown("---")
st.markdown("#### 👥 Integrantes")
for i, p in enumerate(st.session_state.participants):
    c1, c2 = st.columns([0.8, 0.2])
    c1.write(f"• {p}")
    if c2.button("✕", key=f"del_{i}"):
        st.session_state.participants.pop(i); st.rerun()

if st.button("🗑️ Limpiar Todo", use_container_width=True):
    st.session_state.participants = []
    st.rerun()

# --- BOTONES FINALES (EL CORAZÓN DEL PEDIDO) ---
if st.session_state.participants:
    st.markdown("---")
    wa_url = "https://wa.me/?text=Hola"
    pdf_data = generate_pdf("Asado", "2026/08/21", 0, 0, [], {}, [])
    
    # Columnas 50/50 forzadas
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Botón estilo cuadrado con logo WhatsApp oficial
        st.markdown(f'''
            <a href="{wa_url}" class="btn-square">
                <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="35">
            </a>
        ''', unsafe_allow_html=True)
        
    with col_b:
        # Botón estilo cuadrado con logo PDF oficial
        st.download_button(
            label="",
            data=pdf_data,
            file_name="cuentas.pdf",
            help="Descargar PDF",
            use_container_width=True
        )
        # Nota: Streamlit no permite poner imagen dentro del botón de descarga nativo, 
        # así que aplicamos este CSS para que parezca el logo
        st.markdown("""
            <style>
            .stDownloadButton button { 
                width: 65px !important; height: 65px !important; 
                background: url('https://upload.wikimedia.org/wikipedia/commons/8/87/PDF_file_icon.svg') no-repeat center center / 35px white !important;
                border: 1px solid #E2E8F0 !important; border-radius: 12px !important;
            }
            </style>
        """, unsafe_allow_html=True)
