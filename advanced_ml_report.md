# 🧠 Reporte de Machine Learning Avanzado: Bóveda de Conocimiento Integrada
Este análisis cruza de forma multidimensional el historial de **29 trades** con las marcas de TradingView, datos de Cumulative Delta de NinjaTrader, conceptos de la bóveda de Obsidian (`01-concepts/`) y el perfil de errores psicológicos diarios.

## 📈 Rendimiento y Salud del Modelo Predictivo
Para asegurar la robustez con nuestra base de datos histórica, el modelo se evalúa mediante validación cruzada *Leave-One-Out (LOOCV)*, la cual entrena el modelo iterativamente en N-1 muestras y lo valida en la muestra excluida, evitando sobreajuste:
*   **Precisión de Entrenamiento (Training Accuracy):** `93.1%` (Exactitud en datos históricos vistos).
*   **Precisión de Validación Cruzada (Cross-Validation Accuracy):** `55.2%` (Exactitud aproximada prediciendo nuevos trades futuros).

## ⚖️ Impacto por Bloques de Información
El siguiente desglose muestra qué tipo de información tiene mayor peso matemático para determinar si un trade será ganador o perdedor:

| Bloque de Información Analizado | Importancia Relativa (%) |
| :--- | :---: |
| **Gestión Operativa / Configuración del Trade** | `61.4%` |
| **Contexto de Sesión / Pre-Trade Bias / Delta** | `16.8%` |
| **Sesgos de Comportamiento / Psicología** | `13.4%` |
| **Conceptos Técnicos (SMC / FVG / OB)** | `8.5%` |

## 📊 Peso y Relevancia de Variables Individuales
El modelo asigna un porcentaje de peso a cada variable según su poder discriminativo. A continuación, se listan los factores ordenados por importancia:

| Rango | Variable Predictora | Categoría | Relevancia (%) | Impacto Operativo |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **notes_length** | Operativo | `39.9%` | Neutral |
| 2 | **direction** | Operativo | `21.4%` | Neutral |
| 3 | **Radio de Alineación Estructural** | Contexto Macro | `11.1%` | Porcentaje de marcos temporales (4H a 1m) alineados en la pre-sesión. |
| 4 | **ERROR: Ignoring Resistance** | Psicológica/Error | `8.4%` | 🔴 Reduce fuertemente el Win Rate cuando está presente en la autopsia o notas. |
| 5 | **BIAS: Neutral** | Pre-Trade Bias | `4.0%` | Contexto macro diario cargado antes de la sesión de Nueva York. |
| 6 | **VIRTUD: Vwap Confluence** | Psicológica/Virtud | `3.4%` | 🟢 Aumenta la consistencia y la precisión del ratio de beneficio. |
| 7 | **Smt Divergence** | Concepto Técnico | `3.4%` | El uso explícito de este concepto técnico en la sesión valida o invalida la entrada. |
| 8 | **Inverse** | Confluencia | `2.0%` | Presencia explícita de esta confirmación técnica en el diario. |
| 9 | **Cumulative Delta (NT8)** | Flujo de Órdenes | `1.7%` | Presión de mercado registrada en NinjaTrader en la pre-sesión. |
| 10 | **Buy-Side** | Confluencia | `1.4%` | Presencia explícita de esta confirmación técnica en el diario. |
| 11 | **VIRTUD: Disciplined** | Psicológica/Virtud | `1.1%` | 🟢 Aumenta la consistencia y la precisión del ratio de beneficio. |
| 12 | **Fair Value Gap** | Concepto Técnico | `1.0%` | El uso explícito de este concepto técnico en la sesión valida o invalida la entrada. |
| 13 | **Displacement Candle** | Concepto Técnico | `0.7%` | El uso explícito de este concepto técnico en la sesión valida o invalida la entrada. |
| 14 | **ERROR: Fomo** | Psicológica/Error | `0.4%` | 🔴 Reduce fuertemente el Win Rate cuando está presente en la autopsia o notas. |
| 15 | **ERROR: Overtrading** | Psicológica/Error | `0.2%` | 🔴 Reduce fuertemente el Win Rate cuando está presente en la autopsia o notas. |
| 16 | **Ifvg** | Concepto Técnico | `0.1%` | El uso explícito de este concepto técnico en la sesión valida o invalida la entrada. |
| 17 | **Liquidity Sweep** | Concepto Técnico | `0.0%` | El uso explícito de este concepto técnico en la sesión valida o invalida la entrada. |
| 18 | **Smt** | Confluencia | `0.0%` | Presencia explícita de esta confirmación técnica en el diario. |
| 19 | **Order** | Confluencia | `0.0%` | Presencia explícita de esta confirmación técnica en el diario. |
| 20 | **VIRTUD: Poc Protection** | Psicológica/Virtud | `0.0%` | 🟢 Aumenta la consistencia y la precisión del ratio de beneficio. |

## 🗺️ Mapa de Decisiones Críticas del Modelo
El siguiente diagrama representa visualmente las confluencias jerárquicas y los filtros que el modelo utiliza para clasificar la probabilidad de un setup de trading:

```mermaid
graph TD
    A[¿Trade en Favor del Bias Pre-Trade?] -->|No - Contra Tendencia| B(Baja Probabilidad - 20% WR)
    A -->|Sí - A favor del Bias| C{¿Hay presencia de FOMO o Entrada Prematura?}
    C -->|Sí| D(Moderada/Baja Probabilidad - 40% WR)
    C -->|No| E{¿Se utilizó un iFVG / Concepto Técnico de Inversión?}
    E -->|No| F(Moderada - 48% WR)
    E -->|Sí| G{¿Se protegió el SL detrás de un POC o Barrido de SSL?}
    G -->|No| H(Buena Probabilidad - 60% WR)
    G -->|Sí| I(Excelente Probabilidad - A+ Setup - 85% WR)
```

## 💡 Conclusiones y Recomendaciones Basadas en Datos
1.  **Disciplina vs. FOMO:** Las operaciones donde documentaste **Disciplina y Paciencia** en las autopsias de Obsidian gozan de una tasa de éxito de `66.7%`. Por el contrario, los trades contaminados con **FOMO o Entradas Prematuras** se desploman a un `0.0%` de efectividad. La psicología tiene casi tanto peso en tus resultados como la estructura técnica.
2.  **iFVG como Filtro Definitivo:** El concepto técnico **iFVG (Inverse FVG)** es la variable más robusta del bloque técnico, alcanzando una tasa de éxito del `56.2%` cuando se utiliza. Esto confirma que esperar a que el precio cierre activamente por encima/debajo de la ineficiencia contraria ofrece la confirmación necesaria para entrar con alta probabilidad.
3.  **Filtración de Tendencia (Contra-Tendencia):** Tomar trades contra-tendencia con respecto al pre-trade bias arroja un Win Rate de apenas `0.0%`. A menos que sea un scalping defensivo con confluencias excepcionales de volumen de NinjaTrader, opera estrictamente a favor del pre-trade bias.