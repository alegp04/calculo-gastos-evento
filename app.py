from datetime import datetime
import io
import re
import urllib.parse
from fpdf import FPDF
import streamlit as st

# Configuración de Matplotlib sin interfaz gráfica para alta velocidad
import matplotlib

matplotlib.use("Agg")
try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Cálculo de Gastos de Evento",
    page_icon="🎉",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        padding: 22px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
    }
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 13px;
        color: #E0E7FF;
        margin-top: 4px;
    }
    
    .flat-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .guide-card {
        background-color: #EEF2FF;
        border: 1px dashed #A5B4FC;
        border-radius: 12px;
        padding: 16px;
        margin-top: 20px;
        color: #312E81;
    }

    .badge-debtor {
        background-color: #FEF2F2;
        color: #EF4444;
        border: 1px solid #FCA5A5;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
    }
    .badge-creditor {
        background-color: #ECFDF5;
        color: #10B981;
        border: 1px solid #6EE7B7;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
    }
    .badge-neutral {
        background-color: #F1F5F9;
        color: #64748B;
        border: 1px solid #CBD5E1;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
    }
    
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        background-color: #4F46E5;
        color: white;
        border: none;
        padding: 12px 16px;
    }
    .stButton > button:hover {
        background-color: #4338CA;
        color: white;
    }

    /* Estilo para selector de pestañas navegable */
    div[data-testid="stRadio"] > div {
        display: flex;
        gap: 8px;
        background-color: #E2E8F0;
        padding: 6px;
        border-radius: 12px;
        margin-bottom: 16px;
    }
    div[data-testid="stRadio"] label {
        flex: 1;
        text-align: center;
        background-color: transparent;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 600;
        color: #475569;
        cursor: pointer;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none;
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

TAB_OPTIONS = ["⚡ 1. Cargar Gastos y Personas", "📊 2. Cuentas & PDF"]

if "tab_selector" not in st.session_state:
    st.session_state.tab_selector = TAB_OPTIONS[0]


def go_to_results():
    st.session_state.tab_selector = TAB_OPTIONS[1]


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


# --- GENERADOR DE PDF DETALLADO ---
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

    # Encabezado
    _ = pdf.set_font("Helvetica", "B", 16)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(
        0,
        10,
        clean_txt(f"GASTOS DE EVENTO: {event_name.upper()}"),
        ln=True,
        align="C",
    )

    _ = pdf.set_font("Helvetica", "", 10)
    _ = pdf.set_text_color(100, 116, 139)
    _ = pdf.cell(
        0,
        6,
        clean_txt(
            f"Fecha: {event_date_str} | Reporte de Gastos y Transferencias"
        ),
        ln=True,
        align="C",
    )
    _ = pdf.ln(4)

    # Cuadro de Métricas
    _ = pdf.set_fill_color(238, 242, 255)
    _ = pdf.rect(10, 32, 190, 14, "F")
    _ = pdf.set_y(35)
    _ = pdf.set_font("Helvetica", "B", 11)
    _ = pdf.set_text_color(49, 46, 129)
    _ = pdf.cell(95, 8, clean_txt(f"  Gasto Total: ${total_spent:,.2f}"), align="L")
    _ = pdf.cell(
        95,
        8,
        clean_txt(f"Total por Persona: ${per_person:,.2f}  "),
        align="R",
        ln=True,
    )
    _ = pdf.ln(4)

    # Gráfico circular para el PDF
    if HAS_MATPLOTLIB:
        payer_totals = {}
        for exp in expenses:
            p = exp["payer"]
            payer_totals[p] = payer_totals.get(p, 0.0) + exp["amount"]

        if payer_totals and sum(payer_totals.values()) > 0:
            fig, ax = plt.subplots(figsize=(4.5, 2.3))
            labels = [clean_txt(k) for k in payer_totals.keys()]
            sizes = list(payer_totals.values())
            colors = [
                "#4F46E5",
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
                fontsize=10,
                fontweight="bold",
                color="#1E293B",
                pad=6,
            )

            img_buf = io.BytesIO()
            _ = plt.savefig(
                img_buf, format="png", bbox_inches="tight", dpi=140
            )
            _ = plt.close(fig)
            _ = img_buf.seek(0)

            _ = pdf.image(img_buf, x=55, w=100)
            _ = pdf.ln(2)

    # 1. Tabla Gastos
    _ = pdf.set_font("Helvetica", "B", 11)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 7, clean_txt("1. Detalle de los Gastos Cargados"), ln=True)

    _ = pdf.set_font("Helvetica", "B", 9)
    _ = pdf.set_fill_color(79, 70, 229)
    _ = pdf.set_text_color(255, 255, 255)
    _ = pdf.cell(50, 6, clean_txt(" Comprador"), border=0, fill=True)
    _ = pdf.cell(95, 6, clean_txt(" Concepto / Item"), border=0, fill=True)
    _ = pdf.cell(
        45,
        6,
        clean_txt(" Monto ($) "),
        border=0,
        fill=True,
        align="R",
        ln=True,
    )

    _ = pdf.set_font("Helvetica", "", 9)
    _ = pdf.set_text_color(51, 65, 85)
    fill = False
    for exp in expenses:
        if fill:
            _ = pdf.set_fill_color(248, 250, 252)
        else:
            _ = pdf.set_fill_color(255, 255, 255)
        _ = pdf.cell(
            50, 6, clean_txt(f" {exp['payer']}"), border="B", fill=fill
        )
        _ = pdf.cell(
            95, 6, clean_txt(f" {exp['concept']}"), border="B", fill=fill
        )
        _ = pdf.cell(
            45,
            6,
            clean_txt(f"${exp['amount']:,.2f} "),
            border="B",
            fill=fill,
            align="R",
            ln=True,
        )
        fill = not fill

    _ = pdf.ln(4)

    # 2. Balances
    _ = pdf.set_font("Helvetica", "B", 11)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 7, clean_txt("2. Estado de Cuentas por Persona"), ln=True)

    _ = pdf.set_font("Helvetica", "B", 9)
    _ = pdf.set_fill_color(79, 70, 229)
    _ = pdf.set_text_color(255, 255, 255)
    _ = pdf.cell(50, 6, clean_txt(" Persona"), border=0, fill=True)
    _ = pdf.cell(45, 6, clean_txt(" Pago Realizado"), border=0, fill=True, align="R")
    _ = pdf.cell(
        45, 6, clean_txt(" Le Correspondia"), border=0, fill=True, align="R"
    )
    _ = pdf.cell(
        50,
        6,
        clean_txt(" Balance "),
        border=0,
        fill=True,
        align="R",
        ln=True,
    )

    _ = pdf.set_font("Helvetica", "", 9)
    _ = pdf.set_text_color(51, 65, 85)
    fill = False
    for person, bal in balances.items():
        paid = sum(e["amount"] for e in expenses if e["payer"] == person)
        if fill:
            _ = pdf.set_fill_color(248, 250, 252)
        else:
            _ = pdf.set_fill_color(255, 255, 255)

        if bal > 0.01:
            status = f"+${bal:,.2f} (A favor)"
        elif bal < -0.01:
            status = f"-${abs(bal):,.2f} (Debe)"
        else:
            status = "$0.00 (A mano)"

        _ = pdf.cell(50, 6, clean_txt(f" {person}"), border="B", fill=fill)
        _ = pdf.cell(
            45, 6, clean_txt(f"${paid:,.2f} "), border="B", fill=fill, align="R"
        )
        _ = pdf.cell(
            45,
            6,
            clean_txt(f"${per_person:,.2f} "),
            border="B",
            fill=fill,
            align="R",
        )
        _ = pdf.cell(
            50,
            6,
            clean_txt(f"{status} "),
            border="B",
            fill=fill,
            align="R",
            ln=True,
        )
        fill = not fill

    _ = pdf.ln(4)

    # 3. Transferencias
    _ = pdf.set_font("Helvetica", "B", 11)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 7, clean_txt("3. Pagos / Transferencias a Realizar"), ln=True)

    if not settlements:
        _ = pdf.set_font("Helvetica", "I", 9)
        _ = pdf.cell(
            0,
            6,
            clean_txt("Todos aportaron la misma cantidad. No hay deudas."),
            ln=True,
        )
    else:
        _ = pdf.set_font("Helvetica", "", 9)
        for debtor, creditor, amount in settlements:
            _ = pdf.set_fill_color(241, 245, 249)
            _ = pdf.cell(
                0,
                7,
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
        <div class="hero-title">🎉 Cálculo de Gastos de Evento</div>
        <div class="hero-subtitle">Dividí gastos entre amigos fácil y rápido</div>
    </div>
""",
    unsafe_allow_html=True,
)

# Guía para pantalla de inicio
with st.expander(
    "📲 ¿Cómo agregar esta App a la pantalla de inicio de tu celular?"
):
    st.markdown(
        """
        - **En iPhone (Safari):** Tocá el botón **Compartir** (cuadrado con flecha hacia arriba) y elegí **"Agregar a inicio"**.
        - **En Android (Chrome):** Tocá los **tres puntos** arriba a la derecha y elegí **"Agregar a la pantalla principal"**.
    """
    )

# Selector de pestañas dinámico
st.radio(
    "Navegación",
    options=TAB_OPTIONS,
    horizontal=True,
    label_visibility="collapsed",
    key="tab_selector",
)

# -----------------------------------------------------------------------------
# PESTAÑA 1: CARGA UNIFICADA
# -----------------------------------------------------------------------------
if st.session_state.tab_selector == "⚡ 1. Cargar Gastos y Personas":
    st.write("### 🎈 Datos del Evento")
    col_e1, col_e2 = st.columns([2, 1])

    with col_e1:
        event_name = st.text_input(
            "Nombre del Evento:",
            value=st.session_state.get("event_name", "Asado con Amigos"),
            placeholder="Ej: Asado, Topopeña, Cumple de Juan...",
            key="input_event_name",
        )
        st.session_state.event_name = event_name

    with col_e2:
        event_date = st.date_input(
            "Fecha:",
            st.session_state.get("event_date", datetime.now()),
            key="input_event_date",
        )
        st.session_state.event_date = event_date

    st.write("---")
    st.write("### ⚡ Carga Inteligente")

    with st.form("smart_input_form", clear_on_submit=True):
        user_input = st.text_input(
            "Escribí acá:",
            placeholder="Ej: Nico | Nico 15000 Carne | Sofi 4500 Bebidas",
            label_visibility="collapsed",
        )
        submit_btn = st.form_submit_button(
            "🚀 Cargar Datos", use_container_width=True
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
                    st.toast(
                        f"¡Gasto registrado! {name}: ${amount:,.2f} ({concept})"
                    )
                    st.rerun()
                else:
                    st.error("El monto debe ser mayor a 0.")
            else:
                name = raw_text.capitalize()
                if name not in st.session_state.participants:
                    st.session_state.participants.append(name)
                    st.toast(f"¡{name} agregado a la mesa!")
                    st.rerun()
                else:
                    st.info(f"{name} ya está en la lista.")

    col_p, col_g = st.columns(2)

    with col_p:
        st.write(
            f"**👤 Personas ({len(st.session_state.participants)}):**"
        )
        if not st.session_state.participants:
            st.caption("No hay participantes cargados.")
        for idx, name in enumerate(st.session_state.participants):
            c_txt, c_del = st.columns([4, 1])
            c_txt.write(f"• {name}")
            if c_del.button("❌", key=f"del_p_{idx}"):
                st.session_state.participants.pop(idx)
                st.session_state.expenses = [
                    e
                    for e in st.session_state.expenses
                    if e["payer"] != name
                ]
                st.rerun()

    with col_g:
        st.write(f"**🛒 Gastos ({len(st.session_state.expenses)}):**")
        if not st.session_state.expenses:
            st.caption("No hay gastos cargados.")
        for idx, exp in enumerate(st.session_state.expenses):
            c_txt, c_del = st.columns([4, 1])
            c_txt.write(f"• {exp['payer']}: ${exp['amount']:,.0f}")
            if c_del.button("🗑️", key=f"del_e_{idx}"):
                st.session_state.expenses.pop(idx)
                st.rerun()

    if st.session_state.participants or st.session_state.expenses:
        if st.button("🗑️ Limpiar Todo", use_container_width=True):
            st.session_state.participants = []
            st.session_state.expenses = []
            st.rerun()

    st.markdown(
        """
        <div class="guide-card">
            <b>💡 ¿Cómo usar la carga inteligente?</b>
            <ul style="margin-top: 8px; margin-bottom: 0px; padding-left: 20px;">
                <li><b>Para sumar una persona:</b> Escribí solo el nombre.<br><i>Ejemplo: <code>Nico</code></i></li>
                <li><b>Para cargar un gasto con concepto:</b> Escribí Nombre + Monto + Concepto.<br><i>Ejemplo: <code>Juan 18000 Carne y achuras</code></i></li>
                <li><b>Para cargar un gasto rápido:</b> Escribí Nombre + Monto.<br><i>Ejemplo: <code>Pedro 5000</code></i></li>
            </ul>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # BOTÓN VISIBLE FUNCIONAL
    st.write("---")
    st.button(
        "🚀 Continuar a Resultados ➔",
        key="btn_continue_to_results",
        on_click=go_to_results,
        use_container_width=True,
    )

# -----------------------------------------------------------------------------
# PESTAÑA 2: RESULTADOS Y EXPORTACIÓN
# -----------------------------------------------------------------------------
elif st.session_state.tab_selector == "📊 2. Cuentas & PDF":
    event_name = st.session_state.get("event_name", "Asado con Amigos")
    event_date = st.session_state.get("event_date", datetime.now())
    date_str = event_date.strftime("%d/%m/%Y")

    st.subheader(f"Balances: {event_name}")
    st.caption(f"📅 Fecha del evento: {date_str}")

    if not st.session_state.participants or not st.session_state.expenses:
        st.info("💡 Ingresá personas y gastos en la pestaña 1 para ver el resumen.")
    else:
        num_people = len(st.session_state.participants)
        total_spent = sum(e["amount"] for e in st.session_state.expenses)
        per_person = total_spent / num_people

        balances = {p: 0.0 for p in st.session_state.participants}
        for e in st.session_state.expenses:
            balances[e["payer"]] += e["amount"]
        for p in balances:
            balances[p] -= per_person

        settlements = calculate_settlements(balances)

        m1, m2 = st.columns(2)
        m1.metric("Gasto Total", f"${total_spent:,.2f}")
        m2.metric("Total por Persona", f"${per_person:,.2f}")

        # Gráfico visual en pantalla
        if HAS_MATPLOTLIB:
            payer_totals = {}
            for exp in st.session_state.expenses:
                p = exp["payer"]
                payer_totals[p] = payer_totals.get(p, 0.0) + exp["amount"]

            if payer_totals and sum(payer_totals.values()) > 0:
                fig, ax = plt.subplots(figsize=(5, 2.5))
                labels = list(payer_totals.keys())
                sizes = list(payer_totals.values())
                colors = [
                    "#4F46E5",
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
                    textprops=dict(color="#334155", fontsize=9),
                )
                for autotext in autotexts:
                    _ = autotext.set_color("white")
                    _ = autotext.set_weight("bold")

                _ = ax.axis("equal")
                _ = plt.title(
                    "Distribución del Gasto",
                    fontsize=11,
                    fontweight="bold",
                    color="#1E293B",
                )
                st.pyplot(fig)
                plt.close(fig)

        st.write("---")

        st.write("### 👤 Estado por Persona")
        for p in st.session_state.participants:
            bal = balances[p]
            paid = sum(
                e["amount"]
                for e in st.session_state.expenses
                if e["payer"] == p
            )

            if bal > 0.01:
                badge = f'<span class="badge-creditor">+${bal:,.2f} (A favor)</span>'
            elif bal < -0.01:
                badge = f'<span class="badge-debtor">-${abs(bal):,.2f} (Debe)</span>'
            else:
                badge = '<span class="badge-neutral">$0.00 (A mano)</span>'

            st.markdown(
                f"""
                <div class="flat-card" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <b>{p}</b><br>
                        <small style="color:#64748B;">Puso ${paid:,.2f} de ${per_person:,.2f}</small>
                    </div>
                    <div>{badge}</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.write("---")
        st.write("### 🔄 ¿Quién le transfiere a quién?")

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
            wa_text += "¡Todos a mano!"
        else:
            for debtor, creditor, amount in settlements:
                line = f"• *{debtor}* ➔ *{creditor}*: ${amount:,.2f}"
                st.markdown(
                    f"""
                    <div style="background:#EEF2FF; border-left:4px solid #4F46E5; padding:12px; border-radius:8px; margin-bottom:8px;">
                        💳 <b>{debtor}</b> le transfiere a <b>{creditor}</b>: 
                        <span style="color:#4F46E5; font-weight:700;">${amount:,.2f}</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
                wa_text += f"{line}\n"

        st.write("---")

        col_wa, col_pdf = st.columns(2)

        with col_wa:
            encoded_wa = urllib.parse.quote(wa_text)
            wa_url = f"https://wa.me/?text={encoded_wa}"
            st.link_button(
                "Compartir en WhatsApp 📱", wa_url, use_container_width=True
            )

        with col_pdf:
            pdf_bytes = generate_pdf(
                event_name,
                date_str,
                total_spent,
                per_person,
                st.session_state.expenses,
                balances,
                settlements,
            )
            st.download_button(
                label="Descargar PDF Detallado 📄",
                data=pdf_bytes,
                file_name=f"gastos_{event_name.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )