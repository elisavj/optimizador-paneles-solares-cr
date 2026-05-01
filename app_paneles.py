import streamlit as st
import pandas as pd
import altair as alt
from modelo_paneles import resolver_casa, PANELES, ENERGIA_DIARIA, ENERGIA_MENSUAL

st.set_page_config(
    page_title="Paneles Solares CR",
    page_icon="☀️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Tema rosado
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Fondo general */
    .stApp { background-color: #2d0018; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #3d0022; }
    [data-testid="stSidebar"] * { color: #f8bbd0 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #3d0022; border-radius: 10px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #f48fb1; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #880e4f !important; border-radius: 8px; color: #fff !important; }

    /* Texto general */
    .stApp, .stApp p, .stApp label, .stApp span, .stApp div { color: #f8bbd0; }

    /* Métricas */
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #f48fb1; }
    [data-testid="stMetricLabel"] { color: #f8bbd0; font-weight: 600; }
    [data-testid="metric-container"] {
        background-color: #4a0028;
        border: 1px solid #880e4f;
        border-radius: 12px;
        padding: 14px 18px;
    }

    /* Títulos */
    h1, h2, h3 { color: #f48fb1 !important; }

    /* Botón */
    .stButton > button {
        background-color: #880e4f;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        transition: background 0.2s;
    }
    .stButton > button:hover { background-color: #ad1457; color: white; }

    /* Divisores */
    hr { border-color: #880e4f; }

    /* Cajas de info/success */
    .stSuccess { background-color: #4a0028 !important; border-left: 4px solid #f48fb1 !important; color: #f8bbd0 !important; }
    .stInfo    { background-color: #3d0022 !important; border-left: 4px solid #880e4f !important; color: #f8bbd0 !important; }
    .stWarning { background-color: #4a0028 !important; border-left: 4px solid #f48fb1 !important; }
    .stError   { background-color: #4a0028 !important; border-left: 4px solid #c2185b !important; }

    /* Inputs y selectores */
    .stNumberInput input, .stSlider { background-color: #4a0028 !important; color: #f8bbd0 !important; }
    [data-testid="stDataFrame"] { background-color: #3d0022; }

    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("☀️ Optimizador de Paneles Solares — Costa Rica")
st.caption("Modelo de Programación Lineal Entera · Minimiza inversión cubriendo demanda mensual")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Parámetros de entrada")

demanda = st.sidebar.number_input(
    "Consumo mensual (kWh/mes)", min_value=1.0, value=267.0, step=1.0,
    help="Dato de tu recibo eléctrico (ICE/CNFL)"
)
dias = st.sidebar.slider("Días del mes de referencia", 28, 31, 30)
area = st.sidebar.number_input(
    "Área del techo disponible (m²)", min_value=1.0, value=120.0, step=1.0
)
tarifa_colon = st.sidebar.number_input(
    "Tarifa eléctrica (₡/kWh)", min_value=1.0, value=55.0, step=1.0,
    help="Tarifa residencial CR. Ej: CNFL ≈ ₡55/kWh. Se convierte a USD automáticamente."
)
tipo_cambio = st.sidebar.number_input(
    "Tipo de cambio (₡/USD)", min_value=1.0, value=520.0, step=1.0,
    help="Tipo de cambio actual. Ej: ₡520 por dólar"
)
tarifa = tarifa_colon / tipo_cambio  # conversión interna a $/kWh

degradacion = st.sidebar.slider(
    "Degradación anual del panel (%)", min_value=0.0, max_value=2.0, value=0.5, step=0.1,
    help="Los paneles pierden ~0.5% de eficiencia por año. A los 25 años generan ~88% de su capacidad original."
)

st.sidebar.markdown("---")
optimizar = st.sidebar.button("🚀 Optimizar", use_container_width=True)

# ---------------------------------------------------------------------------
# Cálculo y estado de sesión
# ---------------------------------------------------------------------------
if optimizar:
    r = resolver_casa("Casa", demanda, area, dias_mes=dias)
    st.session_state["resultado"]    = r
    st.session_state["demanda"]      = demanda
    st.session_state["tarifa"]       = tarifa
    st.session_state["tarifa_colon"] = tarifa_colon
    st.session_state["tipo_cambio"]  = tipo_cambio
    st.session_state["degradacion"]  = degradacion
    st.session_state["area"]         = area

resultado    = st.session_state.get("resultado")
s_demanda    = st.session_state.get("demanda",      demanda)
s_tarifa     = st.session_state.get("tarifa",       tarifa)
tarifa_colon = st.session_state.get("tarifa_colon", tarifa_colon)
tipo_cambio  = st.session_state.get("tipo_cambio",  tipo_cambio)
degradacion  = st.session_state.get("degradacion",  degradacion)
s_area       = st.session_state.get("area",         area)

# Paleta rosada para gráficos
PINK_PALETTE = ["#e91e8c", "#f48fb1", "#ad1457", "#f8bbd0", "#880e4f"]

# ---------------------------------------------------------------------------
# Pestañas
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔧 Optimizador",
    "💰 Análisis Financiero",
    "⚡ Análisis Energético",
    "📋 Referencia de Paneles",
    "📐 Modelo Matemático",
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — OPTIMIZADOR
# ══════════════════════════════════════════════════════════════
with tab1:
    if resultado is None:
        st.info("Ingresá los parámetros en la barra lateral y presioná **Optimizar**.")
    elif resultado["estado"] != 1:
        st.error("❌ No se encontró solución factible. Revisá los parámetros.")
    else:
        r = resultado
        total_paneles = sum(r["paneles"].values())
        area_usada    = sum(PANELES[p]["area_m2"] * r["paneles"][p] for p in PANELES)
        excedente     = r["energia_kwh_mes"] - s_demanda
        cobertura_pct = (r["energia_kwh_mes"] / s_demanda * 100) if s_demanda > 0 else 0

        st.success(f"✅ Solución óptima encontrada — Inversión mínima: **${r['costo_usd']:,.2f} USD**")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Panel A (400 W)",  r["paneles"]["A"],
                    f"${PANELES['A']['costo_usd'] * r['paneles']['A']:,.0f} USD")
        col2.metric("Panel B (450 W)",  r["paneles"]["B"],
                    f"${PANELES['B']['costo_usd'] * r['paneles']['B']:,.0f} USD")
        col3.metric("Panel C (550 W)",  r["paneles"]["C"],
                    f"${PANELES['C']['costo_usd'] * r['paneles']['C']:,.0f} USD")

        st.markdown("---")
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        col_a.metric("Total paneles",      total_paneles)
        col_b.metric("Área utilizada",     f"{area_usada:.1f} m²",   f"de {s_area:.0f} m²")
        col_c.metric("Energía generada",   f"{r['energia_kwh_mes']:.1f} kWh/mes")
        col_d.metric("Excedente mensual",  f"{excedente:.1f} kWh")
        col_e.metric("Cobertura",          f"{cobertura_pct:.0f}%")

        st.markdown("---")
        st.markdown(
            f"**Interpretación:** La solución instala **{r['paneles']['A']} paneles A**, "
            f"**{r['paneles']['B']} paneles B** y **{r['paneles']['C']} paneles C**, "
            f"generando **{r['energia_kwh_mes']:.1f} kWh/mes** frente a una demanda de "
            f"**{s_demanda:.0f} kWh/mes** (**{cobertura_pct:.0f}%** cubierto), con una "
            f"inversión mínima de **${r['costo_usd']:,.2f} USD**."
        )

# ══════════════════════════════════════════════════════════════
# TAB 2 — ANÁLISIS FINANCIERO
# ══════════════════════════════════════════════════════════════
with tab2:
    if resultado is None:
        st.info("Optimizá primero desde la pestaña **Optimizador**.")
    elif resultado["estado"] != 1:
        st.warning("Sin solución factible.")
    else:
        r         = resultado
        VIDA_UTIL = 25
        tasa_deg  = degradacion / 100.0
        inversion = r["costo_usd"]
        gasto_mes = s_demanda * s_tarifa
        energia_base = r["energia_kwh_mes"]

        # Ahorro año a año con degradación compuesta
        ahorros_anuales = [
            energia_base * (1 - tasa_deg) ** (a - 1) * 12 * s_tarifa
            for a in range(1, VIDA_UTIL + 1)
        ]
        ahorro_mes   = energia_base * s_tarifa                  # año 1
        ahorro_ano   = ahorros_anuales[0]                       # año 1
        ahorro_25    = sum(ahorros_anuales)                      # total real degradado
        roi_25       = ((ahorro_25 - inversion) / inversion) * 100

        # Tiempo de recuperación con degradación (acumulado año a año)
        acum = 0.0
        retorno = float("inf")
        for i, a in enumerate(ahorros_anuales, start=1):
            acum += a
            if acum >= inversion:
                # interpolación lineal dentro del año
                exceso   = acum - inversion
                retorno  = i - exceso / a
                break

        # Año exacto para la línea vertical
        anio_eq = retorno if retorno != float("inf") else VIDA_UTIL

        st.subheader("💰 Resumen financiero")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Inversión inicial",        f"${inversion:,.2f}",  "Costo total paneles")
        col2.metric("Ahorro mensual estimado",  f"${ahorro_mes:,.2f}", f"vs ${gasto_mes:,.2f}/mes sin paneles")
        col3.metric("Ahorro anual estimado",    f"${ahorro_ano:,.2f}")

        st.markdown("---")
        col4, col5, col6 = st.columns(3)
        eficiencia_25 = (1 - tasa_deg) ** 24 * 100
        col4.metric("Vida útil paneles",        f"{VIDA_UTIL} años",
                    f"Eficiencia año 25: {eficiencia_25:.1f}%")
        col5.metric("Ahorro total en 25 años",  f"${ahorro_25:,.2f}",
                    "Con degradación real")
        col6.metric("Tiempo de recuperación",   
                    f"{retorno:.1f} años" if retorno != float("inf") else "No se recupera",
                    f"ROI 25 años: {roi_25:.0f}%")

        # ── Gráfico comparativa + punto de equilibrio ──
        st.markdown("---")
        st.subheader("📈 Ahorro acumulado vs costo acumulado sin paneles (25 años)")

        anos             = list(range(0, VIDA_UTIL + 1))
        # Ahorro acumulado real (con degradación)
        ahorro_acum = [0.0]
        for a in ahorros_anuales:
            ahorro_acum.append(ahorro_acum[-1] + a)
        # Sin paneles: gasto acumulado que se evita
        costo_sin_panel  = [gasto_mes * 12 * a for a in anos]
        inv_line         = [inversion] * len(anos)

        df_fin = pd.DataFrame({
            "Año":                         anos,
            "Ahorro acumulado (con panel)": ahorro_acum,
            "Costo acumulado sin paneles":  costo_sin_panel,
            "Inversión inicial":            inv_line,
        })
        df_melt = df_fin.melt("Año", var_name="Concepto", value_name="USD")

        line_chart = (
            alt.Chart(df_melt)
            .mark_line(strokeWidth=2.5)
            .encode(
                x=alt.X("Año:Q", title="Año"),
                y=alt.Y("USD:Q", title="USD", axis=alt.Axis(format="$,.0f")),
                color=alt.Color("Concepto:N", scale=alt.Scale(
                    domain=["Ahorro acumulado (con panel)", "Costo acumulado sin paneles", "Inversión inicial"],
                    range=["#e91e8c", "#f48fb1", "#ad1457"]
                )),
                tooltip=["Año:Q", "Concepto:N", alt.Tooltip("USD:Q", format="$,.2f")]
            )
            .properties(height=340)
        )

        # Línea vertical del punto de equilibrio
        eq_df   = pd.DataFrame({"Año": [anio_eq]})
        eq_rule = (
            alt.Chart(eq_df)
            .mark_rule(strokeDash=[6, 3], color="#880e4f", strokeWidth=2)
            .encode(x="Año:Q")
        )
        eq_text = (
            alt.Chart(eq_df)
            .mark_text(align="left", dx=6, dy=-120, color="#880e4f", fontSize=12, fontWeight="bold")
            .encode(x="Año:Q", text=alt.value(f"Recuperación: año {anio_eq:.1f}"))
        )

        st.altair_chart(line_chart + eq_rule + eq_text, use_container_width=True)

        st.caption(
            f"*Supuestos: tarifa fija de ₡{tarifa_colon:.0f}/kWh (≈${s_tarifa:.4f}/kWh al cambio ₡{tipo_cambio:.0f}), "
            f"degradación anual de **{degradacion:.1f}%** (eficiencia año 25: {eficiencia_25:.1f}%), "
            f"vida útil {VIDA_UTIL} años, sin mantenimiento significativo.*"
        )

        st.markdown("---")
        st.subheader("📅 Proyección anual detallada")
        tabla = pd.DataFrame({
            "Año":                           anos[1:],
            "Eficiencia (%)":                [f"{(1 - tasa_deg)**(a-1)*100:.1f}%" for a in anos[1:]],
            "Generación (kWh/mes)":          [f"{energia_base * (1 - tasa_deg)**(a-1):.1f}" for a in anos[1:]],
            "Ahorro anual (USD)":            [f"${a:,.2f}" for a in ahorros_anuales],
            "Ahorro acumulado (USD)":        [f"${v:,.2f}" for v in ahorro_acum[1:]],
            "Balance neto (USD)":            [f"${a - inversion:,.2f}" for a in ahorro_acum[1:]],
        })
        st.dataframe(tabla, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# TAB 3 — ANÁLISIS ENERGÉTICO
# ══════════════════════════════════════════════════════════════
with tab3:
    if resultado is None:
        st.info("Optimizá primero desde la pestaña **Optimizador**.")
    elif resultado["estado"] != 1:
        st.warning("Sin solución factible.")
    else:
        r             = resultado
        cobertura_pct = (r["energia_kwh_mes"] / s_demanda * 100) if s_demanda > 0 else 0
        excedente     = max(r["energia_kwh_mes"] - s_demanda, 0)
        deficit       = max(s_demanda - r["energia_kwh_mes"], 0)

        st.subheader("⚡ Cobertura energética")
        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Demanda mensual",    f"{s_demanda:.1f} kWh")
        col2.metric("Energía generada",   f"{r['energia_kwh_mes']:.1f} kWh")
        col3.metric("Cobertura",          f"{cobertura_pct:.1f}%",
                    "✅ Cubierta" if cobertura_pct >= 100 else f"⚠️ Déficit {deficit:.1f} kWh")
        col4.metric("Excedente mensual",  f"{excedente:.1f} kWh",
                    "Inyectable a la red (NetMetering)")

        # Barra de cobertura visual
        st.markdown("---")
        st.subheader("📊 Nivel de cobertura")
        pct_capped = min(cobertura_pct, 100)

        df_cob = pd.DataFrame({
            "Concepto": ["Cobertura", "Restante"],
            "Porcentaje": [pct_capped, max(100 - pct_capped, 0)]
        })
        pie_cob = (
            alt.Chart(df_cob)
            .mark_arc(innerRadius=70, outerRadius=130)
            .encode(
                theta="Porcentaje:Q",
                color=alt.Color("Concepto:N", scale=alt.Scale(
                    domain=["Cobertura", "Restante"],
                    range=["#e91e8c", "#fce4ec"]
                )),
                tooltip=["Concepto:N", alt.Tooltip("Porcentaje:Q", format=".1f")]
            )
            .properties(height=300, title=f"Cobertura: {cobertura_pct:.1f}%")
        )
        st.altair_chart(pie_cob, use_container_width=True)

        # Comparativa demanda vs generación
        st.markdown("---")
        st.subheader("📉 Demanda vs generación mensual")
        df_comp = pd.DataFrame({
            "Concepto":   ["Demanda", "Generación"],
            "kWh/mes":    [s_demanda, r["energia_kwh_mes"]],
        })
        bar_comp = (
            alt.Chart(df_comp)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Concepto:N", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("kWh/mes:Q", title="kWh/mes"),
                color=alt.Color("Concepto:N", scale=alt.Scale(
                    domain=["Demanda", "Generación"],
                    range=["#f48fb1", "#e91e8c"]
                ), legend=None),
                tooltip=["Concepto:N", alt.Tooltip("kWh/mes:Q", format=".2f")]
            )
            .properties(height=280)
        )
        st.altair_chart(bar_comp, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 4 — REFERENCIA DE PANELES
# ══════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📋 Especificaciones técnicas")
    st.markdown("---")

    cols = st.columns(3)
    for i, (tipo, datos) in enumerate(PANELES.items()):
        with cols[i]:
            e_dia = ENERGIA_DIARIA[tipo]
            e_mes = ENERGIA_MENSUAL[tipo]
            # paneles máximos que caben en el techo actual
            max_techo = int(s_area // datos["area_m2"])
            st.markdown(f"### Panel {tipo}")
            st.metric("Potencia",              f"{int(datos['potencia_kw']*1000)} W")
            st.metric("Área ocupada",          f"{datos['area_m2']} m²")
            st.metric("Costo unitario",        f"${datos['costo_usd']}")
            st.metric("Energía diaria",        f"{e_dia:.3f} kWh/día")
            st.metric("Energía mensual",       f"{e_mes:.2f} kWh/mes")
            st.metric("Máx. en tu techo",      f"{max_techo} paneles",
                       f"({datos['area_m2']} m² c/u · {s_area:.0f} m² disp.)")

    st.markdown("---")
    st.subheader("🔢 Parámetros del sistema")
    col1, col2 = st.columns(2)
    col1.metric("HSP Costa Rica", "4.5 h/día", "Horas Pico Solar")
    col2.metric("Fórmula",        "E = Pdc × HSP",  "Energía diaria por panel")

    st.markdown("---")
    st.subheader("📊 Comparativa de paneles")
    df_paneles = pd.DataFrame([
        {
            "Panel":                   f"Panel {t}",
            "Potencia (W)":            int(d["potencia_kw"] * 1000),
            "Área (m²)":               d["area_m2"],
            "Costo (USD)":             d["costo_usd"],
            "Energía diaria (kWh)":    round(ENERGIA_DIARIA[t], 3),
            "Energía mensual (kWh)":   round(ENERGIA_MENSUAL[t], 2),
            "USD por kWh/mes":         round(d["costo_usd"] / ENERGIA_MENSUAL[t], 2),
            f"Máx. en {s_area:.0f} m²": int(s_area // d["area_m2"]),
        }
        for t, d in PANELES.items()
    ])
    st.dataframe(df_paneles, use_container_width=True, hide_index=True)
    st.caption("*'USD por kWh/mes' = costo unitario ÷ energía mensual generada. Menor es más eficiente.*")

# ══════════════════════════════════════════════════════════════
# TAB 5 — MODELO MATEMÁTICO
# ══════════════════════════════════════════════════════════════
with tab5:
    st.subheader("📐 Modelo de Programación Lineal Entera")
    st.markdown("---")

    # ── Variables de decisión ──
    st.markdown("### Variables de decisión")
    st.markdown("""
Las variables representan la **cantidad de paneles de cada tipo** a instalar.
Son enteras y no negativas:
""")
    st.latex(r"C_A, C_B, C_C \in \mathbb{Z}_{\geq 0}")
    st.markdown("""
| Variable | Descripción |
|----------|-------------|
| $C_A$ | Cantidad de paneles tipo A (400 W, \$190, 1.9 m²) |
| $C_B$ | Cantidad de paneles tipo B (450 W, \$205, 2.1 m²) |
| $C_C$ | Cantidad de paneles tipo C (550 W, \$255, 2.5 m²) |
""")

    st.markdown("---")

    # ── Función objetivo ──
    st.markdown("### Función objetivo — Minimizar inversión")
    st.markdown("Se busca la combinación de paneles de **menor costo total** que cumpla todas las restricciones:")
    st.latex(r"\min \; W = 190\,C_A + 205\,C_B + 255\,C_C")

    st.markdown("---")

    # ── Parámetros energéticos ──
    from modelo_paneles import HSP, DIAS, ENERGIA_DIARIA
    st.markdown("### Parámetros del sistema")
    st.markdown(f"- **HSP** (Horas Pico Solar, Costa Rica) = **{HSP} h/día**")
    st.markdown("- Energía diaria generada por un panel de potencia $P_{{dc}}$:")
    st.latex(r"E_{diaria} = P_{dc} \times HSP")
    st.markdown("Valores por tipo de panel:")
    col1, col2, col3 = st.columns(3)
    col1.metric("Panel A — 400 W", f"{ENERGIA_DIARIA['A']:.3f} kWh/día",  "0.4 × 4.5")
    col2.metric("Panel B — 450 W", f"{ENERGIA_DIARIA['B']:.3f} kWh/día",  "0.45 × 4.5")
    col3.metric("Panel C — 550 W", f"{ENERGIA_DIARIA['C']:.3f} kWh/día",  "0.55 × 4.5")

    st.markdown("---")

    # ── Restricciones con valores dinámicos ──
    st.markdown("### Restricciones")

    # Usamos los valores actuales del sidebar o los defaults
    demanda_diaria_actual = s_demanda / (dias if 'dias' in dir() else 30)

    st.markdown("#### R1 — Al menos un panel instalado")
    st.markdown("Debe instalarse como mínimo un panel de cualquier tipo:")
    st.latex(r"C_A + C_B + C_C \geq 1")

    st.markdown("#### R2 — Restricción de área del techo")
    st.markdown(f"La suma del área ocupada no puede superar el área disponible del techo (**{s_area:.0f} m²**):")
    st.latex(
        r"1.9\,C_A + 2.1\,C_B + 2.5\,C_C \leq "
        + rf"{s_area:.0f}"
    )

    st.markdown("#### R3 — Cobertura de la demanda energética diaria")
    st.markdown(
        f"La energía generada debe cubrir la demanda diaria derivada del consumo mensual "
        f"(**{s_demanda:.0f} kWh/mes ÷ días = {demanda_diaria_actual:.3f} kWh/día**):"
    )
    st.latex(
        r"1.8\,C_A + 2.025\,C_B + 2.475\,C_C \geq "
        + rf"{demanda_diaria_actual:.3f}"
    )

    st.markdown("#### R4 — No negatividad e integralidad")
    st.latex(r"C_A,\, C_B,\, C_C \geq 0 \quad \text{y enteros}")

    st.markdown("---")

    # ── Modelo completo ──
    st.markdown("### Modelo completo")
    st.latex(
        r"\min \; W = 190\,C_A + 205\,C_B + 255\,C_C"
        r"\\ \text{sujeto a:}"
        r"\\ C_A + C_B + C_C \geq 1"
        r"\\ 1.9\,C_A + 2.1\,C_B + 2.5\,C_C \leq A_{techo}"
        r"\\ 1.8\,C_A + 2.025\,C_B + 2.475\,C_C \geq D_{diaria}"
        r"\\ C_A,\, C_B,\, C_C \in \mathbb{Z}_{\geq 0}"
    )

    if resultado is not None and resultado["estado"] == 1:
        st.markdown("---")
        st.markdown("### ✅ Solución óptima actual")
        r = resultado
        st.markdown(
            f"Con **área = {s_area:.0f} m²** y **demanda diaria = {demanda_diaria_actual:.3f} kWh/día**, "
            f"el solver encontró:"
        )
        st.latex(
            rf"C_A = {r['paneles']['A']}, \quad C_B = {r['paneles']['B']}, \quad C_C = {r['paneles']['C']}"
        )
        costo_verificado = 190*r['paneles']['A'] + 205*r['paneles']['B'] + 255*r['paneles']['C']
        st.latex(
            rf"W = 190({r['paneles']['A']}) + 205({r['paneles']['B']}) + 255({r['paneles']['C']}) = \${costo_verificado:,}"
        )
    else:
        st.info("Ingresá parámetros y presioná **Optimizar** para ver la solución aplicada al modelo.")

