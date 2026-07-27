---
title: "Sesión <% tp.file.title %>"
tags: [session, journal, autopsy]
created: <% tp.file.creation_date("YYYY-MM-DD HH:mm") %>
pnl: 0.00
trades_count: 0
result: "BE"
---

# 📅 BITÁCORA DE TRADING — <% tp.date.now("DD [de] MMMM [de] YYYY") %>
**Pre-Trade Link:** [[<% tp.date.now("YYYY-MM-DD") %>_pre_trade]]

## 📊 RESUMEN GENERAL DE LA SESIÓN
- **Resultado Neto:** `<pnl> USD`
- **Trades Realizados:** `<trades_count>`
- **Resultado:** `<result>` (WIN / LOSS / BE)

---

## 🖼️ CAPTURA DE PANTALLA
![Gráfico de la Sesión del <% tp.date.now("YYYY-MM-DD") %>](../imagenes/<% tp.date.now("YYYY-MM-DD") %>_chart.png)

---

## 🔍 ANÁLISIS ESTRUCTURAL DE TEMPORALIDADES (TOP-DOWN)
### 1. Temporalidades Mayores (HTF: 4h / 1h)
- **Bias:** Alcista 🟢 / Bajista 🔴 / Rango 🟡
- **Narrativa:** 

### 2. Temporalidades Intermedias (30m / 15m)
- **Zonas clave (POIs):** 

### 3. Temporalidad de Ejecución (5m / 2m / 1m)
- **Gatillo / Desplazamiento:** 

---

## 📈 REPORTE DETALLADO DE LOS TRADES
### 🟢/🔴 TRADE #1: [Long/Short] en [Instrumento]
- **Entrada:** 
- **MAE:** 
- **MFE:** 
- **Resultado:** 

---

## 🎯 CONTEXT SCORE — EVALUACIÓN DE CONTEXTO POR TRADE
> Referencia completa del sistema: [ground_truth.md Sección J](../ground_truth.md) | [configuracion.md Sección 6.G](../configuracion.md)

### Trade #1: Context Score
#### Nivel 0 — Gates Eliminatorias
| Gate | ¿Pasó? |
|:---|:---:|
| Dentro de Killzone | ✅ / ❌ |
| R:R > 1:1 | ✅ / ❌ |
| Sin noticias Red Folder en 5 min | ✅ / ❌ |
| POI no mitigado (1er toque) | ✅ / ❌ |
| P/D correcto (Rango) o A favor de tendencia (Expansión) | ✅ / ❌ |

#### Nivel 1 — Peso Máximo (×3 pts c/u)
| Factor | Presente | Pts |
|:---|:---:|:---:|
| DOL claro y definido | ✅ / ❌ | 3 / 0 |
| LRLR a favor (camino limpio) | ✅ / ❌ | 3 / 0 |
| Sin resistencia macro cerca del entry | ✅ / ❌ | 3 / 0 |
| Calidad del nivel de reacción (TF del POI) | ✅ / ❌ | 3 / 0 |

#### Nivel 2 — Peso Alto (×2 pts c/u)
| Factor | Presente | Pts |
|:---|:---:|:---:|
| HTF Bias alineado (4H/1D) | ✅ / ❌ | 2 / 0 |
| Tipo de día + Posición VA correcta | ✅ / ❌ | 2 / 0 |
| Fase del PO3 correcta | ✅ / ❌ | 2 / 0 |
| Sin FVGs en contra de mi dirección | ✅ / ❌ | 2 / 0 |

#### Nivel 3 — Confluencias (×1 pt c/u)
| Factor | Presente | Pts |
|:---|:---:|:---:|
| SMT Divergence | ✅ / ❌ | 1 / 0 |
| Order Flow / Delta confirmando | ✅ / ❌ | 1 / 0 |
| Sweep de sesión previa confirmado | ✅ / ❌ | 1 / 0 |
| Protected H/L como DOL | ✅ / ❌ | 1 / 0 |
| Velocidad de formación FVG macro (agresivo) | ✅ / ❌ | 1 / 0 |
| Sin BPR activo en contra | ✅ / ❌ | 1 / 0 |

**CONTEXT SCORE TOTAL: __ / 26 pts → Clasificación: [A+ / B / C / No Operable]**

| Rango | Clasificación |
|:---:|:---|
| 22-26 | Setup A+ → Full size |
| 16-21 | Setup B → Tamaño normal |
| 10-15 | Setup C → Reducir o no operar |
| 0-9 | No operable → El Mech Model era irrelevante |

---

## 🧠 CENTRO DE APRENDIZAJE Y RETROALIMENTACIÓN (MÉTODO STEENBARGER)

> [!TIP]
> **TARJETA DE MEMORIA DE RÁPIDA CONSULTA (Revisar antes de abrir el mercado)**
> - **El Foco de Hoy:** <resumen_accionario_de_1_oracion>
> - **Acción de Éxito a Repetir (Músculo):** <buen_habito_a_mantener>
> - **Error Crítico a Evitar (Eliminar):** <error_a_mitigar_y_su_gatillo>

### ⚖️ Clasificación: Proceso vs. Resultado
*¿Ejecutaste el plan de manera disciplinada, independientemente de ganar o perder dinero?*
- **Trade #1:** [<Resultado_PnL>] ➔ **Proceso:** [CORRECTO (Buen Trade) / INCORRECTO (Mal Trade)] \| *Razón:* <explicacion_del_proceso>
- **Trade #2:** [<Resultado_PnL>] ➔ **Proceso:** [CORRECTO (Buen Trade) / INCORRECTO (Mal Trade)] \| *Razón:* <explicacion_del_proceso>

### 📈 Plan de Acción Inmediato para la Próxima Sesión
- **Qué mantendré:** 
- **Qué corregiré activamente:** 

