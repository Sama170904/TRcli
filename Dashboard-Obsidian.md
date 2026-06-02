---
title: Dashboard Obsidian
tags: [dashboard, analytics, metrics]
created: 2026-06-01
---

# 📈 Obsidian Trading Dashboard
Este tablero compila de forma automatizada (usando el plugin **Dataview**) las estadísticas e historial de tus sesiones de trading registradas en la carpeta `bitacoras/`.

---

## 📊 Estadísticas Generales de la Cuenta

```dataviewjs
let pages = dv.pages('"bitacoras"').filter(p => p.pnl !== undefined && p.file.name.includes("_session"));
let totalSessions = pages.length;
let totalPnL = pages.values.reduce((sum, p) => sum + parseFloat(p.pnl || 0), 0);
let wins = pages.filter(p => p.result === "WIN" || parseFloat(p.pnl) > 0).length;
let losses = pages.filter(p => p.result === "LOSS" || parseFloat(p.pnl) < 0).length;
let be = pages.filter(p => p.result === "BE" || parseFloat(p.pnl) === 0).length;
let winRate = totalSessions ? Math.round((wins / totalSessions) * 100) : 0;

let colorPnL = totalPnL >= 0 ? "green" : "red";
let signPnL = totalPnL >= 0 ? "+" : "";

dv.paragraph(`* **Balance Neto Total:** <span style="color:${colorPnL}; font-weight:bold">${signPnL}$${totalPnL.toFixed(2)} USD</span>
* **Total Sesiones Operadas:** \`${totalSessions}\`
* **Resultado de Sesiones (Win / Loss / BE):** <span style="color:green; font-weight:bold">${wins} WIN</span> / <span style="color:red; font-weight:bold">${losses} LOSS</span> / <span style="color:gray">${be} BE</span>
* **Win Rate de Sesión:** \`${winRate}%\``);
```

---

## 📅 Registro Histórico de Sesiones

```dataview
TABLE pnl AS "PnL Neto (USD)", result AS "Resultado", created AS "Fecha Registro"
FROM "bitacoras"
WHERE file.name = this.file.name OR contains(file.tags, "session")
SORT file.name DESC
```

---

## 💡 Instrucciones de Configuración en Obsidian
Para que este Dashboard y las plantillas funcionen correctamente dentro de Obsidian:

1. **Instalar Plugins de la Comunidad:**
   * Ve a `Configuración` ➔ `Complementos de la Comunidad` y busca:
     * **Dataview** (habilita la opción *"Enable JavaScript Queries"* en la configuración del plugin).
     * **Templater** (habilita la opción *"Trigger Templater on new file creation"*).
2. **Configurar las Plantillas:**
   * En la configuración de **Templater**, define tu carpeta de plantillas como `templates/`.
   * En la configuración de **Date format**, asegúrate de que use el formato estándar de tu sistema.
