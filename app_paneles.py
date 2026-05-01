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
    .stApp { background-color: #fff0f5; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #fce4ec; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #fce4ec; border-radius: 10px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #880e4f; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #f48fb1 !important; border-radius: 8px; color: #fff !important; }

    /* Métricas */
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #880e4f; }
    [data-testid="stMetricLabel"] { color: #ad1457; font-weight: 600; }
    [data-testid="metric-container"] {
        background-color: #fce4ec;
        border: 1px solid #f48fb1;
        border-radius: 12px;
        padding: 14px 18px;
    }

    /* Títulos */
    h1, h2, h3 { color: #880e4f !important; }

    /* Botón */
    .stButton > button {
        background-color: #e91e8c;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        transition: background 0.2s;
    }
    .stButton > button:hover { background-color: #c2185b; color: white; }

    /* Divisores */
    hr { border-color: #f48fb1; }

    /* Cajas de info/success */
    .stSuccess { background-color: #fce4ec !important; border-left: 4px solid #e91e8c !important; }
    .stInfo    { background-color: #fce4ec !important; border-left: 4px solid #f48fb1 !important; }

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
tarifa = st.sidebar.number_input(
    "Tarifa eléctrica ($/kWh)", min_value=0.01, value=0.11, step=0.01,
    help="Promedio residencial CR ≈ $0.11/kWh"
)

st.sidebar.markdown("---")
optimizar = st.sidebar.button("🚀 Optimizar", use_container_width=True)

# ---------------------------------------------------------------------------
# Cálculo y estado de sesión
# ---------------------------------------------------------------------------
if optimizar:
    r = resolver_casa("Casa", demanda, area, dias_mes=dias)
    st.session_state["resultado"] = r
    st.session_state["demanda"]   = demanda
    st.session_state["tarifa"]    = tarifa
    st.session_state["area"]      = area

resultado = st.session_state.get("resultado")
s_demanda = st.session_state.get("demanda", demanda)
s_tarifa  = st.session_state.get("tarifa",  tarifa)
s_area    = st.session_state.get("area",    area)

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
    "📊 Gráficos",
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
        inversion = r["costo_usd"]
        gasto_mes = s_demanda * s_tarifa
        ahorro_mes = r["energia_kwh_mes"] * s_tarifa
        ahorro_ano = ahorro_mes * 12
        ahorro_25  = ahorro_ano * VIDA_UTIL
        retorno    = inversion / ahorro_ano if ahorro_ano > 0 else float("inf")
        roi_25     = ((ahorro_25 - inversion) / inversion) * 100
        # año exacto de equilibrio
        anio_eq    = retorno

        st.subheader("💰 Resumen financiero")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Inversión inicial",        f"${inversion:,.2f}",  "Costo total paneles")
        col2.metric("Ahorro mensual estimado",  f"${ahorro_mes:,.2f}", f"vs ${gasto_mes:,.2f}/mes sin paneles")
        col3.metric("Ahorro anual estimado",    f"${ahorro_ano:,.2f}")

        st.markdown("---")
        col4, col5, col6 = st.columns(3)
        col4.metric("Vida útil paneles",        f"{VIDA_UTIL} años")
        col5.metric("Ahorro total en 25 años",  f"${ahorro_25:,.2f}")
        col6.metric("Punto de equilibrio",      f"{retorno:.1f} años", f"ROI 25 años: {roi_25:.0f}%")

        # ── Gráfico comparativa + punto de equilibrio ──
        st.markdown("---")
        st.subheader("📈 Ahorro acumulado vs costo acumulado sin paneles (25 años)")

        anos             = list(range(0, VIDA_UTIL + 1))
        ahorro_acum      = [ahorro_ano * a for a in anos]
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
            .encode(x="Año:Q", text=alt.value(f"Equilibrio: año {anio_eq:.1f}"))
        )

        st.altair_chart(line_chart + eq_rule + eq_text, use_container_width=True)

        st.caption(
            f"*Supuestos: tarifa fija de ${s_tarifa}/kWh, generación constante, "
            f"vida útil {VIDA_UTIL} años, sin mantenimiento significativo.*"
        )

        st.markdown("---")
        st.subheader("📅 Proyección anual detallada")
        tabla = pd.DataFrame({
            "Año":                          anos[1:],
            "Ahorro acumulado (USD)":       [f"${v:,.2f}" for v in ahorro_acum[1:]],
            "Costo acum. sin paneles (USD)":[f"${v:,.2f}" for v in costo_sin_panel[1:]],
            "Balance neto (USD)":           [f"${a - inversion:,.2f}" for a in ahorro_acum[1:]],
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
    col1, col2, col3 = st.columns(3)
    col1.metric("HSP Costa Rica",    "4.5 h/día",   "Horas Pico Solar")
    col2.metric("Performance Ratio", "0.80",         "Factor de eficiencia global")
    col3.metric("Fórmula",           "E = Pdc × HSP × PR", "Rendimiento fotovoltaico")

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
# TAB 5 — GRÁFICOS
# ══════════════════════════════════════════════════════════════
with tab5:
    st.subheader("⚡ Energía mensual por tipo de panel (unitario)")
    df_e = pd.DataFrame([
        {"Panel": f"Panel {t}", "kWh/mes": round(ENERGIA_MENSUAL[t], 2)}
        for t in PANELES
    ])
    bar_e = (
        alt.Chart(df_e)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Panel:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("kWh/mes:Q", title="Energía mensual (kWh)"),
            color=alt.Color("Panel:N", scale=alt.Scale(
                domain=["Panel A", "Panel B", "Panel C"],
                range=["#e91e8c", "#f48fb1", "#ad1457"]
            ), legend=None),
            tooltip=["Panel:N", "kWh/mes:Q"]
        )
        .properties(height=280)
    )
    st.altair_chart(bar_e, use_container_width=True)

    st.markdown("---")
    st.subheader("💲 Eficiencia de costo (USD / kWh mensual)")
    df_ef = pd.DataFrame([
        {"Panel": f"Panel {t}", "USD/kWh-mes": round(PANELES[t]["costo_usd"] / ENERGIA_MENSUAL[t], 2)}
        for t in PANELES
    ])
    bar_ef = (
        alt.Chart(df_ef)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Panel:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("USD/kWh-mes:Q", title="USD por kWh/mes generado"),
            color=alt.Color("Panel:N", scale=alt.Scale(
                domain=["Panel A", "Panel B", "Panel C"],
                range=["#e91e8c", "#f48fb1", "#ad1457"]
            ), legend=None),
            tooltip=["Panel:N", "USD/kWh-mes:Q"]
        )
        .properties(height=280, title="Menor valor = más eficiente en costo")
    )
    st.altair_chart(bar_ef, use_container_width=True)

    if resultado is not None and resultado["estado"] == 1:
        r = resultado
        st.markdown("---")
        st.subheader("🏠 Distribución de la solución óptima")

        df_inst = pd.DataFrame([
            {
                "Panel":         f"Panel {p}",
                "Cantidad":      r["paneles"][p],
                "Área total m²": round(PANELES[p]["area_m2"] * r["paneles"][p], 1),
                "Costo USD":     PANELES[p]["costo_usd"] * r["paneles"][p],
            }
            for p in PANELES if r["paneles"][p] > 0
        ])

        if not df_inst.empty:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                bar_cant = (
                    alt.Chart(df_inst)
                    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                    .encode(
                        x=alt.X("Panel:N", axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("Cantidad:Q"),
                        color=alt.Color("Panel:N", scale=alt.Scale(
                            domain=["Panel A", "Panel B", "Panel C"],
                            range=["#e91e8c", "#f48fb1", "#ad1457"]
                        ), legend=None),
                        tooltip=["Panel:N", "Cantidad:Q", "Costo USD:Q"]
                    )
                    .properties(height=260, title="Cantidad instalada por tipo")
                )
                st.altair_chart(bar_cant, use_container_width=True)

            with col_g2:
                pie_costo = (
                    alt.Chart(df_inst)
                    .mark_arc(innerRadius=55)
                    .encode(
                        theta=alt.Theta("Costo USD:Q"),
                        color=alt.Color("Panel:N", scale=alt.Scale(
                            domain=["Panel A", "Panel B", "Panel C"],
                            range=["#e91e8c", "#f48fb1", "#ad1457"]
                        )),
                        tooltip=["Panel:N", "Costo USD:Q", "Cantidad:Q"]
                    )
                    .properties(height=260, title="Distribución del costo de inversión")
                )
                st.altair_chart(pie_costo, use_container_width=True)

        st.markdown("---")
        st.subheader("📐 Uso del área del techo")
        area_usada = sum(PANELES[p]["area_m2"] * r["paneles"][p] for p in PANELES)
        df_area = pd.DataFrame({
            "Zona":       ["Utilizada", "Disponible"],
            "Área (m²)":  [area_usada, max(s_area - area_usada, 0)]
        })
        pie_area = (
            alt.Chart(df_area)
            .mark_arc(innerRadius=55)
            .encode(
                theta="Área (m²):Q",
                color=alt.Color("Zona:N", scale=alt.Scale(
                    domain=["Utilizada", "Disponible"],
                    range=["#e91e8c", "#fce4ec"]
                )),
                tooltip=["Zona:N", alt.Tooltip("Área (m²):Q", format=".1f")]
            )
            .properties(height=280, title=f"Techo: {s_area:.0f} m² totales")
        )
        st.altair_chart(pie_area, use_container_width=True)
    else:
        st.info("Optimizá desde la pestaña **Optimizador** para ver los gráficos de tu solución.")
