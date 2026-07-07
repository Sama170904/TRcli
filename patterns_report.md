# 📊 Reporte Estadístico: Patrones de Rendimiento y Confluencias
Generado a partir del análisis histórico de **29 trades** en tu bitácora de trading.

### 📈 Resumen General de Cuenta
* **Trades Totales:** `29`
* **Victorias (Wins):** `15`
* **Derrotas (Losses):** `11`
* **Breakevens (BEs):** `3`
* **Win Rate Efectivo (excluyendo BEs):** `57.7%` 

---
## 🧠 Patrones de Confluencias Ganadoras vs. Perdedoras
Analiza qué factores técnicos aumentan matemáticamente tu probabilidad de éxito:

| Confluencia Técnica | Usos Totales | Wins | Losses | BEs | Win Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Heatmap Limit Buy Block** | `2` | `2` | `0` | `0` | `100.0%` |
| **Heatmap Empty Liquidity Below** | `1` | `1` | `0` | `0` | `100.0%` |
| **Htf Bias Alignment** | `9` | `9` | `0` | `0` | `100.0%` |
| **Stop Hunt / Liquidity Sweep** | `3` | `2` | `0` | `1` | `100.0%` |
| **Choch Confirmation** | `1` | `1` | `0` | `0` | `100.0%` |
| **Fair Value Gap (Fvg) On Entry Tf** | `2` | `2` | `0` | `0` | `100.0%` |
| **Htf Pd Array Mitigation** | `11` | `8` | `1` | `2` | `88.9%` |
| **Liquidity Swept** | `4` | `3` | `1` | `0` | `75.0%` |
| **Htf Premium/Discount Zone** | `7` | `3` | `2` | `2` | `60.0%` |
| **Inverse Fvg (Ifvg)** | `21` | `11` | `8` | `2` | `57.9%` |
| **Smt Divergence** | `8` | `4` | `3` | `1` | `57.1%` |
| **Kill Zone Timing** | `22` | `11` | `9` | `2` | `55.0%` |
| **Orderflow Absorption** | `2` | `1` | `1` | `0` | `50.0%` |
| **Order Block Alignment** | `3` | `1` | `2` | `0` | `33.3%` |
| **Adding Contracts** | `1` | `0` | `1` | `0` | `0.0%` |
| **5M Continuation** | `1` | `0` | `1` | `0` | `0.0%` |
| **Fomo** | `1` | `0` | `1` | `0` | `0.0%` |
| **Bos Confirmation** | `1` | `0` | `0` | `1` | `0.0%` |
| **Minimum 2R Target Available** | `1` | `0` | `1` | `0` | `0.0%` |

---
## 🔍 Impacto de la AUSENCIA de Confluencias Clave
¿Qué sucede si ignoras un elemento del plan? Estos son los resultados cuando operas **SIN** confluencia:

| Confluencia Faltante | Trades Operados SIN ella | Wins | Losses | BEs | Win Rate SIN ella (%) | Impacto en tu WR |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **SIN Smt Divergence** | `21` | `11` | `8` | `2` | `57.9%` | 🟢 Subida de `0.2%` en tu WR |
| **SIN Orderflow Absorption** | `27` | `14` | `10` | `3` | `58.3%` | 🟢 Subida de `0.6%` en tu WR |
| **SIN Htf Bias Alignment** | `20` | `6` | `11` | `3` | `35.3%` | ⚠️ **🔴 Caída de `22.4%` en tu WR (Muy Crítico)** |
| **SIN Liquidity Swept** | `25` | `12` | `10` | `3` | `54.5%` | 🔴 Caída de `3.1%` en tu WR |
| **SIN Htf Pd Array Mitigation** | `18` | `7` | `10` | `1` | `41.2%` | ⚠️ **🔴 Caída de `16.5%` en tu WR (Muy Crítico)** |
| **SIN Inverse Fvg (Ifvg)** | `8` | `4` | `3` | `1` | `57.1%` | 🔴 Caída de `0.5%` en tu WR |

---
## ⚡ Análisis por Mercado (MNQ vs. MES)
¿En qué instrumento eres más rentable y eficiente?

| Instrumento | Trades Totales | Wins | Losses | BEs | Win Rate (%) | Ratio R:R Promedio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ES** | `8` | `5` | `2` | `1` | `71.4%` | `6.91 R` |
| **NQ** | `21` | `10` | `9` | `2` | `52.6%` | `1.54 R` |

---
## 📐 Métricas de Precisión MAE y MFE
Precisión de tus entradas y eficiencia de tus salidas en ticks promedio:

* **MAE Promedio en Victorias (Drawdown):** `69.0 ticks` (Un MAE bajo indica entradas precisas al instante).
* **MFE Promedio en Victorias (Recorrido Máximo):** `296.9 ticks` (Evalúa si tus salidas estructurales dejan dinero en la mesa).
* **MAE Promedio en Derrotas:** `82.3 ticks` (Muestra qué tanto permites que el precio vaya en tu contra antes de stop out).
* **MFE Promedio en Derrotas (Falsas Alarmas):** `87.5 ticks` (Muestra si tus trades perdedores estuvieron a favor antes de volverse en contra. Indica si debes ajustar la protección BE).

---
## 🚨 Patrones de Errores y Sesgos Psicológicos
Identificación de sesgos de comportamiento redactados en tus notas y su impacto real:

| Error Conductual Detectado | Sesiones con este Error | Wins | Losses | Win Rate (%) | Estado / Consecuencia |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Fomo / Entrada Prematura** | `4` | `1` | `3` | `25.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Sobreloteo / Riesgo Excesivo** | `2` | `0` | `2` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Duda / Ejecución Tardía** | `1` | `1` | `0` | `100.0%` | 🟢 Operable con cuidado |
| **Indisciplina / Fuera De Plan** | `0` | `0` | `0` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Be Prematuro / Miedo A Perder** | `0` | `0` | `0` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |

---
## 💡 CONCLUSIONES Y PLAN DE ACCIÓN PARA MEJORAR
1. ⚠️ **Regla de Oro:** Operar **SIN HTF BIAS ALIGNMENT** destruye tu Win Rate, provocando una caída del `22.4%` en tu efectividad. A partir de ahora, **Htf Bias Alignment** debe ser una confluencia de carácter **OBLIGATORIO** para autorizar cualquier trade.
2. ⚡ **Selección de Mercado:** Eres sustancialmente más rentable operando en **S&P 500 (ES)** (`71.4%` WR) en comparación con **Nasdaq (NQ)** (`52.6%` WR). Considera enfocar el 80% de tus análisis en tu mercado fuerte.
3. 🛡️ **Defensa y Gestión de BE:** En tus operaciones perdedoras, el precio avanza a favor de media un recorrido significativo antes de volverse en contra y tocar el stop. Esto indica que necesitas un protocolo más defensivo de **Breakeven parcial** o ajuste de Stop Loss cuando el precio alcance confluencias de 1:1 R:R.
4. 🚨 **Gestión de Impulsividad:** Las operaciones marcadas con sesgo de **FOMO / Entrada Prematura** tienen una tasa de acierto de apenas el `25.0%`. Esperar el cierre de la vela de confirmación y el retesteo estructural no es opcional: entrar antes por miedo a quedarse fuera es una pérdida matemática garantizada.