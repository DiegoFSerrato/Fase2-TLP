# ------------------------------------------------------------
# FASE 2 - PRUEBAS Y REGISTRO REPRODUCIBLE DEL PARSER ESPANOL
# ------------------------------------------------------------
# Lee el corpus etiquetado, ejecuta EL MISMO parser_es.py del
# proyecto, compara los resultados con las etiquetas esperadas,
# calcula metricas y conserva las salidas originales.
#
# Ejecucion:
#   python pruebas_parser_es.py
#
# Requiere PLY, porque importa el lexer real del proyecto.
# La tabla LL(1) es la ya existente: NO se reconstruye.
# ------------------------------------------------------------

import csv
import hashlib
import json
import platform
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ply
from lexer_es import tokenizar
from parser_es import analizar


CARPETA = Path(__file__).resolve().parent
ARCHIVO_CORPUS = CARPETA / "corpus_es_fase2.csv"
CARPETA_RESULTADOS = CARPETA / "resultados_es"


# ------------------------------------------------------------
# 1. HERRAMIENTAS AUXILIARES
# ------------------------------------------------------------

MODO_HORA = "dispositivo"
ZONA_EL_SALVADOR = timezone(timedelta(hours=-6))


def fecha_local():
    """Devuelve un timestamp con desfase horario explicito."""
    if MODO_HORA == "dispositivo":
        momento = datetime.now().astimezone()
    else:
        raise ValueError("MODO_HORA debe ser 'dispositivo'.")
    return momento.isoformat(timespec="seconds")


def hash_sha256(ruta):
    """Identifica exactamente el contenido de un archivo."""
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def leer_corpus():
    """Carga el corpus y verifica su formato y etiquetas."""
    if not ARCHIVO_CORPUS.exists():
        raise FileNotFoundError(f"No se encontro el corpus: {ARCHIVO_CORPUS}")

    with ARCHIVO_CORPUS.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        requeridas = {
            "id", "nivel", "oracion", "etiqueta_esperada",
            "etapa_esperada", "estructura_esperada", "justificacion"
        }
        if not requeridas.issubset(lector.fieldnames or []):
            raise ValueError("Faltan columnas obligatorias en corpus_es_fase2.csv")
        filas = list(lector)

    if len(filas) < 40:
        raise ValueError("El corpus debe contener al menos 40 oraciones.")

    ids = set()
    for fila in filas:
        identificador = fila["id"]
        if not identificador or identificador in ids:
            raise ValueError(f"ID vacio o repetido: {identificador!r}")
        ids.add(identificador)
        if fila["nivel"] not in {"1", "2", "3"}:
            raise ValueError(f"Nivel invalido en {identificador}")
        if fila["etiqueta_esperada"] not in {"aceptada", "rechazada"}:
            raise ValueError(f"Etiqueta invalida en {identificador}")
        if fila["etapa_esperada"] not in {"aceptada", "lexico", "sintactico"}:
            raise ValueError(f"Etapa esperada invalida en {identificador}")
        if fila["etiqueta_esperada"] == "aceptada" and fila["etapa_esperada"] != "aceptada":
            raise ValueError(f"Etiquetas inconsistentes en {identificador}")
        if fila["etiqueta_esperada"] == "rechazada" and fila["etapa_esperada"] == "aceptada":
            raise ValueError(f"Etiquetas inconsistentes en {identificador}")
        if not fila["oracion"].strip():
            raise ValueError(f"Oracion vacia en {identificador}")

    return filas


def division_segura(numerador, denominador):
    """Evita calcular una tasa con denominador cero."""
    if denominador == 0:
        return None
    return numerador / denominador


def metricas(registros):
    """Calcula matriz de confusion y las metricas del informe."""
    tp = sum(r["esperado"] == "aceptada" and r["obtenido"] == "aceptada" for r in registros)
    fp = sum(r["esperado"] == "rechazada" and r["obtenido"] == "aceptada" for r in registros)
    fn = sum(r["esperado"] == "aceptada" and r["obtenido"] == "rechazada" for r in registros)
    tn = sum(r["esperado"] == "rechazada" and r["obtenido"] == "rechazada" for r in registros)

    return {
        "total": len(registros),
        "VP": tp,
        "FP": fp,
        "FN": fn,
        "VN": tn,
        "precision": division_segura(tp, tp + fp),
        "recall": division_segura(tp, tp + fn),
        "tasa_rechazo_correcto": division_segura(tn, tn + fp),
        "exactitud": division_segura(tp + tn, len(registros)),
    }


def formato_porcentaje(valor):
    return "N/D" if valor is None else f"{valor * 100:.1f}%"


# ------------------------------------------------------------
# 2. EJECUTAR TODO EL CORPUS
# ------------------------------------------------------------

def ejecutar_pruebas():
    filas = leer_corpus()
    CARPETA_RESULTADOS.mkdir(exist_ok=True)

    archivo_csv = CARPETA_RESULTADOS / "resultados_parser_es.csv"
    archivo_log = CARPETA_RESULTADOS / "logs_parser_es.jsonl"
    archivo_metricas = CARPETA_RESULTADOS / "metricas_parser_es.json"
    archivo_metadatos = CARPETA_RESULTADOS / "metadatos_ejecucion.json"

    registros = []
    inicio = fecha_local()

    # Se guarda la salida original de cada prueba en un archivo JSONL.
    with archivo_log.open("w", encoding="utf-8") as salida_log:
        for fila in filas:
            texto = fila["oracion"]

            # Ejecutar el parser REAL del proyecto (incluye lexer).
            aceptada, mensajes = analizar(texto, mostrar_pasos=False)

            # Recuperar los tokens para registrar evidencia del lexer.
            tokens, errores_lexicos = tokenizar(texto)

            obtenido = "aceptada" if aceptada else "rechazada"
            if aceptada:
                etapa_obtenida = "aceptada"
            elif errores_lexicos:
                etapa_obtenida = "lexico"
            else:
                etapa_obtenida = "sintactico"

            esperado = fila["etiqueta_esperada"]
            coincide = obtenido == esperado
            etapa_coincide = etapa_obtenida == fila["etapa_esperada"]

            registro = {
                "id": fila["id"],
                "nivel": int(fila["nivel"]),
                "oracion": texto,
                "esperado": esperado,
                "obtenido": obtenido,
                "etapa_esperada": fila["etapa_esperada"],
                "etapa_obtenida": etapa_obtenida,
                "coincide": coincide,
                "etapa_coincide": etapa_coincide,
                "estructura_esperada": fila["estructura_esperada"],
                "justificacion": fila["justificacion"],
                "tokens": [{"tipo": t.type, "valor": t.value, "linea": t.lineno} for t in tokens],
                "errores_lexicos": errores_lexicos,
                "mensajes_parser": mensajes,
                "timestamp_local": fecha_local(),
            }
            registros.append(registro)
            salida_log.write(json.dumps(registro, ensure_ascii=False) + "\n")

            estado = "OK" if coincide else "FALLO"
            observacion = "" if etapa_coincide else " [REVISAR ETAPA]"
            print(f"[{estado}] {fila['id']} (nivel {fila['nivel']}): {obtenido.upper()}{observacion} — {texto}")
            if not coincide or not etapa_coincide:
                for mensaje in mensajes:
                    print("      ", mensaje)

    # CSV sintetico para abrir con Excel y graficar resultados.
    columnas = [
        "id", "nivel", "oracion", "esperado", "obtenido",
        "etapa_esperada", "etapa_obtenida", "coincide", "etapa_coincide",
        "estructura_esperada", "justificacion", "timestamp_local"
    ]
    with archivo_csv.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for registro in registros:
            escritor.writerow({clave: registro[clave] for clave in columnas})

    resumen = {
        "total": metricas(registros),
        "por_nivel": {
            str(nivel): metricas([r for r in registros if r["nivel"] == nivel])
            for nivel in (1, 2, 3)
        },
        "discordancias_etapa": sum(not r["etapa_coincide"] for r in registros),
        "criterio": "positivo=oracion aceptada por la CFG; negativo=oracion rechazada por la CFG",
        "formula_precision": "VP / (VP + FP)",
        "formula_recall": "VP / (VP + FN)",
        "formula_tasa_rechazo_correcto": "VN / (VN + FP)",
    }
    archivo_metricas.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    archivos_base = [
        "corpus_es_fase2.csv", "lexer_es.py", "parser_es.py",
        "gramatica_es_ll1.py", "tabla_es_ll1.py"
    ]
    metadatos = {
        "ejecucion_inicio_local": inicio,
        "ejecucion_final_local": fecha_local(),
        "configuracion_horaria": MODO_HORA,
        "zona_horaria": ("El Salvador (UTC-06:00)" if MODO_HORA == "el_salvador" else "Zona horaria del dispositivo"),
        "python": platform.python_version(),
        "ply": getattr(ply, "__version__", "no especificada"),
        "archivos_sha256": {
            nombre: hash_sha256(CARPETA / nombre)
            for nombre in archivos_base
            if (CARPETA / nombre).exists()
        },
        "numero_de_oraciones": len(registros),
        "tabla": "tabla_es_ll1.py (fija; solo lectura durante analisis)",
        "observacion": "Los timestamps locales incluyen su desfase horario; cambian en cada ejecucion, pero las etiquetas y metricas se reproducen con los mismos archivos.",
    }
    archivo_metadatos.write_text(json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8")

    total = resumen["total"]
    print("\n" + "=" * 78)
    print("RESULTADOS GENERALES - PARSER LL(1) ESPANOL")
    print("=" * 78)
    print(f"Total: {total['total']} | VP: {total['VP']} | FP: {total['FP']} | FN: {total['FN']} | VN: {total['VN']}")
    print("Precision:", formato_porcentaje(total["precision"]))
    print("Cobertura / recall:", formato_porcentaje(total["recall"]))
    print("Tasa de rechazo correcto:", formato_porcentaje(total["tasa_rechazo_correcto"]))
    print("Exactitud:", formato_porcentaje(total["exactitud"]))
    print("Discordancias de etapa lexica/sintactica:", resumen["discordancias_etapa"])
    print("\nEVIDENCIAS GENERADAS EN:", CARPETA_RESULTADOS)
    print(" -", archivo_csv.name)
    print(" -", archivo_log.name)
    print(" -", archivo_metricas.name)
    print(" -", archivo_metadatos.name)

    # El proceso termina con error si hay discrepancias; util en evaluacion.
    return all(r["coincide"] and r["etapa_coincide"] for r in registros)


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar_pruebas() else 1)
