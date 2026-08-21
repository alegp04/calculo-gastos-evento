import base64
from datetime import datetime
import io
import re
import urllib.parse
from fpdf import FPDF
import streamlit as st

# Configuración de Matplotlib
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

# --- LOGOS VECTORIALES OFICIALES EXACTOS ---
WA_OFFICIAL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="#25D366" d="M0 512l35.3-128C12 347 0 303.5 0 256 0 114.6 114.6 0 256 0c141.4 0 256 114.6 256 256 0 141.4-114.6 256-256 256-47.5 0-91-12-128-35.3L0 512z"/><path fill="#FFFFFF" d="M256 46.5c-115.7 0-209.5 93.8-209.5 209.5 0 41.5 12.1 80.2 33 112.8L59.2 452.8l86-20.3c31.3 19.4 68.3 30.7 108 30.7 115.7 0 209.5-93.8 209.5-209.5S371.7 46.5 256 46.5zm121.2 296c-5.1 14.4-29.8 27.5-41.2 29.2-11 1.6-25.2 2.3-41-2.7-9.6-3-22-7.2-38.1-14.1-67.1-29.1-110.8-97.1-114.1-101.6-3.3-4.5-27.2-36.2-27.2-69 0-32.8 17.2-48.9 23.3-55.5 6.1-6.6 13.3-8.3 17.7-8.3 4.4 0 8.8 0 12.7.2 4.1.2 9.6-1.5 15 11.4 5.5 13.3 18.8 45.9 20.4 49.2 1.6 3.3 2.7 7.2.5 11.6-2.2 4.4-3.3 7.2-6.6 11-3.3 3.8-7 8.5-10 11.4-3.3 3.3-6.8 6.9-2.9 13.5 3.9 6.6 17.4 28.7 37.3 46.4 25.6 22.8 47.3 29.9 53.9 33.2 6.6 3.3 10.5 2.7 14.4-1.6 3.9-4.4 16.6-19.4 21-26.1 4.4-6.6 8.8-5.5 14.9-3.3 6.1 2.2 38.7 18.3 45.3 21.6 6.6 3.3 11 4.9 12.7 7.7 1.6 2.8 1.6 16.1-3.5 30.5z"/></svg>"""

ACROBAT_OFFICIAL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="#EC1C24" d="M128 0h256c70.7 0 128 57.3 128 128v256c0 70.7-57.3 128-128 128H128C57.3 512 0 454.7 0 384V128C0 57.3 57.3 0 128 0z"/><path fill="#FFFFFF" d="M358.5 284c-13.8-12-33.8-21.8-55.8-28.3 6.8-24.6 10.6-51.5 10.6-72.8 0-29.2-8.2-42.5-24.6-42.5-13.7 0-23.3 10.9-23.3 28 0 29.7 13.3 75.8 34.2 120.9-29 53.9-64.9 96.9-101.5 122.5-11.6 8.2-23.3 13-33.9 13-16 0-26.3-12-26.3-29.7 0-32.4 42-75.8 102.5-108.6 5.1-2.7 2.7-7.5-2.7-5.8-65.9 20.1-127 61.8-127 119.1 0 35.8 23.3 55.3 53.9 55.3 21.5 0 44-10.2 65.9-29 47.1-40.3 90.1-102.5 121.5-168.3 42 16.4 88.1 26.3 129 26.3 33.4 0 53.9-13.3 53.9-36.2 0-22.5-18.1-34.1-45-34.1-32.1 0-73 12-110.6 32.8 4.1 3.1 6.1 6.8 2.7 9.5zm84.3 10.9c16 0 24.6 5.5 24.6 15.3 0 10.2-9.2 15.3-23.5 15.3-26.3 0-58.4-8.2-87.7-20.8 28.6-6.8 59.3-9.8 86.6-9.8zM228.1 199.1c0-10.2 4.1-15.7 9.6-15.7 4.1 0 6.8 4.1 6.8 10.9 0 13.7-3.1 31.5-8.2 50.5-5.8-17.4-8.2-34.1-8.2-45.7z"/></svg>"""

WA_URI = f"data:image/svg+xml;base64,{base64.b64encode(WA_OFFICIAL_SVG.encode('utf-8')).decode('utf-8')}"
ACROBAT_URI = f"data:image/svg+xml;base64,{base64.b64encode(ACROBAT_OFFICIAL_SVG.encode('utf-8')).decode('utf-8')}"

# --- ESTILOS CSS CON ANULACIÓN DE COLAPSO EN MÓVIL ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }

    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
        overflow-x: hidden !important;
    }

    p, label, span, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #0F172A !important;
    }

    /* FORZAR COLUMNAS SIEMPRE LADO A LADO EN CELULARES */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        width: 100% !important;
    }

    div[data-testid="column"] {
        min-width: 0 !important;
    }

    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        div[data-testid="column"] {
            min-width: 0 !important;
        }
    }

    /* Banner Superior */
    .hero-container {
        background-color: #1E293B;
        padding: 10px 14px;
        border-radius: 10px;
        color: #FFFFFF !important;
        text-align: center;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 17px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        margin: 0;
    }

    /* Formulario */
    div[data-testid="stForm"] {
        padding: 10px !important;
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }

    /* Botón Cargar Datos */
    div[data-testid="stForm"] button {
        background-color: #2563EB !important;
        border: none !important;
        border-radius: 8px !important;
        height: 42px !important;
        width: 100% !important;
        cursor: pointer !important;
    }
    div[data-testid="stForm"] button p, 
    div[data-testid="stForm"] button span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 14px !important;
    }

    /* Cruz Eliminar Participante */
    div[class*="st-key-del_p_"] {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }
    div[class*="st-key-del_p_"] button {
        background: transparent !important;
        border: none !important;
        color: #94A3B8 !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        cursor: pointer !important;
        height: auto !important;
        min-height: 0 !important;
    }
    div[class*="st-key-del_p_"] button:hover {
        color: #EF4444 !important;
    }

    /* Botón Limpiar Todo */
    div[class*="st-key-clean_all_btn"] button {
        background-color: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        color: #64748B !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        height: 36px !important;
        width: 100% !important;
    }

    /* Tarjetas de Resultado */
    .flat-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px;
        padding: 8px 10px !important;
        margin-bottom: 4px !important;
        font-size: 13px !important;
    }

    .badge-debtor {
        background-color: #FEF2F2 !important;
        color: #EF4444 !important;
        border: 1px solid #FCA5A5 !important;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-creditor {
        background-color: #ECFDF5 !important;
        color: #10B981 !important;
        border: 1px solid #6EE7B7 !important;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-neutral {
        background-color: #F1F5F9 !important;
        color: #64748B !important;
        border: 1px solid #CBD5E1 !important;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
    }

    /* BOTONES CUADRADOS DE ACCIÓN CENTRADOS */
    .action-row-container {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 20px !important;
        margin-top: 15px !important;
        margin-bottom: 15px !important;
        width: 100% !important;
    }
    .btn-action-square {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 65px !important;
        height: 65px !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
    }
    .btn-action-square:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- INICIALIZACIÓN DEL ESTADO ---
if "participants" not in st.session_state:
    st.session_state.participants = []
if "expenses" not in st.session_state:
    st.session_state.expenses = []


# --- ALGORITMO DE LIQUIDACIÓN DE DEUDAS ---
def calculate_settlements(balances):
    debtors = sorted(
        [[k, -v] for k, v in balances.items() if v < -0.01],
        key=lambda x: x[1],
        reverse=True,
    )
    creditors = sorted(
        [[k, v] for k, v in balances.items() if v > 0.01],
        key=lambda x: x[1],
        reverse=True,
    )

    settlements = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor_name, debt = debtors[i]
        creditor_name, credit = creditors[j]
        amount = min(debt, credit)
        settlements.append((debtor_name, creditor_name, amount))

        debtors[i][1] -= amount
        creditors[j][1] -= amount

        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1
    return settlements


# --- GENERADOR DE PDF ---
def generate_pdf(
    event_name,
    event_date_str,
    total_spent,
    per_person,
    expenses,
    balances,
    settlements,
):
    pdf = FPDF()
    _ = pdf.add_page()
    _ = pdf.set_auto_page_break(auto=True, margin=15)

    def clean_txt(t):
        return str(t).encode("latin-1", "replace").decode("latin-1")

    _ = pdf.set_font("Helvetica", "B", 15)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(
        0,
        9,
        clean_txt(f"GASTOS DE EVENTO: {event_name.upper()}"),
        ln=True,
        align="C",
    )

    _ = pdf.set_font("Helvetica", "", 10)
    _ = pdf.set_text_color(100, 116, 139)
    _ = pdf.cell(
        0,
        5,
        clean_txt(
            f"Fecha: {event_date_str} | Reporte de Gastos y Transferencias"
        ),
        ln=True,
        align="C",
    )
    _ = pdf.ln(3)

    _ = pdf.set_fill_color(240, 249, 255)
    _ = pdf.rect(10, 30, 190, 12, "F")
    _ = pdf.set_y(32)
    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(37, 99, 235)
    _ = pdf.cell(95, 7, clean_txt(f"  Gasto Total: ${total_spent:,.2f}"), align="L")
    _ = pdf.cell(
        95,
        7,
        clean_txt(f"Total por Persona: ${per_person:,.2f}  "),
        align="R",
        ln=True,
    )
    _ = pdf.ln(3)

    if HAS_MATPLOTLIB:
        payer_totals = {}
        for exp in expenses:
            p = exp["payer"]
            payer_totals[p] = payer_totals.get(p, 0.0) + exp["amount"]

        if payer_totals and sum(payer_totals.values()) > 0:
            fig, ax = plt.subplots(figsize=(4.2, 2.0))
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_facecolor("#FFFFFF")
            labels = [clean_txt(k) for k in payer_totals.keys()]
            sizes = list(payer_totals.values())
            colors = [
                "#2563EB",
                "#10B981",
                "#F59E0B",
                "#EF4444",
                "#8B5CF6",
                "#EC4899",
                "#14B8A6",
                "#F97316",
            ]

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=colors[: len(labels)],
                textprops=dict(color="#334155", fontsize=8),
            )
            for autotext in autotexts:
                _ = autotext.set_color("white")
                _ = autotext.set_weight("bold")

            _ = ax.axis("equal")
            _ = plt.title(
                clean_txt("Distribución de Gastos"),
                fontsize=9,
                fontweight="bold",
                color="#1E293B",
                pad=4,
            )

            img_buf = io.BytesIO()
            _ = plt.savefig(
                img_buf, format="png", bbox_inches="tight", dpi=130, facecolor="#FFFFFF"
            )
            _ = plt.close(fig)
            _ = img_buf.seek(0)

            _ = pdf.image(img_buf, x=60, w=90)
            _ = pdf.ln(2)

    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 6, clean_txt("1. Detalle de los Gastos Cargados"), ln=True)

    _ = pdf.set_font("Helvetica", "B", 8)
    _ = pdf.set_fill_color(37, 99, 235)
    _ = pdf.set_text_color(255, 255, 255)
    _ = pdf.cell(50, 5, clean_txt(" Comprador"), border=0, fill=True)
    _ = pdf.cell(95, 5, clean_txt(" Concepto / Item"), border=0, fill=True)
    _ = pdf.cell(
        45,
        5,
        clean_txt(" Monto ($) "),
        border=0,
        fill=True,
        align="R",
        ln=True,
    )

    _ = pdf.set_font("Helvetica", "", 8)
    _ = pdf.set_text_color(51, 65, 85)
    fill = False
    for exp in expenses:
        _ = pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(
            255, 255, 255
        )
        _ = pdf.cell(
            50, 5, clean_txt(f" {exp['payer']}"), border="B", fill=fill
        )
        _ = pdf.cell(
            95, 5, clean_txt(f" {exp['concept']}"), border="B", fill=fill
        )
        _ = pdf.cell(
            45,
            5,
            clean_txt(f"${exp['amount']:,.2f} "),
            border="B",
            fill=fill,
            align="R",
            ln=True,
        )
        fill = not fill

    _ = pdf.ln(3)

    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 6, clean_txt("2. Estado de Cuentas por Persona"), ln=True)

    _ = pdf.set_font("Helvetica", "B", 8)
    _ = pdf.set_fill_color(37, 99, 235)
    _ = pdf.set_text_color(255, 255, 255)
    _ = pdf.cell(50, 5, clean_txt(" Persona"), border=0, fill=True)
    _ = pdf.cell(45, 5, clean_txt(" Pago Realizado"), border=0, fill=True, align="R")
    _ = pdf.cell(
        45, 5, clean_txt(" Le Correspondia"), border=0, fill=True, align="R"
    )
    _ = pdf.cell(
        50,
        5,
        clean_txt(" Balance "),
        border=0,
        fill=True,
        align="R",
        ln=True,
    )

    _ = pdf.set_font("Helvetica", "", 8)
    _ = pdf.set_text_color(51, 65, 85)
    fill = False
    for person, bal in balances.items():
        paid = sum(e["amount"] for e in expenses if e["payer"] == person)
        _ = pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(
            255, 255, 255
        )

        if bal > 0.01:
            status = f"+${bal:,.2f} (A favor)"
        elif bal < -0.01:
            status = f"-${abs(bal):,.2f} (Debe)"
        else:
            status = "$0.00 (A mano)"

        _ = pdf.cell(50, 5, clean_txt(f" {person}"), border="B", fill=fill)
        _ = pdf.cell(
            45, 5, clean_txt(f"${paid:,.2f} "), border="B", fill=fill, align="R"
        )
        _ = pdf.cell(
            45,
            5,
            clean_txt(f"${per_person:,.2f} "),
            border="B",
            fill=fill,
            align="R",
        )
        _ = pdf.cell(
            50,
            5,
            clean_txt(f"{status} "),
            border="B",
            fill=fill,
            align="R",
            ln=True,
        )
        fill = not fill

    _ = pdf.ln(3)

    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 6, clean_txt("3. Pagos / Transferencias a Realizar"), ln=True)

    if not settlements:
        _ = pdf.set_font("Helvetica", "I", 8)
        _ = pdf.cell(
            0,
            5,
            clean_txt("Todos aportaron la misma cantidad. No hay deudas."),
            ln=True,
        )
    else:
        _ = pdf.set_font("Helvetica", "", 8)
        for debtor, creditor, amount in settlements:
            _ = pdf.set_fill_color(241, 245, 249)
            _ = pdf.cell(
                0,
                6,
                clean_txt(
                    f"   - {debtor} ---> le transfiere a ---> {creditor}:   ${amount:,.2f}"
                ),
                ln=True,
                fill=True,
            )
            _ = pdf.ln(1)

    return bytes(pdf.output())


# --- INTERFAZ PRINCIPAL ---

st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🥳 Cuentas del Evento</div>
    </div>
""",
    unsafe_allow_html=True,
)

# Nombre del Evento a ancho completo
event_name = st.text_input(
    "🏷️ Evento:",
    value="Asado con Amigos",
    placeholder="Ej: Topopeña...",
)

# Formulario de Carga
with st.form("smart_input_form", clear_on_submit=True):
    user_input = st.text_input(
        "Ingreso rápido:",
        placeholder="Ej: Nico | Nico 15000 Carne",
        label_visibility="collapsed",
    )
    submit_btn = st.form_submit_button(
        "⚡ Cargar Datos", use_container_width=True
    )

    if submit_btn and user_input.strip():
        raw_text = user_input.strip()
        match = re.search(r"^(.*?)\s+(\d+(?:[\.,]\d+)?)\s*(.*)$", raw_text)

        if match:
            name = match.group(1).strip().capitalize()
            amount = float(match.group(2).replace(",", "."))
            concept = match.group(3).strip() or "Varios"

            if amount > 0:
                if name not in st.session_state.participants:
                    st.session_state.participants.append(name)
                st.session_state.expenses.append(
                    {"payer": name, "amount": amount, "concept": concept}
                )
                st.toast(f"¡Registrado! {name}: ${amount:,.2f} ({concept})")
                st.rerun()
            else:
                st.error("El monto debe ser mayor a 0.")
        else:
            name = raw_text.capitalize()
            if name not in st.session_state.participants:
                st.session_state.participants.append(name)
                st.toast(f"¡{name} agregado!")
                st.rerun()
            else:
                st.info(f"{name} ya está en la lista.")

with st.expander("❓ ¿Cómo cargar datos?"):
    st.markdown(
        """
        - **Sumar integrante sin gasto:** `Nico`
        - **Gasto completo:** `Juan 18000 Carne`
        - **Gasto simple:** `Pedro 5000`
    """
    )

# LISTA UNIFICADA DE PARTICIPANTES
st.markdown(
    f"<div style='font-size:12px; font-weight:800; color:#475569; margin-bottom:4px;'>👥 INTEGRANTES Y COMPRAS ({len(st.session_state.participants)})</div>",
    unsafe_allow_html=True,
)

if not st.session_state.participants:
    st.caption("Sin integrantes cargados.")
else:
    for idx, person in enumerate(st.session_state.participants):
        person_expenses = [
            e for e in st.session_state.expenses if e["payer"] == person
        ]
        total_p = sum(e["amount"] for e in person_expenses)

        if person_expenses:
            concepts = [
                e["concept"]
                for e in person_expenses
                if e["concept"] and e["concept"] != "Varios"
            ]
            concept_str = (
                f" <span style='color:#64748B; font-size:11px;'>({', '.join(concepts)})</span>"
                if concepts
                else ""
            )
            label_html = f"• <b>{person}</b>: ${total_p:,.0f}{concept_str}"
        else:
            label_html = f"• <b>{person}</b>"

        c_txt, c_del = st.columns([0.85, 0.15], vertical_alignment="center")
        with c_txt:
            st.markdown(
                f"<div style='font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{label_html}</div>",
                unsafe_allow_html=True,
            )
        with c_del:
            if st.button("✕", key=f"del_p_{idx}"):
                st.session_state.participants.pop(idx)
                st.session_state.expenses = [
                    e for e in st.session_state.expenses if e["payer"] != person
                ]
                st.rerun()

if st.session_state.participants or st.session_state.expenses:
    if st.button("🗑️ Limpiar Todo", key="clean_all_btn"):
        st.session_state.participants = []
        st.session_state.expenses = []
        st.rerun()

# RESULTADOS AUTOMÁTICOS
if st.session_state.participants and st.session_state.expenses:
    st.write("---")
    date_str = datetime.now().strftime("%d/%m/%Y")
    st.markdown(
        f"<b>📊 Resumen de Cuentas: {event_name}</b> <small>({date_str})</small>",
        unsafe_allow_html=True,
    )

    num_people = len(st.session_state.participants)
    total_spent = sum(e["amount"] for e in st.session_state.expenses)
    per_person = total_spent / num_people

    balances = {p: 0.0 for p in st.session_state.participants}
    for e in st.session_state.expenses:
        balances[e["payer"]] += e["amount"]
    for p in balances:
        balances[p] -= per_person

    settlements = calculate_settlements(balances)

    # TARJETAS DE MÉTRICAS COMPACTAS
    st.markdown(
        f"""
        <div style="display: flex; gap: 6px; margin: 8px 0; width:100%;">
            <div style="flex:1; background:#FFFFFF; border:1px solid #E2E8F0; padding:8px 6px; border-radius:8px; text-align:center;">
                <div style="font-size:10px; color:#64748B; font-weight:800; text-transform:uppercase;">💰 Gasto Total</div>
                <div style="font-size:15px; font-weight:800; color:#1E293B; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${total_spent:,.2f}</div>
            </div>
            <div style="flex:1; background:#FFFFFF; border:1px solid #E2E8F0; padding:8px 6px; border-radius:8px; text-align:center;">
                <div style="font-size:10px; color:#64748B; font-weight:800; text-transform:uppercase;">🛒 Por Persona</div>
                <div style="font-size:15px; font-weight:800; color:#2563EB; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${per_person:,.2f}</div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # GRÁFICO DE TORTA
    if HAS_MATPLOTLIB:
        payer_totals = {}
        for exp in st.session_state.expenses:
            p = exp["payer"]
            payer_totals[p] = payer_totals.get(p, 0.0) + exp["amount"]

        if payer_totals and sum(payer_totals.values()) > 0:
            fig, ax = plt.subplots(figsize=(4.0, 1.7))
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_facecolor("#FFFFFF")
            labels = list(payer_totals.keys())
            sizes = list(payer_totals.values())
            colors = [
                "#2563EB",
                "#10B981",
                "#F59E0B",
                "#EF4444",
                "#8B5CF6",
                "#EC4899",
                "#14B8A6",
                "#F97316",
            ]

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=colors[: len(labels)],
                textprops=dict(color="#334155", fontsize=8),
            )
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_weight("bold")

            ax.axis("equal")
            st.pyplot(fig)
            plt.close(fig)

    st.markdown("<b>👤 Balance por Integrante:</b>", unsafe_allow_html=True)
    for p in st.session_state.participants:
        bal = balances[p]
        paid = sum(
            e["amount"]
            for e in st.session_state.expenses
            if e["payer"] == p
        )

        if bal > 0.01:
            badge = f'<span class="badge-creditor">+${bal:,.2f}</span>'
        elif bal < -0.01:
            badge = f'<span class="badge-debtor">-${abs(bal):,.2f}</span>'
        else:
            badge = '<span class="badge-neutral">$0.00</span>'

        st.markdown(
            f"""
            <div class="flat-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    <b>{p}</b> <small style="color:#64748B;">(puso ${paid:,.0f})</small>
                </div>
                <div>{badge}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<b>💸 ¿Quién le paga a quién?</b>", unsafe_allow_html=True
    )

    wa_text = f"🎉 *EVENTO: {event_name.upper()}*\n"
    wa_text += f"📅 *Fecha:* {date_str}\n\n"
    wa_text += f"💰 *Gasto Total:* ${total_spent:,.2f}\n"
    wa_text += f"👤 *Por Persona:* ${per_person:,.2f}\n\n"
    wa_text += "📝 *DETALLE DE COMPRAS:*\n"

    for exp in st.session_state.expenses:
        wa_text += (
            f"• {exp['payer']}: {exp['concept']} (${exp['amount']:,.2f})\n"
        )

    wa_text += "\n👉 *PAGOS A REALIZAR:*\n"

    if not settlements:
        st.success("🎉 ¡Todos aportaron lo mismo! Están a mano.")
        wa_text += "¡Todos a mano!\n"
    else:
        for debtor, creditor, amount in settlements:
            line = f"• *{debtor}* ➔ *{creditor}*: ${amount:,.2f}"
            st.markdown(
                f"""
                <div style="background:#EFF6FF; border-left:4px solid #2563EB; padding:6px 10px; border-radius:6px; margin-bottom:4px; font-size:13px; color:#1E293B; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    💳 <b>{debtor}</b> ➔ <b>{creditor}</b>: <b>${amount:,.2f}</b>
                </div>
            """,
                unsafe_allow_html=True,
            )
            wa_text += f"{line}\n"

    wa_text += "\n📲 *Armá y calculá los gastos de tu evento acá:*\n"
    wa_text += "https://cuentas-evento.streamlit.app"

    # ENLACES DE LOS BOTONES
    encoded_wa = urllib.parse.quote(wa_text)
    wa_url = f"https://wa.me/?text={encoded_wa}"

    pdf_bytes = generate_pdf(
        event_name,
        date_str,
        total_spent,
        per_person,
        st.session_state.expenses,
        balances,
        settlements,
    )
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_href = f"data:application/pdf;base64,{pdf_b64}"
    clean_filename = f"gastos_{event_name.lower().replace(' ', '_')}.pdf"

    # BOTONES CUADRADOS DE ACCIÓN CON LOGOS OFICIALES REALES
    st.markdown(
        f"""
        <div class="action-row-container">
            <a href="{wa_url}" target="_blank" class="btn-action-square" title="Compartir por WhatsApp">
                <img src="{WA_URI}" width="38" height="38" alt="WhatsApp">
            </a>
            <a href="{pdf_href}" download="{clean_filename}" class="btn-action-square" title="Descargar Reporte PDF">
                <img src="{ACROBAT_URI}" width="38" height="38" alt="Adobe Acrobat PDF">
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
