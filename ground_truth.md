# 🧠 GROUND TRUTH — Verdades Absolutas del Sistema de Trading
# Este archivo es el núcleo comprimido de TODO el entorno de Obsidian.
# Antigravity DEBE leerlo al inicio de CADA sesión y usarlo como referencia
# antes de responder cualquier pregunta de trading. Prevalece sobre conocimiento genérico.

---

## A. MODELO DE ENTRADA (MECH MODEL — 5 FASES)
1. **Contexto Macro:** Confirmar bias HTF (4H/1D). Si chocan, obedece 1D. Longs en Discount, Shorts en Premium. EXCEPCIÓN: En días de Expansión, Premium/Discount macro deja de importar.
2. **Killzone:** Solo operar dentro de London (08:00-11:00 GMT) o NY AM (09:30-10:30 NYT). Fuera de killzone = no trade.
3. **Fase 1 — Sweep:** El precio DEBE barrer un POI institucional (BSL/SSL de sesión, EQH/EQL). SMT Divergence es opcional pero sin ella el win rate cae al 20%.
4. **Fase 2 — Desplazamiento + iFVG:** La vela de confirmación DEBE CERRAR CON CUERPO COMPLETO cruzando el FVG, invirtiéndolo. Sin cierre de cuerpo = no hay setup.
5. **Fase 3 — Entrada en RETESTEO:** Nunca en la vela de desplazamiento. Esperar retroceso al iFVG. Si el cierre está lejos (daña RR 1:2), usar ORDEN LÍMITE. Si el precio se va sin tomar el límite, se descarta.

## B. GESTIÓN DE RIESGO INQUEBRANTABLE
- **Riesgo por trade:** Máximo 1% del balance.
- **Pérdida diaria:** Máximo 2% (2 trades perdedores). Si se alcanza → cerrar plataformas.
- **R:R mínimo:** 1:2 obligatorio para entrar.
- **SL:** Justo fuera del límite lejano del iFVG + 5 ticks de holgura.
- **TP1:** Al tocar liquidez interna → cerrar 50% y mover SL a BE obligatoriamente.
- **Prohibido:** Averaging down, sobrelotear tras ganar, mover SL a BE por pánico antes de TP1.

## C. FILTROS DE EXCLUSIÓN (CUÁNDO NO OPERAR)
- Dentro de 5 min antes de noticias Red Folder.
- Desplazamiento lento (>2 velas consolidando en lugar de quiebre fuerte).
- Contra-momentum extremo institucional llegando al POI.
- OB/Breaker Block bloqueando el camino al DOL.
- iFVG invalidado (vela cierra cruzando la frontera lejana).
- Segundo toque de un OB (ya fue mitigado, el OB muere al 1er toque limpio).

## D. CLASIFICACIÓN DEL DÍA (ACCIÓN DEL PRECIO > INDICADORES)
- **Expansión (Tendencia):** Precio rompe nivel clave (Asia/London H/L) con cierre de cuerpo con momentum consecutivo. → Operar SOLO a favor. VWAP: usar bandas SD2/SD3 como soporte dinámico. PROHIBIDO contratendencia.
- **Consolidación (Rango):** Precio barre extremos pero rechaza con mechas, cuerpos encajados. → Mean Reversion: comprar en SD-2, vender en SD+2, target = media VWAP.
- **Balance vs Imbalance (Cramz/AMT):** Si NY abre dentro del VA previo = Balance (reversiones en extremos). Si abre fuera = Imbalance (direccional, no operar reversión hacia adentro).

## E. ERRORES PSICOLÓGICOS RECURRENTES (FRECUENCIA REAL)
1. **Ignorar Resistencia/Soporte Macro** — 67.7% de incidencia. EL ERROR #1.
2. **FOMO / Chasing** — 58.1%. Perseguir precio en lugar de esperar retesteo.
3. **Overtrading** — 25.8%. Forzar entradas tras rachas o volatilidad.
4. **Revenge Trading** — Dudar en un buen trade → compensar con trade impulsivo.
5. **BE Prematuro** — Mover a breakeven por pánico antes de TP1 mata la esperanza matemática.

## F. VERDADES ESTADÍSTICAS DEL JOURNAL
- **Mejor setup:** iFVG + SMT Divergence a favor de HTF bias en killzone. Mayor win rate y recorridos más limpios.
- **Peor setup:** Continuación en 1m forzada contra tendencia mayor o en Premium extremo sin retroceso.
- **En trades ganadores:** MAE cercano a 0 (el precio no visita la zona de pérdida cuando el setup es correcto). MFE excede ampliamente el TP final → se dejan ganancias significativas en la mesa.
- **En trades perdedores:** MAE = SL completo. La pérdida es total cuando se viola el sistema.

## G. REGLAS CLAVE DE MENTORES
- **PB Trading:** Setup más rápido = iFVG entre 9:30-9:37 AM NY. SMT solo como confluencia, nunca setup aislado. "Pérdidas buenas" son costo del negocio. No mover SL a BE prematuramente.
- **Supreme:** Validar sweep viendo caída de Open Interest (cierre de SL de minoristas). Confirmar SMC con Footprint/Order Flow, nunca ciegamente.
- **Fabio:** Liquidez real = profundidad de órdenes limitadas pasivas (DOM/Bookmap), no "stop losses dibujados". Absorción = reversión. Exhaustión = reversión. Sweep masivo = continuación.
- **Cramz:** Clasificar el día por Value Area (Balance/Imbalance). Confirmar con divergencia Delta/CVD y absorción en Footprint.
- **TJR:** 1% riesgo sagrado. Trading = ejecución de un skillset probabilístico, no "hacer dinero". FOMO y apego al resultado son los destructores.
- **BionicNQ:** R:R manda sobre todo. Si un FVG inmitigado acorta la expansión y el ratio es basura, NO se opera. BE prematuro sobre Monthly FVG = error gravísimo.

## H. JERARQUÍA DE TEMPORALIDADES (ANÁLISIS TOP-DOWN)
4H/1H (Macro/Bias) → 30m/15m (Intermedio/Zonas) → 5m/4m/3m (Transición/Confirmación) → 1m-2m (Micro/Gatillo de entrada)
- Si se forman múltiples iFVGs, priorizar temporalidad mayor.
- No buscar confirmaciones en TF > 5m para entrar.

## I. PERFIL DE VELAS FVG (PROBABILIDAD DE INVERSIÓN)
- **Fácil (Bajo compromiso):** R-G-R (bajista) o G-R-G (alcista). Alta prob. de convertirse en iFVG.
- **Moderado:** R-G-G o G-G-R. Requiere más confluencia.
- **Difícil (Fuerte compromiso):** G-G-G o R-R-R. Si se invierte, el movimiento contratendencia será explosivo.
