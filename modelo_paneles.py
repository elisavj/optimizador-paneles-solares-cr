from pulp import LpProblem, LpMinimize, LpVariable, LpInteger, lpSum, value, PULP_CBC_CMD

# ---------------------------------------------------------------------------
# Datos de los paneles solares
# ---------------------------------------------------------------------------
PANELES = {
    "A": {"potencia_kw": 0.400, "area_m2": 1.9, "costo_usd": 190},
    "B": {"potencia_kw": 0.450, "area_m2": 2.1, "costo_usd": 205},
    "C": {"potencia_kw": 0.550, "area_m2": 2.5, "costo_usd": 255},
}

HSP = 4.5   # Horas Pico Solar (h/día) — Costa Rica
PR  = 0.80  # Performance Ratio (factor de eficiencia estándar)

# Energía diaria por panel: E = Pdc × HSP × PR  (kWh/día)
ENERGIA_DIARIA = {p: d["potencia_kw"] * HSP * PR for p, d in PANELES.items()}

# ---------------------------------------------------------------------------
# Datos de las casas
# ---------------------------------------------------------------------------
CASAS = {
    "Casa 1": {"demanda_kwh": 267, "area_techo_m2": 120},
    "Casa 2": {"demanda_kwh": 120, "area_techo_m2": 250},
    "Casa 3": {"demanda_kwh": 172, "area_techo_m2":  80},
}


def resolver_casa(nombre_casa: str, demanda_kwh: float, area_techo_m2: float) -> dict:
    """
    Resuelve el modelo de PL para una casa dada.

    Parámetros
    ----------
    nombre_casa   : Identificador de la casa (solo para etiquetas).
    demanda_kwh   : Consumo diario a cubrir (kWh/día).
    area_techo_m2 : Área máxima disponible en el techo (m²).

    Retorna
    -------
    dict con cantidad óptima de cada panel, costo total y energía generada.
    """
    modelo = LpProblem(f"Paneles_{nombre_casa.replace(' ', '_')}", LpMinimize)

    # Variables de decisión: enteros no negativos
    vars_panel = {
        p: LpVariable(f"panel_{p}_{nombre_casa.replace(' ', '_')}",
                      lowBound=0, cat=LpInteger)
        for p in PANELES
    }

    # Función objetivo: minimizar costo total de inversión
    modelo += lpSum(PANELES[p]["costo_usd"] * vars_panel[p] for p in PANELES), "costo_total"

    # R1 — Al menos un panel instalado
    modelo += lpSum(vars_panel[p] for p in PANELES) >= 1, "min_un_panel"

    # R2 — No exceder el área del techo
    modelo += (
        lpSum(PANELES[p]["area_m2"] * vars_panel[p] for p in PANELES) <= area_techo_m2,
        "area_techo",
    )

    # R3 — Cubrir la demanda energética diaria
    modelo += (
        lpSum(ENERGIA_DIARIA[p] * vars_panel[p] for p in PANELES) >= demanda_kwh,
        "cobertura_demanda",
    )

    modelo.solve(PULP_CBC_CMD(msg=0))

    cantidades = {p: int(vars_panel[p].varValue) for p in PANELES}
    costo      = value(modelo.objective)
    energia    = sum(ENERGIA_DIARIA[p] * cantidades[p] for p in PANELES)

    return {
        "casa"        : nombre_casa,
        "paneles"     : cantidades,
        "costo_usd"   : costo,
        "energia_kwh" : round(energia, 3),
        "estado"      : modelo.status,
    }


def resolver_todas() -> list[dict]:
    """Resuelve el modelo para las tres casas y devuelve una lista de resultados."""
    return [resolver_casa(nombre, datos["demanda_kwh"], datos["area_techo_m2"])
            for nombre, datos in CASAS.items()]


if __name__ == "__main__":
    print(f"{'Casa':<10} {'Panel A':>8} {'Panel B':>8} {'Panel C':>8} "
          f"{'Energía (kWh)':>15} {'Costo (USD)':>12}")
    print("-" * 65)
    for r in resolver_todas():
        print(f"{r['casa']:<10} {r['paneles']['A']:>8} {r['paneles']['B']:>8} "
              f"{r['paneles']['C']:>8} {r['energia_kwh']:>15.3f} {r['costo_usd']:>12.2f}")
