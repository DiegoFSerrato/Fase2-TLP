# ------------------------------------------------------------
# FASE 2 - EVALUACION DEL CORPUS CON spaCy (ESPANOL)
# ------------------------------------------------------------
# spaCy NO ofrece por si mismo un veredicto "aceptada/rechazada".
# Esta comparacion implementa un criterio externo documentado:
#   C1. La entrada termina en un punto.
#   C2. spaCy la segmenta como una sola oracion.
#   C3. La raiz sintactica de esa oracion es verbal (VERB/AUX).
#   C4. La raiz tiene un sujeto explicito dependiente (nsubj/csubj).
#
# Si se cumplen las cuatro condiciones: aceptada; si no: rechazada.
# Este criterio NO es equivalente a la CFG y NO garantiza que la
# oracion sea gramaticalmente correcta en el espanol general.
#
# Instalacion (en Windows / VS Code):
#   python -m pip install -U spacy
#   python -m spacy download es_core_news_sm
#
# Ejecucion:
#   python evaluar_spacy_es.py
#
# Para que la comparacion sea reproducible, se almacenan las 45
# salidas completas, el modelo, las versiones y la regla utilizada.
# No se modifica el corpus ni los archivos del parser LL(1).
# ------------------------------------------------------------

import csv
import hashlib
import json
import platform
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).resolve().parent
CORPUS = BASE / "corpus_es_fase2.csv"
RESULTADOS = BASE / "resultados_spacy"
MODELO = "es_core_news_sm"
CRITERIO_ID = "spacy_raiz_verbal_sujeto_v1"
DESCRIPCION_CRITERIO = (
    "Aceptada si: termina en punto, spaCy detecta una sola oracion, "
    "su raiz es VERB o AUX, y posee sujeto explicito nsubj o csubj "
    "dependiente directamente de esa raiz. Si falta alguna condicion, rechazada."
)


def hora_local():
    """Hora de la computadora, con su desfase horario explicito."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def leer_corpus():
    with CORPUS.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        columnas = {"id", "nivel", "oracion", "etiqueta_esperada"}
        if not columnas.issubset(set(lector.fieldnames or [])):
            raise ValueError(f"Faltan columnas requeridas: {sorted(columnas)}")
        filas = list(lector)

    if len(filas) < 40:
        raise ValueError("El corpus contiene menos de 40 oraciones.")
    if len({fila['id'] for fila in filas}) != len(filas):
        raise ValueError("El corpus contiene identificadores repetidos.")
    for fila in filas:
        if fila["etiqueta_esperada"] not in {"aceptada", "rechazada"}:
            raise ValueError(f"Etiqueta invalida para {fila['id']}.")
        if fila["nivel"] not in {"1", "2", "3"}:
            raise ValueError(f"Nivel invalido para {fila['id']}.")
    return filas


def criterio_spacy(doc, texto):
    """
    Convierte el analisis de dependencias de spaCy en un veredicto.
    No depende de la etiqueta esperada ni de la tabla de la CFG.

    Devuelve: (aceptada, indicadores, motivo)
    """
    oraciones = list(doc.sents)
    termina_punto = texto.rstrip().endswith(".")
    es_una_oracion = len(oraciones) == 1

    raiz = oraciones[0].root if es_una_oracion else None
    raiz_verbal = bool(raiz is not None and raiz.pos_ in {"VERB", "AUX"})
    sujetos = []
    if raiz is not None:
        sujetos = [
            t for t in oraciones[0]
            if t.head.i == raiz.i
            and t.dep_.lower().split(":", 1)[0] in {"nsubj", "csubj"}
        ]

    tiene_sujeto = len(sujetos) > 0
    indicadores = {
        "termina_en_punto": termina_punto,
        "una_sola_oracion": es_una_oracion,
        "numero_oraciones_spacy": len(oraciones),
        "raiz_texto": raiz.text if raiz is not None else None,
        "raiz_pos": raiz.pos_ if raiz is not None else None,
        "raiz_verbal": raiz_verbal,
        "sujeto_explicito": tiene_sujeto,
        "sujetos_encontrados": [t.text for t in sujetos],
    }

    if not termina_punto:
        return False, indicadores, "Falta punto final."
    if not es_una_oracion:
        return False, indicadores, "spaCy no detecto exactamente una oracion."
    if not raiz_verbal:
        return False, indicadores, "La raiz sintactica no es VERB ni AUX."
    if not tiene_sujeto:
        return False, indicadores, "No se detecto sujeto explicito dependiente de la raiz."
    return True, indicadores, "Cumple las cuatro condiciones del criterio."


def dividir(a, b):
    return a / b if b else None


def calcular_metricas(registros):
    vp = sum(x["esperado"] == "aceptada" and x["obtenido"] == "aceptada" for x in registros)
    fp = sum(x["esperado"] == "rechazada" and x["obtenido"] == "aceptada" for x in registros)
    fn = sum(x["esperado"] == "aceptada" and x["obtenido"] == "rechazada" for x in registros)
    vn = sum(x["esperado"] == "rechazada" and x["obtenido"] == "rechazada" for x in registros)
    return {
        "total": len(registros),
        "VP": vp, "FP": fp, "FN": fn, "VN": vn,
        "precision": dividir(vp, vp + fp),
        "recall": dividir(vp, vp + fn),
        "tasa_rechazo_correcto": dividir(vn, vn + fp),
        "exactitud": dividir(vp + vn, len(registros)),
    }


def ejecutar():
    try:
        import spacy
    except ImportError as e:
        raise SystemExit(
            "Falta spaCy. Ejecuta: python -m pip install -U spacy"
        ) from e

    try:
        nlp = spacy.load(MODELO)
    except OSError as e:
        raise SystemExit(
            f"Falta el modelo {MODELO}. Ejecuta: python -m spacy download {MODELO}"
        ) from e

    if "parser" not in nlp.pipe_names:
        raise SystemExit("El modelo cargado no dispone del componente 'parser'.")

    filas = leer_corpus()
    # Carpeta distinta por corrida: evita sobrescribir evidencias originales.
    inicio = hora_local()
    id_corrida = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    salida = RESULTADOS / id_corrida
    salida.mkdir(parents=True, exist_ok=False)

    registros = []
    ruta_logs = salida / "logs_spacy.jsonl"
    with ruta_logs.open("w", encoding="utf-8") as f:
        for fila in filas:
            doc = nlp(fila["oracion"])
            aceptada, indicadores, motivo = criterio_spacy(doc, fila["oracion"])
            obtenido = "aceptada" if aceptada else "rechazada"
            esperado = fila["etiqueta_esperada"]
            registro = {
                "id": fila["id"],
                "nivel": int(fila["nivel"]),
                "oracion": fila["oracion"],
                "esperado": esperado,
                "obtenido": obtenido,
                "coincide": esperado == obtenido,
                "criterio_id": CRITERIO_ID,
                "indicadores": indicadores,
                "motivo": motivo,
                "tokens_spacy": [
                    {
                        "texto": t.text,
                        "lema": t.lemma_,
                        "pos": t.pos_,
                        "etiqueta": t.tag_,
                        "dependencia": t.dep_,
                        "cabeza": t.head.text,
                        "cabeza_indice": t.head.i,
                        "morfologia": str(t.morph),
                        "indice": t.i,
                    }
                    for t in doc
                ],
                "timestamp_local": hora_local(),
            }
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
            registros.append(registro)
            marca = "OK" if registro["coincide"] else "DIFERENCIA"
            print(f"[{marca}] {fila['id']} nivel {fila['nivel']}: {obtenido.upper()} - {fila['oracion']}")

    columnas = [
        "id", "nivel", "oracion", "esperado", "obtenido",
        "coincide", "motivo", "criterio_id", "timestamp_local",
    ]
    with (salida / "resultados_spacy.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as archivo:
        w = csv.DictWriter(archivo, fieldnames=columnas)
        w.writeheader()
        for r in registros:
            w.writerow({k: r[k] for k in columnas})

    resumen = {
        "total": calcular_metricas(registros),
        "por_nivel": {
            str(n): calcular_metricas([r for r in registros if r["nivel"] == n])
            for n in (1, 2, 3)
        },
        "criterio_id": CRITERIO_ID,
        "criterio_texto": DESCRIPCION_CRITERIO,
        "etiquetas_referencia": "aceptacion/rechazo segun la CFG y el corpus etiquetado",
        "advertencia": (
            "spaCy realiza analisis lingüistico; el veredicto procede del "
            "criterio externo. Las diferencias no implican por si solas "
            "que la oracion sea gramaticalmente incorrecta."
        ),
    }
    (salida / "metricas_spacy.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    metadatos = {
        "inicio_local": inicio,
        "final_local": hora_local(),
        "configuracion_horaria": "dispositivo",
        "python": platform.python_version(),
        "spacy": spacy.__version__,
        "modelo": MODELO,
        "modelo_version": nlp.meta.get("version"),
        "pipeline": nlp.pipe_names,
        "criterio_id": CRITERIO_ID,
        "criterio_texto": DESCRIPCION_CRITERIO,
        "numero_oraciones": len(registros),
        "corpus_sha256": sha256(CORPUS),
        "script_sha256": sha256(Path(__file__).resolve()),
    }
    (salida / "metadatos_spacy.json").write_text(
        json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nRESULTADOS DE spaCy (referencia: CFG)")
    print(json.dumps(resumen["total"], ensure_ascii=False, indent=2))
    print("Evidencias originales guardadas en:", salida)
    print("No se modificaron el corpus, lexer, parser ni la tabla LL(1).")


if __name__ == "__main__":
    ejecutar()
