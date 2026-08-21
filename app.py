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

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Forzar fondo claro */
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }

    p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #0F172A !important;
    }

    /* Banner de Título */
    .hero-container {
        background: linear-gradient(135deg, #0284C7 0%, #0D9488 100%);
        padding: 12px 16px;
        border-radius: 12px;
        color: white !important;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .hero-title {
        font-size: 20px !important;
        font-weight: 700 !important;
        margin: 0;
        color: #FFFFFF !important;
        letter-spacing: -0.3px;
    }
    
    /* Tarjetas Compactas */
    .flat-card {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    
    .flat-card, .flat-card b, .flat-card span, .flat-card small, .flat-card div {
        color: #0F172A !important;
    }
    
    /* Badges de Estado */
    .badge-debtor {
        background-color: #FEF2F2 !important;
        color: #EF4444 !important;
        border: 1px solid #FCA5A5 !important;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-creditor {
        background-color: #ECFDF5 !important;
        color: #10B981 !important;
        border: 1px solid #6EE7B7 !important;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-neutral {
        background-color: #F1F5F9 !important;
        color: #64748B !important;
        border: 1px solid #CBD5E1 !important;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
    }
    
    /* Botón Principal */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border: none !important;
        padding: 8px 14px !important;
    }
    .stButton > button:hover {
        background-color: #0369A1 !important;
        color: #FFFFFF !important;
    }

    /* Estilo para los botones de eliminar (íconos chiquitos y discretos) */
    div[data-testid="column"] div.stButton > button {
        background-color: transparent !important;
        border: 1px solid #E2E8F0 !important;
        color: #EF4444 !important;
        padding: 2px 6px !important;
        min-height: 28px !important;
        height: 28px !important;
        font-size: 12px !important;
        border-radius: 6px !important;
        margin-top: 2px;
    }
    div[data-testid="column"] div.stButton > button:hover {
        background-color: #FEF2F2 !important;
        border-color: #FCA5A5 !important;
    }

    /* Campos de Entrada */
    input[type="text"], input[type="number"] {
        border-radius: 8px !important;
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
if "show_results" not in st.session_state:
    st.session_state.show_results = False


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

    # Encabezado
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

    # Métricas
    _ = pdf.set_fill_color(240, 249, 255)
    _ = pdf.rect(10, 30, 190, 12, "F")
    _ = pdf.set_y(32)
    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(2, 132, 199)
    _ = pdf.cell(95, 7, clean_txt(f"  Gasto Total: ${total_spent:,.2f}"), align="L")
    _ = pdf.cell(
        95,
        7,
        clean_txt(f"Total por Persona: ${per_person:,.2f}  "),
        align="R",
        ln=True,
    )
    _ = pdf.ln(3)

    # Gráfico circular
    if HAS_MATPLOTLIB:
        payer_totals = {}
        for exp in expenses:
            p = exp["payer"]
            payer_totals[p] = payer_totals.get(p, 0.0) + exp["amount"]

        if payer_totals and sum(payer_totals.values()) > 0:
            fig, ax = plt.subplots(figsize=(4.2, 2.0))
            fig.patch.set_facecolor("#FFFFFF")
            labels = [clean_txt(k) for k in payer_totals.keys()]
            sizes = list(payer_totals.values())
            colors = [
                "#0284C7",
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
                img_buf, format="png", bbox_inches="tight", dpi=130, facecolor=fig.get_facecolor()
            )
            _ = plt.close(fig)
            _ = img_buf.seek(0)

            _ = pdf.image(img_buf, x=60, w=90)
            _ = pdf.ln(2)

    # 1. Tabla Gastos
    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 6, clean_txt("1. Detalle de los Gastos Cargados"), ln=True)

    _ = pdf.set_font("Helvetica", "B", 8)
    _ = pdf.set_fill_color(2, 132, 199)
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

    # 2. Balances
    _ = pdf.set_font("Helvetica", "B", 10)
    _ = pdf.set_text_color(30, 41, 59)
    _ = pdf.cell(0, 6, clean_txt("2. Estado de Cuentas por Persona"), ln=True)

    _ = pdf.set_font("Helvetica", "B", 8)
    _ = pdf.set_fill_color(2, 132, 199)
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

    # 3. Transferencias
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


# --- INTERFAZ DE USUARIO ---

st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🎉 Cálculo de Gastos de Evento</div>
    </div>
""",
    unsafe_allow_html=True,
)

components.html(
    """
    <script>
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        const btn = document.getElementById('install-pwa-btn');
        if(btn) btn.style.display = 'block';
    });
    function installPWA() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                deferredPrompt = null;
            });
        } else {
            alert("Para instalar: tocá 'Compartir' en iPhone (Agregar a inicio) o los 3 puntos en Android (Instalar Aplicación).");
        }
    }
    function shareApp() {
        const shareData = {
            title: 'Cálculo de Gastos de Evento',
            text: '¡Usá esta app para dividir y calcular los gastos de nuestro evento!',
            url: window.top ? window.top.location.href : window.location.href
        };
        if (navigator.share) {
            navigator.share(shareData).catch((err) => console.log(err));
        } else {
            navigator.clipboard.writeText(shareData.url);
            alert('¡Link de la app copiado al portapapeles!');
        }
    }
    </script>
    <div style="display: flex; gap: 8px; font-family: sans-serif;">
        <button id="install-pwa-btn" onclick="installPWA()" style="display:none; flex: 1; background:#10B981; color:white; border:none; padding:8px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:13px;">
            📲 Instalar App
        </button>
        <button id="share-app-btn" onclick="shareApp()" style="flex: 1; background:#0284C7; color:white; border:none; padding:8px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:13px;">
            🔗 Compartir App
        </button>
    </div>
""",
    height=42,
)

col_date, col_name = st.columns([1, 2])
with col_date:
    event_date = st.date_input("Fecha:", datetime.now())
with col_name:
    event_name = st.text_input(
        "Nombre del Evento:",
        value="Asado con Amigos",
        placeholder="Ej: Topopeña, Cumple...",
    )

with st.form("smart_input_form", clear_on_submit=True):
    col_in, col_btn = st.columns([3, 1])
    with col_in:
        user_input = st.text_input(
            "Ingreso rápido:",
            placeholder="Ej: Nico | Nico 15000 Carne",
            label_visibility="collapsed",
        )
    with col_btn:
        submit_btn = st.form_submit_button(
            "🚀 Cargar", use_container_width=True
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
                    f"¡Registrado! {name}: ${amount:,.2f} ({concept})"
                )
                st.session_state.show_results = True
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

with st.expander("❓ ¿Cómo cargar datos? (Ver ejemplos)"):
    st.markdown(
        """
        - **Sumar participante sin gasto:** Escribí solo el nombre (`Nico`).
        - **Gasto completo:** Nombre + Monto + Detalle (`Juan 18000 Carne`).
        - **Gasto sin detalle:** Nombre + Monto (`Pedro 5000`).
    """
    )

# SECCIÓN 3: LISTADO COMPACTO DE PERSONAS Y GASTOS
col_p, col_g = st.columns(2)

with col_p:
    st.markdown(
        f"<b>👤 Personas ({len(st.session_state.participants)}):</b>",
        unsafe_allow_html=True,
    )
    if not st.session_state.participants:
        st.caption("Sin participantes.")
    for idx, name in enumerate(st.session_state.participants):
        c_txt, c_del = st.columns([5, 1])
        c_txt.write(f"• {name}")
        if c_del.button("✕", key=f"del_p_{idx}"):
            st.session_state.participants.pop(idx)
            st.session_state.expenses = [
                e
                for e in st.session_state.expenses
                if e["payer"] != name
            ]
            st.rerun()

with col_g:
    st.markdown(
        f"<b>🛒 Gastos ({len(st.session_state.expenses)}):</b>",
        unsafe_allow_html=True,
    )
    if not st.session_state.expenses:
        st.caption("Sin gastos.")
    for idx, exp in enumerate(st.session_state.expenses):
        c_txt, c_del = st.columns([5, 1])
        c_txt.write(f"• {exp['payer']}: ${exp['amount']:,.0f}")
        if c_del.button("✕", key=f"del_e_{idx}"):
            st.session_state.expenses.pop(idx)
            st.rerun()

if st.session_state.participants or st.session_state.expenses:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Limpiar Todo", key="clean_all_btn"):
        st.session_state.participants = []
        st.session_state.expenses = []
        st.session_state.show_results = False
        st.rerun()

st.write("---")

# SECCIÓN 4: BOTÓN "CALCULAR CUENTAS"
if st.button("🚀 Calcular Cuentas / Ver Resultados", use_container_width=True):
    st.session_state.show_results = True

# SECCIÓN 5: RESULTADOS
if st.session_state.show_results:
    if not st.session_state.participants or not st.session_state.expenses:
        st.warning("⚠️ Cargá al menos una persona y un gasto para ver el cálculo.")
    else:
        date_str = event_date.strftime("%d/%m/%Y")
        st.markdown(
            f"### 📊 Balances: {event_name} <small>({date_str})</small>",
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

        m1, m2 = st.columns(2)
        m1.metric("Gasto Total", f"${total_spent:,.2f}")
        m2.metric("Por Persona", f"${per_person:,.2f}")

        # Gráfico visual en pantalla
        if HAS_MATPLOTLIB:
            payer_totals = {}
            for exp in st.session_state.expenses:
                p = exp["payer"]
                payer_totals[p] = payer_totals.get(p, 0.0) + exp["amount"]

            if payer_totals and sum(payer_totals.values()) > 0:
                fig, ax = plt.subplots(figsize=(4.5, 2.0))
                fig.patch.set_facecolor("#FFFFFF")
                labels = list(payer_totals.keys())
                sizes = list(payer_totals.values())
                colors = [
                    "#0284C7",
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

        st.markdown("<b>👤 Estado por Persona:</b>", unsafe_allow_html=True)
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
                    <div>
                        <b>{p}</b> <small style="color:#64748B;">(puso ${paid:,.0f})</small>
                    </div>
                    <div>{badge}</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "<b>🔄 ¿Quién le transfiere a quién?</b>", unsafe_allow_html=True
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
                    <div style="background:#E0F2FE; border-left:4px solid #0284C7; padding:8px 12px; border-radius:6px; margin-bottom:6px; font-size:14px; color:#0F172A;">
                        💳 <b>{debtor}</b> ➔ <b>{creditor}</b>: <b>${amount:,.2f}</b>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
                wa_text += f"{line}\n"

        wa_text += "\n📲 *Armá y calculá los gastos de tu evento acá:*\n"
        wa_text += "https://cuentas-evento.streamlit.app"

        col_wa, col_pdf = st.columns(2)

        with col_wa:
            encoded_wa = urllib.parse.quote(wa_text)
            wa_url = f"https://wa.me/?text={encoded_wa}"
            st.link_button(
                "WhatsApp 📱", wa_url, use_container_width=True
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
                label="Descargar PDF 📄",
                data=pdf_bytes,
                file_name=f"gastos_{event_name.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )