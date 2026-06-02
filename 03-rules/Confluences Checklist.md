---
title: Confluences Checklist
tags: [confluences, checklist, setup-quality, rules]
created: 2024-01-15
tokens: 600
---

# Confluences Checklist

## Definition
The Confluences Checklist is the **real-time scoring system used before entering any trade**. Each item is a confluence — a factor that independently supports the trade direction. More confluences = higher probability. A minimum threshold must be met; below it, skip the trade.

**Scoring:** Confirm requirements first, then calculate points. 3 points or fewer = skip. 4–5 = proceed with caution. 6+ = A+ setup.

## Rules

### Group 1 — HTF Context (Contexto Macro)
*Required structural foundations:*
- [ ] **[[Higher Timeframe Bias]] is clear** — 4H/1D structure aligns with trade direction (Required)
- [ ] **Zone Context** — Entry is in a [[Discount Zone]] for longs, or [[Premium Zone]] for shorts (Required)
- [ ] **PD Array Alignment** — Entry zone aligns with HTF OB, FVG, or Breaker (+1 point)

### Group 2 — Levels & Liquidity (Zonas de Interés)
*Where liquidity or imbalance rests:*
- [ ] **[[Liquidity Sweep]]** occurred at a relevant key level (+1 point)
- [ ] **[[Equal Highs]] or [[Equal Lows]] swept** (tapped prior to move) (+1 point)
- [ ] **[[Session Highs - Lows|Previous Day High/Low]]** swept (+0.5 point)
- [ ] **[[Asian Session Range]]** level swept at London open (+0.5 point)

### Group 3 — LTF Confirmation (Gatillo Micro)
*Low timeframe validation and trigger:*
- [ ] **[[Displacement Candle]]** followed the sweep, showing institutional entry (+1 point)
- [ ] **[[Fair Value Gap]] or [[IFVG]]** is the active entry zone (+1 point)
- [ ] **[[Change of Character]] or MSS** confirmed the reversal on lower TF (+1 point)
- [ ] **[[Order Block (Bullish)|Order Block]] alignment** on entry timeframe (+1 point)
- [ ] **[[SMT Divergence]]** present on correlated pair (MES vs MNQ) (+1 point)

### Group 4 — Timing & Session (Horario y Noticias)
*Timing filters:*
- [ ] **[[Kill Zones|Active Kill Zone]]** — Trade executed during London or NY AM Open (Required)
- [ ] **[[Kill Zones|Power of Three]]** phase is aligned (+1 point)
- [ ] **News Filter** — No red folder news within 5 minutes of execution (+0.5 point)

### Scoring Key
- **Required items missing:** Do not enter — structural requirements not met
- **Score 0–3:** Skip
- **Score 4–5:** Acceptable setup — standard 1% risk
- **Score 6–8:** A+ setup — standard 1% risk (do not increase size)
- **Score 9+:** Exceptional — still only 1% risk; note it for journaling

## Connexions
- [[Entry Rules]] — the parent execution process; this checklist lives inside Step 4
- [[Higher Timeframe Bias]] — Group 1 required item; the single most important factor
- [[Kill Zones]] — Group 4 required item; timing is structural, not optional
- [[IFVG Setup]] — use this checklist before every IFVG entry
- [[SMT Divergence]] — high-value Group 3 confirmation; adds +1 to any setup
- [[Pre-Trade Checklist]] — the broader daily routine that precedes this checklist
- [[Best Setups]] — A+ setups score 6+ on this checklist every time
- [[Trade Journal Template]] — log the confluence score for every trade taken
