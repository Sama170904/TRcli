# 📊 Reporte Estadístico: Patrones de Rendimiento y Confluencias
Generado a partir del análisis histórico de **24 trades** en tu bitácora de trading.

### 📈 Resumen General de Cuenta
* **Trades Totales:** `24`
* **Victorias (Wins):** `12`
* **Derrotas (Losses):** `9`
* **Breakevens (BEs):** `3`
* **Win Rate Efectivo (excluyendo BEs):** `57.1%` 

---
## 🧠 Patrones de Confluencias Ganadoras vs. Perdedoras
Analiza qué factores técnicos aumentan matemáticamente tu probabilidad de éxito:

| Confluencia Técnica | Usos Totales | Wins | Losses | BEs | Win Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Liquidity Swept** | `3` | `3` | `0` | `0` | `100.0%` |
| **Htf Bias Alignment** | `9` | `9` | `0` | `0` | `100.0%` |
| **Stop Hunt / Liquidity Sweep** | `3` | `2` | `0` | `1` | `100.0%` |
| **Choch Confirmation** | `1` | `1` | `0` | `0` | `100.0%` |
| **Fair Value Gap (Fvg) On Entry Tf** | `2` | `2` | `0` | `0` | `100.0%` |
| **Htf Pd Array Mitigation** | `9` | `6` | `1` | `2` | `85.7%` |
| **Htf Premium/Discount Zone** | `7` | `3` | `2` | `2` | `60.0%` |
| **Inverse Fvg (Ifvg)** | `16` | `8` | `6` | `2` | `57.1%` |
| **Kill Zone Timing** | `21` | `10` | `9` | `2` | `52.6%` |
| **Smt Divergence** | `5` | `2` | `2` | `1` | `50.0%` |
| **Order Block Alignment** | `2` | `1` | `1` | `0` | `50.0%` |
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
| **SIN Smt Divergence** | `19` | `10` | `7` | `2` | `58.8%` | 🟢 Subida de `1.7%` en tu WR |
| **SIN Orderflow Absorption** | `24` | `12` | `9` | `3` | `57.1%` | 🟢 Subida de `0.0%` en tu WR |
| **SIN Htf Bias Alignment** | `15` | `3` | `9` | `3` | `25.0%` | ⚠️ **🔴 Caída de `32.1%` en tu WR (Muy Crítico)** |
| **SIN Liquidity Swept** | `21` | `9` | `9` | `3` | `50.0%` | **🔴 Caída de `7.1%` en tu WR (Peligro)** |
| **SIN Htf Pd Array Mitigation** | `15` | `6` | `8` | `1` | `42.9%` | **🔴 Caída de `14.3%` en tu WR (Peligro)** |
| **SIN Inverse Fvg (Ifvg)** | `8` | `4` | `3` | `1` | `57.1%` | 🟢 Subida de `0.0%` en tu WR |

---
## ⚡ Análisis por Mercado (MNQ vs. MES)
¿En qué instrumento eres más rentable y eficiente?

| Instrumento | Trades Totales | Wins | Losses | BEs | Win Rate (%) | Ratio R:R Promedio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **NQ** | `21` | `10` | `9` | `2` | `52.6%` | `1.54 R` |
| **ES** | `3` | `2` | `0` | `1` | `100.0%` | `12.87 R` |

---
## 📐 Métricas de Precisión MAE y MFE
Precisión de tus entradas y eficiencia de tus salidas en ticks promedio:

* **MAE Promedio en Victorias (Drawdown):** `87.8 ticks` (Un MAE bajo indica entradas precisas al instante).
* **MFE Promedio en Victorias (Recorrido Máximo):** `355.5 ticks` (Evalúa si tus salidas estructurales dejan dinero en la mesa).
* **MAE Promedio en Derrotas:** `115.9 ticks` (Muestra qué tanto permites que el precio vaya en tu contra antes de stop out).
* **MFE Promedio en Derrotas (Falsas Alarmas):** `91.7 ticks` (Muestra si tus trades perdedores estuvieron a favor antes de volverse en contra. Indica si debes ajustar la protección BE).

---
## 🚨 Patrones de Errores y Sesgos Psicológicos
Identificación de sesgos de comportamiento redactados en tus notas y su impacto real:

| Error Conductual Detectado | Sesiones con este Error | Wins | Losses | Win Rate (%) | Estado / Consecuencia |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Fomo / Entrada Prematura** | `3` | `0` | `3` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Sobreloteo / Riesgo Excesivo** | `2` | `0` | `2` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Duda / Ejecución Tardía** | `1` | `1` | `0` | `100.0%` | 🟢 Operable con cuidado |
| **Indisciplina / Fuera De Plan** | `0` | `0` | `0` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Be Prematuro / Miedo A Perder** | `0` | `0` | `0` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |

---
## 💡 CONCLUSIONES Y PLAN DE ACCIÓN PARA MEJORAR
1. ⚠️ **Regla de Oro:** Operar **SIN HTF BIAS ALIGNMENT** destruye tu Win Rate, provocando una caída del `32.1%` en tu efectividad. A partir de ahora, **Htf Bias Alignment** debe ser una confluencia de carácter **OBLIGATORIO** para autorizar cualquier trade.
2. ⚡ **Selección de Mercado:** Eres sustancialmente más rentable operando en **S&P 500 (ES)** (`100.0%` WR) en comparación con **Nasdaq (NQ)** (`52.6%` WR). Considera enfocar el 80% de tus análisis en tu mercado fuerte.
4. 🚨 **Gestión de Impulsividad:** Las operaciones marcadas con sesgo de **FOMO / Entrada Prematura** tienen una tasa de acierto de apenas el `0.0%`. Esperar el cierre de la vela de confirmación y el retesteo estructural no es opcional: entrar antes por miedo a quedarse fuera es una pérdida matemática garantizada.