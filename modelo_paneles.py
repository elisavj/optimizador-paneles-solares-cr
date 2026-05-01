from pulp import LpProblem, LpMinimize, LpVariable, LpInteger, lpSum, value, PULP_CBC_CMD

# ---------------------------------------------------------------------------
# Datos de los paneles solares
# ---------------------------------------------------------------------------
PANELES = {
    "A": {"potencia_kw": 0.400, "area_m2": 1.9, "costo_usd": 190},
    "B": {"potencia_kw": 0.450, "area_m2": 2.1, "costo_usd": 205},
    "C": {"potencia_kw": 0.550, "area_m2": 2.5, "costo_usd": 255},
}

HSP  = 4.5   # Horas Pico Solar (h/día) — Costa Rica
DIAS = 30    # Días por mes (estándar)

# Energía diaria por panel: E = Pdc × HSP  (kWh/día)
ENERGIA_DIARIA = {p: d["potencia_kw"] * HSP for p, d in PANELES.items()}

# Energía mensual por panel (kWh/mes)
ENERGIA_MENSUAL = {p: ENERGIA_DIARIA[p] * DIAS for p in PANELES}

# ---------------------------------------------------------------------------
# Datos de las casas  (consumo en kWh/mes)
# ---------------------------------------------------------------------------
CASAS = {
    "Casa 1": {"demanda_kwh_mes": 267, "area_techo_m2": 120},
    "Casa 2": {"demanda_kwh_mes": 120, "area_techo_m2": 250},
    "Casa 3": {"demanda_kwh_mes": 172, "area_techo_m2":  80},
}


def resolver_casa(nombre_casa: str, demanda_kwh_mes: float, area_techo_m2: float,
                  dias_mes: int = DIAS) -> dict:
    """
    Resuelve el modelo de PL para una casa dada.

    Parámetros
    ----------
    nombre_casa     : Identificador de la casa (solo para etiquetas).
    demanda_kwh_mes : Consumo mensual a cubrir (kWh/mes).
    area_techo_m2   : Área máxima disponible en el techo (m²).
    dias_mes        : Días del mes de referencia (default 30).

    Retorna
    -------
    dict con cantidad óptima de cada panel, costo total y energía generada.
    """
    demanda_diaria = demanda_kwh_mes / dias_mes  # conversión interna para R3

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

    # R3 — Cubrir la demanda energética diaria (derivada del consumo mensual)
    modelo += (
        lpSum(ENERGIA_DIARIA[p] * vars_panel[p] for p in PANELES) >= demanda_diaria,
        "cobertura_demanda",
    )

    modelo.solve(PULP_CBC_CMD(msg=0))

    cantidades      = {p: int(vars_panel[p].varValue) for p in PANELES}
    energia_diaria  = sum(ENERGIA_DIARIA[p] * cantidades[p] for p in PANELES)
    energia_mensual = energia_diaria * dias_mes

    return {
        "casa"             : nombre_casa,
        "paneles"          : cantidades,
        "costo_usd"        : value(modelo.objective),
        "energia_kwh_mes"  : round(energia_mensual, 2),
        "energia_kwh_dia"  : round(energia_diaria, 3),
        "demanda_kwh_mes"  : demanda_kwh_mes,
        "estado"           : modelo.status,
    }


def resolver_todas() -> list[dict]:
    """Resuelve el modelo para las tres casas y devuelve una lista de resultados."""
    return [resolver_casa(nombre, datos["demanda_kwh_mes"], datos["area_techo_m2"])
            for nombre, datos in CASAS.items()]


if __name__ == "__main__":
    print(f"{'Casa':<10} {'Panel A':>8} {'Panel B':>8} {'Panel C':>8} "
          f"{'Energía (kWh/mes)':>18} {'Costo (USD)':>12}")
    print("-" * 70)
    for r in resolver_todas():
        print(f"{r['casa']:<10} {r['paneles']['A']:>8} {r['paneles']['B']:>8} "
              f"{r['paneles']['C']:>8} {r['energia_kwh_mes']:>18.2f} {r['costo_usd']:>12.2f}")
