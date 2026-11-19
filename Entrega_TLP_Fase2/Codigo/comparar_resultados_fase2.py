"""Comparacion reproducible de cinco evaluaciones sobre el corpus Fase 2.

No utiliza ninguna API: carga exclusivamente resultados ya guardados.

Ejemplo:
python comparar_resultados_fase2.py --corpus corpus_es_fase2.csv --parser resultados_parser_es.csv --spacy resultados_spacy.csv --nltk resultados_nltk.csv --llm resultados_llm.csv

Requisitos para graficas: matplotlib (pip install matplotlib).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ETIQUETAS = {"aceptada", "rechazada"}
METODOS = ["Parser LL(1)", "spaCy + criterio", "NLTK + criterio", "LLM zero-shot", "LLM few-shot"]


def leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def escribir_csv(ruta: Path, filas: list[dict], columnas: list[str]) -> None:
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_referencia(ruta: Path) -> tuple[dict[str, dict], list[str]]:
    filas = leer_csv(ruta)
    ref = {}
    orden = []
    for fila in filas:
        id_ = fila["id"]
        if id_ in ref:
            raise ValueError(f"ID duplicado en corpus: {id_}")
        if fila["etiqueta_esperada"] not in ETIQUETAS:
            raise ValueError(f"Etiqueta invalida en corpus: {id_}")
        ref[id_] = fila
        orden.append(id_)
    if not ref:
        raise ValueError("El corpus esta vacio")
    return ref, orden


def cargar_predicciones(ruta: Path, ref: dict[str, dict], modo: str | None = None) -> dict[str, str]:
    pred = {}
    for fila in leer_csv(ruta):
        if modo is not None and fila["modo"] != modo:
            continue
        id_ = fila["id"]
        if id_ in pred:
            raise ValueError(f"ID repetido para el mismo metodo en {ruta}: {id_}")
        if id_ not in ref:
            raise ValueError(f"ID fuera del corpus en {ruta}: {id_}")
        if fila["oracion"] != ref[id_]["oracion"] or fila["nivel"] != ref[id_]["nivel"]:
            raise ValueError(f"Oracion/nivel no coinciden con el corpus: {ruta} {id_}")
        if fila["esperado"] != ref[id_]["etiqueta_esperada"]:
            raise ValueError(f"Etiqueta de referencia distinta: {ruta} {id_}")
        if fila.get("estado", "ok") != "ok":
            raise ValueError(f"Resultado con error o sin respuesta: {ruta} {id_}")
        if fila["obtenido"] not in ETIQUETAS:
            raise ValueError(f"Veredicto no valido: {ruta} {id_}")
        pred[id_] = fila["obtenido"]
    if set(pred) != set(ref):
        faltantes = sorted(set(ref) - set(pred))
        raise ValueError(f"Archivo {ruta} incompleto. IDs faltantes: {faltantes}")
    return pred


def medir(ids: list[str], ref: dict, pred: dict) -> dict:
    vp = sum(ref[i]["etiqueta_esperada"] == "aceptada" and pred[i] == "aceptada" for i in ids)
    fp = sum(ref[i]["etiqueta_esperada"] == "rechazada" and pred[i] == "aceptada" for i in ids)
    fn = sum(ref[i]["etiqueta_esperada"] == "aceptada" and pred[i] == "rechazada" for i in ids)
    vn = sum(ref[i]["etiqueta_esperada"] == "rechazada" and pred[i] == "rechazada" for i in ids)

    def ratio(a: int, b: int) -> float | None:
        return a / b if b else None

    precision = ratio(vp, vp + fp)
    recall = ratio(vp, vp + fn)
    return {
        "total": len(ids), "VP": vp, "FP": fp, "FN": fn, "VN": vn,
        "precision": precision,
        "recall": recall,
        "rechazo_correcto": ratio(vn, vn + fp),
        "exactitud": ratio(vp + vn, len(ids)),
        "f1": ratio(2 * vp, 2 * vp + fp + fn),
    }


def porcentaje(valor: float | None) -> str:
    return "" if valor is None else f"{100 * valor:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, default=Path("corpus_es_fase2.csv"))
    ap.add_argument("--parser", type=Path, default=Path("resultados_parser_es.csv"))
    ap.add_argument("--spacy", type=Path, default=Path("resultados_spacy.csv"))
    ap.add_argument("--nltk", type=Path, default=Path("resultados_nltk.csv"))
    ap.add_argument("--llm", type=Path, default=Path("resultados_llm.csv"))
    ap.add_argument("--salida", type=Path, default=Path("comparacion_fase2"))
    ap.add_argument("--sin-graficas", action="store_true")
    a = ap.parse_args()
    origenes = [a.corpus, a.parser, a.spacy, a.nltk, a.llm]
    for p in origenes:
        if not p.is_file():
            raise FileNotFoundError(f"Falta el archivo: {p}")
    ref, orden = cargar_referencia(a.corpus)
    pred = {
        "Parser LL(1)": cargar_predicciones(a.parser, ref),
        "spaCy + criterio": cargar_predicciones(a.spacy, ref),
        "NLTK + criterio": cargar_predicciones(a.nltk, ref),
        "LLM zero-shot": cargar_predicciones(a.llm, ref, "zero-shot"),
        "LLM few-shot": cargar_predicciones(a.llm, ref, "few-shot"),
    }
    a.salida.mkdir(parents=True, exist_ok=True)
    resumen = []
    por_nivel = []
    medidas = {}
    for metodo in METODOS:
        m = medir(orden, ref, pred[metodo])
        medidas[metodo] = m
        resumen.append({"metodo": metodo, **{
            k: porcentaje(v) if k in {"precision", "recall", "rechazo_correcto", "exactitud", "f1"} else v
            for k, v in m.items()
        }})
        for nivel in sorted({x["nivel"] for x in ref.values()}, key=int):
            ids = [i for i in orden if ref[i]["nivel"] == nivel]
            lm = medir(ids, ref, pred[metodo])
            por_nivel.append({"metodo": metodo, "nivel": nivel, **{
                k: porcentaje(v) if k in {"precision", "recall", "rechazo_correcto", "exactitud", "f1"} else v
                for k, v in lm.items()
            }})

    medidas_campos = ["total", "VP", "FP", "FN", "VN", "precision", "recall", "rechazo_correcto", "exactitud", "f1"]
    escribir_csv(a.salida / "comparacion_metricas.csv", resumen, ["metodo", *medidas_campos])
    escribir_csv(a.salida / "comparacion_por_nivel.csv", por_nivel, ["metodo", "nivel", *medidas_campos])

    matriz = []
    errores = []
    for i in orden:
        fila = {"id": i, "nivel": ref[i]["nivel"], "oracion": ref[i]["oracion"], "esperado": ref[i]["etiqueta_esperada"]}
        for metodo in METODOS:
            obtenido = pred[metodo][i]
            fila[metodo] = obtenido
            if obtenido != fila["esperado"]:
                errores.append({"id": i, "nivel": fila["nivel"], "oracion": fila["oracion"], "metodo": metodo, "esperado": fila["esperado"], "obtenido": obtenido, "tipo_error": "FP" if fila["esperado"] == "rechazada" else "FN"})
        matriz.append(fila)
    escribir_csv(a.salida / "comparacion_oracion_por_oracion.csv", matriz, ["id", "nivel", "oracion", "esperado", *METODOS])
    escribir_csv(a.salida / "errores_comparados.csv", errores, ["id", "nivel", "oracion", "metodo", "esperado", "obtenido", "tipo_error"])

    comprobacion = {"archivos_sha256": {p.name: sha256(p) for p in origenes}, "numero_oraciones": len(ref), "metodos": medidas}
    (a.salida / "resultados_recalculados.json").write_text(json.dumps(comprobacion, ensure_ascii=False, indent=2), encoding="utf-8")

    tabla_md = ["| Metodo | VP | FP | FN | VN | Precision | Recall | Rechazo correcto | Exactitud |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for metodo in METODOS:
        m = medidas[metodo]
        tabla_md.append(f"| {metodo} | {m['VP']} | {m['FP']} | {m['FN']} | {m['VN']} | " + " | ".join(porcentaje(m[k]) + "%" if m[k] is not None else "N/D" for k in ("precision", "recall", "rechazo_correcto", "exactitud")) + " |")
    conclusiones = [
        "# Comparacion experimental - TLP Fase 2",
        "",
        "Referencia: etiquetas de aceptacion/rechazo de la CFG para las mismas 45 oraciones.",
        "Los veredictos de spaCy y NLTK proceden de criterios externos definidos previamente; no son una funcion nativa de aceptacion/rechazo.",
        "",
        *tabla_md,
        "",
        "## Interpretacion y limites",
        "",
        "- La referencia gold se construyo segun el alcance de la CFG. Por ello la coincidencia del parser LL(1) con sus propias reglas no equivale a comprender todo el español.",
        "- Las discrepancias de spaCy y NLTK incluyen diferencias de cobertura y de criterio de equivalencia, no necesariamente errores de analisis linguistico.",
        "- Zero-shot y few-shot son una ejecucion por oracion y condicion; no se estima variabilidad entre ejecuciones. Few-shot incluye seis ejemplos externos al corpus.",
        "- Una clasificacion correcta no garantiza una explicacion correcta. Consultar logs de la API para errores de justificacion.",
        "- En el nivel 1 no hay rechazos de referencia: la tasa de rechazo correcto es indefinida (N/D), no cero.",
    ]
    (a.salida / "resumen_comparativo.md").write_text("\n".join(conclusiones) + "\n", encoding="utf-8")

    if not a.sin_graficas:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Instala matplotlib con: python -m pip install matplotlib; o ejecuta --sin-graficas") from exc
        etiquetas = ["LL(1)", "spaCy", "NLTK", "LLM 0-shot", "LLM few-shot"]
        campos = [("precision", "Precision"), ("recall", "Recall"), ("rechazo_correcto", "Rechazo correcto"), ("exactitud", "Exactitud")]
        x = np.arange(len(etiquetas))
        ancho = 0.19
        fig, ax = plt.subplots(figsize=(12, 5.7))
        for j, (campo, nombre) in enumerate(campos):
            alturas = [medidas[met][campo] * 100 if medidas[met][campo] is not None else float("nan") for met in METODOS]
            ax.bar(x + (j - 1.5) * ancho, alturas, ancho, label=nombre)
        ax.set_xticks(x, etiquetas)
        ax.set_ylabel("Porcentaje (%)")
        ax.set_ylim(0, 109)
        ax.set_title("Evaluacion de cinco enfoques frente a la CFG (45 oraciones)")
        ax.legend(loc="lower right", ncol=2)
        ax.grid(axis="y", alpha=0.22)
        fig.tight_layout()
        fig.savefig(a.salida / "grafico_metricas.png", dpi=185)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5.8))
        niveles = ["Nivel 1", "Nivel 2", "Nivel 3"]
        xx = np.arange(3)
        width = .145
        for j, met in enumerate(METODOS):
            valores = [medir([i for i in orden if ref[i]["nivel"] == str(k)], ref, pred[met])["exactitud"] * 100 for k in (1,2,3)]
            ax.bar(xx + (j - 2) * width, valores, width, label=etiquetas[j])
        ax.set_xticks(xx, niveles)
        ax.set_ylabel("Exactitud (%)")
        ax.set_ylim(0, 110)
        ax.set_title("Exactitud por nivel de complejidad")
        ax.legend(ncol=3, loc="upper right")
        ax.grid(axis="y", alpha=.22)
        fig.tight_layout()
        fig.savefig(a.salida / "grafico_por_nivel.png", dpi=185)
        plt.close(fig)

    print("AUDITORIA APROBADA: mismos 45 ID, oraciones y etiquetas en los cinco enfoques")
    for m in METODOS:
        x = medidas[m]
        print(f"  {m:18s}: exactitud={porcentaje(x['exactitud'])}% VP={x['VP']} FP={x['FP']} FN={x['FN']} VN={x['VN']}")
    print(f"Archivos generados en: {a.salida.resolve()}")


if __name__ == "__main__":
    main()
