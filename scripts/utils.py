#!/usr/bin/env python3
# encoding: utf-8
"""Módulo de utilidades compartidas para los scripts del Trading Journal.

Contiene funciones de validación de datos, parseo seguro, y utilidades
comunes para evitar duplicación de código entre scripts."""

import sys
import json
import subprocess


def safe_float(value, default=0.0):
    """Parsea un valor a float de forma segura, retornando default si falla."""
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default


def validate_trade(trade):
    """Valida campos obligatorios de un trade del journal.json.
    Retorna True si el trade es válido, False si tiene campos faltantes."""
    required = ["id", "datetime", "instrument", "direction", "entry", "sl", "result"]
    missing = [f for f in required if not trade.get(f)]
    if missing:
        print(f"Advertencia: Trade {trade.get('id', '?')} tiene campos vacíos: {missing}", file=sys.stderr)
        return False
    if trade["result"] not in ("Win", "Loss", "BE"):
        print(f"Advertencia: Trade {trade.get('id')} tiene result inválido: '{trade['result']}'", file=sys.stderr)
        return False
    return True


def run_node_command(mcp_cli_path, args, timeout=15):
    """Ejecuta un comando Node.js con manejo robusto de errores.
    Retorna (success: bool, data: dict/None, error_msg: str/None)"""
    try:
        result = subprocess.run(
            ["node", mcp_cli_path] + args,
            capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return False, None, "'node' no está instalado o no está en el PATH del sistema."
    except subprocess.TimeoutExpired:
        return False, None, f"Timeout ({timeout}s) al ejecutar comando Node."
    except Exception as e:
        return False, None, f"Error inesperado: {type(e).__name__}: {e}"

    if result.returncode != 0 or not result.stdout.strip():
        return False, None, result.stderr or "Sin respuesta del servidor."

    try:
        data = json.loads(result.stdout)
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f"Respuesta JSON inválida: {e}"


CDP_GET_DRAWINGS_JS = r"""(function(){try{var api=window.TradingViewApi._activeChartWidgetWV.value();var all=api.getAllShapes();var drawings=[];for(var i=0;i<all.length;i++){var s=all[i];var shape=api.getShapeById(s.id);if(shape){var pts=null;try{pts=shape.getPoints();}catch(e){}if(!pts){try{pts=shape.points();}catch(e){}}var props=null;try{props=shape.getProperties();}catch(e){}if(!props){try{props=shape.properties();}catch(e){}}drawings.push({id:s.id,name:s.name,points:pts,properties:props});}}return {success:true,drawings:drawings};}catch(e){return {success:false,error:e.message};}})()"""


def extract_cdp_drawings(mcp_cli_path):
    """Extrae los dibujos manuales del gráfico activo de TradingView vía CDP.
    Retorna una lista de shapes o lista vacía si falla."""
    success, data, error = run_node_command(mcp_cli_path, ["ui", "eval", CDP_GET_DRAWINGS_JS])
    if not success:
        print(f"Error extrayendo dibujos CDP: {error}", file=sys.stderr)
        return []

    shapes = []
    if data and data.get("success"):
        if "result" in data and isinstance(data["result"], dict):
            shapes = data["result"].get("drawings", [])
        else:
            shapes = data.get("drawings", [])
    return shapes
