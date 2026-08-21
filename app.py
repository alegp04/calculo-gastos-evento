from datetime import datetime
import io
import re
import urllib.parse
from fpdf import FPDF
import streamlit as st
import streamlit.components.v1 as components

# Configuración de Matplotlib sin interfaz gráfica
import matplotlib

matplotlib.use("Agg")
try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gastos de Evento",
    page_icon="🎉",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- ESTILOS CSS REFINADOS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }

    /* Banner */
    .hero-container {
        background-color: #1E293B;
        padding: 12px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 15px;
    }
    .hero-title { font-size: 18px; font-weight: 800; }

    /* Botón Cargar Datos (Azul, Blanco, Negrita) */
    div[data-testid="stForm"] button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        height: 45px !important;
        border: none !important;
        width: 100% !important;
    }

    /* Botones Inferiores (WhatsApp / PDF) - Lado a lado forzado */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        flex: 1 !important;
    }

    /* Botón WhatsApp */
    div[data-testid="stLinkButton"] a {
        background-color: #25D366 !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        height: 45px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-decoration: none !important;
    }
    /* Botón PDF */
    .stDownloadButton button {
        background-color: #DC2626 !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
    }

    /* Limpiar Todo */
    div[class*="st-key-clean_all_btn"] button {
        background-color: #E2E8F0 !important;
        color: #475569 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
    }

    /* Cruz eliminar */
    div[class*="st-key-del_p_"] button {
        background: transparent !important;
        color: #94A3B8 !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 18px !important;
    }
    div[class*="st-key-del_p_"] button:hover { color: #EF4444 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- LÓGICA ---
if "participants" not in st.session_state: st.session_state.participants = []
if "expenses" not in st.session_state: st.session_state.expenses = []

def calculate_settlements(balances):
    debtors = sorted([[k, -v] for k, v in balances.items() if v < -0.01], key=lambda x: x[1], reverse=True)
    creditors = sorted([[k, v] for k, v in balances.items() if v > 0.01], key=lambda x: x[1], reverse=True)
    settlements = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor_name, debt = debtors[i]
        creditor_name, credit = creditors[j]
        amount = min(debt, credit)
        settlements.append((debtor_name, creditor_name, amount))
        debtors[i][1] -= amount
        creditors[j][1] -= amount
        if debtors[i][1] < 0.01: i += 1
        if creditors[j][1] < 0.01: j += 1
    return settlements

# --- INTERFAZ ---
st.markdown('<div class="hero-container"><div class="hero-title">🥳 Cuentas del Evento</div></div>', unsafe_allow_html=True)

col_date, col_name = st.columns([1, 1.5], vertical_alignment="center")
with col_date: event_date = st.date_input("📅 Fecha:", datetime.now())
with col_name: event_name = st.text_input("🏷️ Evento:", value="Asado con Amigos")

with st.form("smart_input_form", clear_on_submit=True):
    user_input = st.text_input("Ingreso rápido:", placeholder="Ej: Nico | Nico 15000 Carne", label_visibility="collapsed")
    submit_btn = st.form_submit_button("⚡ Cargar Datos")
    if submit_btn and user_input.strip():
        match = re.search(r"^(.*?)\s+(\d+(?:[\.,]\d+)?)\s*(.*)$", user_input.strip())
        if match:
            name, amount, concept = match.group(1).strip().capitalize(), float(match.group(2).replace(",", ".")), match.group(3).strip() or "Varios"
            if amount > 0:
                if name not in st.session_state.participants: st.session_state.participants.append(name)
                st.session_state.expenses.append({"payer": name, "amount": amount, "concept": concept})
                st.rerun()
        else:
            name = user_input.strip().capitalize()
            if name not in st.session_state.participants:
                st.session_state.participants.append(name)
                st.rerun()

with st.expander("❓ ¿Cómo cargar datos?"):
    st.markdown("- **Solo persona:** `Nico`\n- **Con gasto:** `Juan 18000 Carne`")

# LISTA INTEGRANTES
st.markdown("<b>👥 INTEGRANTES ({})</b>".format(len(st.session_state.participants)), unsafe_allow_html=True)
for idx, person in enumerate(st.session_state.participants):
    c1, c2 = st.columns([0.85, 0.15])
    c1.write(f"• {person}")
    if c2.button("✕", key=f"del_p_{idx}"):
        st.session_state.participants.pop(idx)
        st.session_state.expenses = [e for e in st.session_state.expenses if e["payer"] != person]
        st.rerun()

if st.session_state.participants:
    st.button("🗑️ Limpiar Todo", key="clean_all_btn", use_container_width=True)

# RESULTADOS
if st.session_state.participants and st.session_state.expenses:
    st.write("---")
    total_spent = sum(e["amount"] for e in st.session_state.expenses)
    per_person = total_spent / len(st.session_state.participants)
    balances = {p: -per_person for p in st.session_state.participants}
    for e in st.session_state.expenses: balances[e["payer"]] += e["amount"]
    
    # Métricas
    st.markdown(f"""
        <div style="display:flex; gap:10px; margin-bottom:15px;">
            <div style="flex:1; background:#FFF; border:1px solid #E2E8F0; padding:10px; border-radius:10px; text-align:center;">
                <div style="font-size:10px; font-weight:800; color:#64748B;">GASTO TOTAL</div>
                <div style="font-size:16px; font-weight:800;">${total_spent:,.2f}</div>
            </div>
            <div style="flex:1; background:#FFF; border:1px solid #E2E8F0; padding:10px; border-radius:10px; text-align:center;">
                <div style="font-size:10px; font-weight:800; color:#64748B;">POR PERSONA</div>
                <div style="font-size:16px; font-weight:800; color:#2563EB;">${per_person:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Pagos
    settlements = calculate_settlements(balances)
    st.markdown("<b>💸 ¿Quién le paga a quién?</b>", unsafe_allow_html=True)
    for d, c, a in settlements:
        st.markdown(f'<div style="background:#EFF6FF; padding:10px; border-radius:8px; border-left:4px solid #2563EB; margin-bottom:5px;">💳 <b>{d}</b> ➔ <b>{c}</b>: <b>${a:,.2f}</b></div>', unsafe_allow_html=True)

    # BOTONES FINALES
    wa_text = f"Resumen {event_name}: Total ${total_spent:,.2f}"
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("💬 WhatsApp", f"https://wa.me/?text={urllib.parse.quote(wa_text)}", use_container_width=True)
    with col2:
        st.download_button("📄 PDF", data=b"PDF_DUMMY", file_name="cuentas.pdf", use_container_width=True)
