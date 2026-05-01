import streamlit as st
from modelo_paneles import resolver_casa, PANELES, ENERGIA_DIARIA

st.set_page_config(
    page_title="Optimizador Paneles Solares CR",
    page_icon="☀️",
    layout="wide",
)

st.title("☀️ Optimizador de Paneles Solares — Costa Rica")
st.write(
    "Minimiza la inversión en paneles solares cubriendo el consumo energético "
    "diario de cada hogar sin exceder el área de techo disponible."
)

# ---------------------------------------------------------------------------
# Sidebar — parámetros editables
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Parámetros de la casa")

nombre   = st.sidebar.text_input("Nombre de la casa", value="Mi Casa")
demanda  = st.sidebar.number_input("Consumo diario (kWh/día)", min_value=0.1, value=8.9, step=0.1)
area     = st.sidebar.number_input("Área del techo disponible (m²)", min_value=1.0, value=120.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Referencia de paneles")
for p, d in PANELES.items():
    st.sidebar.markdown(
        f"**Panel {p}** — {int(d['potencia_kw']*1000)} W · "
        f"{d['area_m2']} m² · ${d['costo_usd']}"
    )

# ---------------------------------------------------------------------------
# Optimización
# ---------------------------------------------------------------------------
if st.button("🚀 Optimizar"):
    resultado = resolver_casa(nombre, demanda, area)

    if resultado["estado"] != 1:
        st.error("❌ No se encontró solución factible. Revisa los parámetros ingresados.")
    else:
        st.success(f"✅ Inversión mínima: **${resultado['costo_usd']:,.2f} USD**")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔵 Paneles A (400 W)", resultado["paneles"]["A"])
        col2.metric("🟠 Paneles B (450 W)", resultado["paneles"]["B"])
        col3.metric("🟢 Paneles C (550 W)", resultado["paneles"]["C"])
        col4.metric("⚡ Energía generada", f"{resultado['energia_kwh']} kWh/día")

        total_paneles = sum(resultado["paneles"].values())
        area_usada    = sum(PANELES[p]["area_m2"] * resultado["paneles"][p] for p in PANELES)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            st.bar_chart(
                {f"Panel {p}": resultado["paneles"][p] for p in PANELES},
                use_container_width=True,
            )
        with col_b:
            st.markdown("#### 📊 Resumen")
            st.markdown(f"- **Total de paneles:** {total_paneles}")
            st.markdown(f"- **Área utilizada:** {area_usada:.1f} m² / {area} m²")
            st.markdown(f"- **Cobertura:** {resultado['energia_kwh']:.2f} kWh/día "
                        f"(demanda: {demanda} kWh/día)")
            st.markdown(f"- **Excedente:** {resultado['energia_kwh'] - demanda:.2f} kWh/día")

        st.markdown("---")
        st.markdown(
            f"**Interpretación:** La solución óptima para **{nombre}** instala "
            f"**{resultado['paneles']['A']} paneles A**, "
            f"**{resultado['paneles']['B']} paneles B** y "
            f"**{resultado['paneles']['C']} paneles C**, "
            f"generando {resultado['energia_kwh']:.2f} kWh/día con una inversión "
            f"mínima de **${resultado['costo_usd']:,.2f} USD**."
        )
