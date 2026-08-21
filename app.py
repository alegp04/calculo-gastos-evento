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

# --- ESTILOS CSS REFINADOS Y RESPONSIVOS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    *, *:before, *:after {
        box-sizing: border-box !important;
    }

    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }

    /* Margen superior para bajar el título una línea entera */
    .block-container {
        padding-top: 4.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }

    p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #0F172A !important;
    }

    /* Banner de Título */
    .hero-container {
        background-color: #1E293B !important;
        padding: 10px 14px;
        border-radius: 10px;
        color: #FFFFFF !important;
        text-align: center;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 17px !important;
        font-weight: 800 !important;
        margin: 0;
        color: #FFFFFF !important;
    }

    /* FORZAR FILAS HORIZONTALES EN CELULAR */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important;
        width: 100% !important;
    }

    div[data-testid="column"] {
        min-width: 0 !important;
    }

    /* Formulario compacto */
    div[data-testid="stForm"] {
        padding: 10px !important;
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }

    /* Botón Cargar Datos */
    div[data-testid="stForm"] button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        height: 42px !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
        cursor: pointer !important;
    }

    div[data-testid="stForm"] button *,
    div[data-testid="stForm"] button p,
    div[data-testid="stForm"] button span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 14px !important;
    }

    /* --- BOTONES CUADRADOS CON LOGOS LIMPIOS (WHATSAPP + ACROBAT) --- */
    
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stLinkButton"]) {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 20px !important;
        width: 100% !important;
        margin-top: 10px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stLinkButton"]) > div[data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        display: flex !important;
        justify-content: center !important;
    }

    /* Botón Cuadrado WhatsApp */
    div[data-testid="stLinkButton"] a {
        width: 60px !important;
        height: 60px !important;
        min-width: 60px !important;
        min-height: 60px !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 14px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06) !important;
        padding: 0 !important;
        text-decoration: none !important;
        overflow: hidden !important;
        cursor: pointer !important;
    }

    div[data-testid="stLinkButton"] a *,
    div[data-testid="stLinkButton"] a p,
    div[data-testid="stLinkButton"] a span {
        display: none !important;
    }

    div[data-testid="stLinkButton"] a::before {
        content: "" !important;
        display: block !important;
        width: 34px !important;
        height: 34px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2325D366'%3E%3Cpath d='M12.012 2c-5.506 0-9.989 4.478-9.99 9.984 0 1.763.459 3.486 1.332 5.003l-1.416 5.17 5.291-1.387c1.464.798 3.116 1.218 4.78 1.218h.004c5.506 0 9.989-4.478 9.99-9.984 0-2.669-1.038-5.177-2.925-7.064C17.19 3.039 14.68 2 12.012 2zm0 1.834c4.493 0 8.152 3.656 8.153 8.15 0 2.181-.849 4.232-2.39 5.773-1.54 1.541-3.591 2.39-5.77 2.39h-.003c-1.488 0-2.951-.397-4.228-1.149l-.303-.18-3.142.823.838-3.061-.197-.314a8.127 8.127 0 0 1-1.246-4.282c0-4.494 3.659-8.15 8.153-8.15zm-3.6 4.398c-.22 0-.582.083-.888.416-.305.333-1.165 1.137-1.165 2.774 0 1.637 1.192 3.218 1.358 3.44.166.222 2.348 3.585 5.688 5.027 2.773 1.198 3.337.96 3.947.904.61-.055 1.969-.804 2.247-1.58.277-.777.277-1.442.194-1.58-.083-.139-.305-.222-.638-.388-.333-.166-1.969-.971-2.274-1.082-.305-.111-.527-.166-.749.166-.222.333-.86 1.082-1.054 1.304-.194.222-.388.25-.721.083-.333-.166-1.406-.518-2.678-1.652-.99-.883-1.658-1.974-1.853-2.307-.194-.333-.021-.513.146-.679.15-.149.333-.388.5-.582.166-.194.222-.333.333-.555.111-.222.055-.416-.028-.582-.083-.166-.749-1.803-1.026-2.468-.27-.648-.545-.56-.749-.57-.194-.01-.416-.01-.638-.01z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
    }

    div[data-testid="stLinkButton"] a:hover {
        border-color: #25D366 !important;
        background-color: #F0FDF4 !important;
    }

    /* Botón Cuadrado PDF Acrobat */
    .stDownloadButton button {
        width: 60px !important;
        height: 60px !important;
        min-width: 60px !important;
        min-height: 60px !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 14px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06) !important;
        padding: 0 !important;
        overflow: hidden !important;
        cursor: pointer !important;
    }

    .stDownloadButton button *,
    .stDownloadButton button p,
    .stDownloadButton button span {
        display: none !important;
    }

    .stDownloadButton button::before {
        content: "" !important;
        display: block !important;
        width: 34px !important;
        height: 34px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23E1251B'%3E%3Cpath d='M19.36 2.72H4.64A1.92 1.92 0 0 0 2.72 4.64v14.72a1.92 1.92 0 0 0 1.92 1.92h14.72a1.92 1.92 0 0 0 1.92-1.92V4.64a1.92 1.92 0 0 0-1.92-1.92zm-5.06 13.91c-.88-.88-2.02-2.31-3.15-4.04-1.29 2.65-2.66 4.31-3.69 4.31-.5 0-.82-.32-.82-.82 0-1.14 1.78-3.68 4.24-7.07-.58-1.89-.92-3.69-.92-4.88 0-.93.38-1.47 1.01-1.47.53 0 .88.38.88.94 0 1.34-.41 2.97-.99 4.58 1.63 2.14 3.28 3.65 4.54 4.33 1.57-.68 3.02-1.18 3.98-1.18.66 0 1.04.38 1.04.9 0 .86-1.39 1.76-3.17 2.16a18.23 18.23 0 0 1-2.95 2.24z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
    }

    .stDownloadButton button:hover {
        border-color: #E1251B !important;
        background-color: #FEF2F2 !important;
    }

    /* Inputs de Texto */
    input[type="text"], input[type="number"], div[data-baseweb="input"] {
        font-size: 13px !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    div[data-baseweb="input"] input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* Botón Limpiar Todo */
    div[class*="st-key-clean_all_btn"] button {
        background-color: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        color: #64748B !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        height: 34px !important;
        min-height: 34px !important;
        width: 100% !important;
        box-shadow: none !important;
        margin-top: 6px !important;
    }

    div[class*="st-key-clean_all_btn"] button *,
    div[class*="st-key-clean_all_btn"] button p,
    div[class*="st-key-clean_all_btn"] button span {
        color: #64748B !important;
        font-weight: 600 !important;
    }

    /* Cruz eliminar en la lista */
    div[class*="st-key-del_p_"] {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }

    div[class*="st-key-del_p_"] button,
    div[class*="st-key-del_p_"] button * {
        background: transparent !important;
        border: none !important;
        color: #94A3B8 !important;
        padding: 0px !important;
        margin: 0px !important;
        width: 24px !important;
        height: 24px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
        box-shadow: none !important;
    }

    div[class*="st-key-del_p_"] button:hover {
        color: #EF4444 !important;
    }

    /* Tarjetas de Resultados */
    .flat-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px;
        padding: 8px 10px !important;
        margin-bottom: 4px !important;
        color: #0F172A !important;
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

# Botones PWA / Compartir App
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
    <div style="display: flex; gap: 6px; font-family: sans-serif;">
        <button id="install-pwa-btn" onclick="installPWA()" style="display:none; flex: 1; background:#0D9488; color:white; border:none; padding:5px; border-radius:6px; font-weight:600; cursor:pointer; font-size:11px;">
            📲 Instalar App
        </button>
        <button id="share-app-btn" onclick="shareApp()" style="flex: 1; background:#475569; color:white; border:none; padding:5px; border-radius:6px; font-weight:600; cursor:pointer; font-size:11px;">
            🔗 Compartir App
        </button>
    </div>
""",
    height=34,
)

# Fecha y Evento LADO A LADO EN CELULAR
col_date, col_name = st.columns([1, 1.2], vertical_alignment="center")
with col_date:
    event_date = st.date_input("📅 Fecha:", datetime.now())
with col_name:
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

        c_txt, c_del = st.columns([0.88, 0.12], vertical_alignment="center")
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

# RESULTADOS AUTOMÁTICOS Y REACTIVOS
if st.session_state.participants and st.session_state.expenses:
    st.write("---")
    date_str = event_date.strftime("%d/%m/%Y")
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

    # BOTONES CUADRADOS LADO A LADO CON LOGOS VECTORIALES
    col_wa, col_pdf = st.columns(2)

    with col_wa:
        encoded_wa = urllib.parse.quote(wa_text)
        wa_url = f"https://wa.me/?text={encoded_wa}"
        st.link_button(
            "WA", wa_url, use_container_width=False
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
            label="PDF",
            data=pdf_bytes,
            file_name=f"gastos_{event_name.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
