# 📊 Reporte Estadístico: Patrones de Rendimiento y Confluencias
Generado a partir del análisis histórico de **52 trades** en tu bitácora de trading.

### 📈 Resumen General de Cuenta
* **Trades Totales:** `52`
* **Victorias (Wins):** `23`
* **Derrotas (Losses):** `20`
* **Breakevens (BEs):** `9`
* **Win Rate Efectivo (excluyendo BEs):** `53.5%` 

---
## 🧠 Patrones de Confluencias Ganadoras vs. Perdedoras
Analiza qué factores técnicos aumentan matemáticamente tu probabilidad de éxito:

| Confluencia Técnica | Usos Totales | Wins | Losses | BEs | Win Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Order Flow Support** | `5` | `3` | `0` | `2` | `100.0%` |
| **Bookmap Order Flow Absorption** | `1` | `1` | `0` | `0` | `100.0%` |
| **Heatmap Absorption** | `2` | `2` | `0` | `0` | `100.0%` |
| **Htf Bias Alignment** | `10` | `10` | `0` | `0` | `100.0%` |
| **Stop Hunt / Liquidity Sweep** | `5` | `4` | `0` | `1` | `100.0%` |
| **Fair Value Gap (Fvg) Retest** | `1` | `1` | `0` | `0` | `100.0%` |
| **Heatmap Limit Buy Block** | `2` | `2` | `0` | `0` | `100.0%` |
| **Heatmap Empty Liquidity Below** | `1` | `1` | `0` | `0` | `100.0%` |
| **Choch Confirmation** | `1` | `1` | `0` | `0` | `100.0%` |
| **Htf Pd Array Mitigation** | `19` | `12` | `3` | `4` | `80.0%` |
| **Liquidity Swept** | `5` | `4` | `1` | `0` | `80.0%` |
| **Smt Divergence** | `14` | `9` | `4` | `1` | `69.2%` |
| **Orderflow Absorption** | `8` | `5` | `3` | `0` | `62.5%` |
| **Htf Premium/Discount Zone** | `7` | `3` | `2` | `2` | `60.0%` |
| **Fair Value Gap (Fvg) On Entry Tf** | `9` | `5` | `4` | `0` | `55.6%` |
| **Inverse Fvg (Ifvg)** | `33` | `15` | `12` | `6` | `55.6%` |
| **Kill Zone Timing** | `36` | `17` | `14` | `5` | `54.8%` |
| **Order Block Alignment** | `3` | `1` | `2` | `0` | `33.3%` |
| **1M Cisd** | `2` | `0` | `1` | `1` | `0.0%` |
| **Overtrading / Emotional Revenge Entry** | `1` | `0` | `1` | `0` | `0.0%` |
| **5M Continuation Retest** | `1` | `0` | `1` | `0` | `0.0%` |
| **3M Fvg Retest** | `1` | `0` | `1` | `0` | `0.0%` |
| **Accidental Execution Due To Ui Lag** | `1` | `0` | `0` | `1` | `0.0%` |
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
| **SIN Smt Divergence** | `38` | `14` | `16` | `8` | `46.7%` | **🔴 Caída de `6.8%` en tu WR (Peligro)** |
| **SIN Orderflow Absorption** | `44` | `18` | `17` | `9` | `51.4%` | 🔴 Caída de `2.1%` en tu WR |
| **SIN Htf Bias Alignment** | `42` | `13` | `20` | `9` | `39.4%` | **🔴 Caída de `14.1%` en tu WR (Peligro)** |
| **SIN Liquidity Swept** | `47` | `19` | `19` | `9` | `50.0%` | 🔴 Caída de `3.5%` en tu WR |
| **SIN Htf Pd Array Mitigation** | `33` | `11` | `17` | `5` | `39.3%` | **🔴 Caída de `14.2%` en tu WR (Peligro)** |
| **SIN Inverse Fvg (Ifvg)** | `19` | `8` | `8` | `3` | `50.0%` | 🔴 Caída de `3.5%` en tu WR |

---
## ⚡ Análisis por Mercado (MNQ vs. MES)
¿En qué instrumento eres más rentable y eficiente?

| Instrumento | Trades Totales | Wins | Losses | BEs | Win Rate (%) | Ratio R:R Promedio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MES** | `7` | `0` | `4` | `3` | `0.0%` | `0.10 R` |
| **MNQ** | `5` | `3` | `2` | `0` | `60.0%` | `3.52 R` |
| **ES** | `19` | `10` | `5` | `4` | `66.7%` | `4.19 R` |
| **NQ** | `21` | `10` | `9` | `2` | `52.6%` | `1.54 R` |

---
## 📐 Métricas de Precisión MAE y MFE
Precisión de tus entradas y eficiencia de tus salidas en ticks promedio:

* **MAE Promedio en Victorias (Drawdown):** `60.5 ticks` (Un MAE bajo indica entradas precisas al instante).
* **MFE Promedio en Victorias (Recorrido Máximo):** `250.4 ticks` (Evalúa si tus salidas estructurales dejan dinero en la mesa).
* **MAE Promedio en Derrotas:** `61.3 ticks` (Muestra qué tanto permites que el precio vaya en tu contra antes de stop out).
* **MFE Promedio en Derrotas (Falsas Alarmas):** `51.1 ticks` (Muestra si tus trades perdedores estuvieron a favor antes de volverse en contra. Indica si debes ajustar la protección BE).

---
## 🚨 Patrones de Errores y Sesgos Psicológicos
Identificación de sesgos de comportamiento redactados en tus notas y su impacto real:

| Error Conductual Detectado | Sesiones con este Error | Wins | Losses | Win Rate (%) | Estado / Consecuencia |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Fomo / Entrada Prematura** | `9` | `1` | `6` | `14.3%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Sobreloteo / Riesgo Excesivo** | `3` | `0` | `3` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Duda / Ejecución Tardía** | `3` | `1` | `2` | `33.3%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Indisciplina / Fuera De Plan** | `2` | `0` | `2` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |
| **Be Prematuro / Miedo A Perder** | `0` | `0` | `0` | `0.0%` | 🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa) |

---
## 💡 CONCLUSIONES Y PLAN DE ACCIÓN PARA MEJORAR
1. ⚠️ **Regla de Oro:** Operar **SIN HTF PD ARRAY MITIGATION** destruye tu Win Rate, provocando una caída del `14.2%` en tu efectividad. A partir de ahora, **Htf Pd Array Mitigation** debe ser una confluencia de carácter **OBLIGATORIO** para autorizar cualquier trade.
2. ⚡ **Selección de Mercado:** Eres sustancialmente más rentable operando en **S&P 500 (ES)** (`66.7%` WR) en comparación con **Nasdaq (NQ)** (`52.6%` WR). Considera enfocar el 80% de tus análisis en tu mercado fuerte.
3. 🛡️ **Defensa y Gestión de BE:** En tus operaciones perdedoras, el precio avanza a favor de media un recorrido significativo antes de volverse en contra y tocar el stop. Esto indica que necesitas un protocolo más defensivo de **Breakeven parcial** o ajuste de Stop Loss cuando el precio alcance confluencias de 1:1 R:R.
4. 🚨 **Gestión de Impulsividad:** Las operaciones marcadas con sesgo de **FOMO / Entrada Prematura** tienen una tasa de acierto de apenas el `14.3%`. Esperar el cierre de la vela de confirmación y el retesteo estructural no es opcional: entrar antes por miedo a quedarse fuera es una pérdida matemática garantizada.