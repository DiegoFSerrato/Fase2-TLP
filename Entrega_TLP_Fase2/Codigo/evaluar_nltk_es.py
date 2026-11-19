# ------------------------------------------------------------
# FASE 2 - EVALUACION EXPERIMENTAL CON NLTK (ESPANOL)
# ------------------------------------------------------------
# NLTK NO acepta/rechaza oraciones automaticamente.
# Este script realiza un analisis morfosintactico con NLTK y
# aplica un criterio EXTERNO previamente definido:
#
#   C1. La entrada termina en punto.
#   C2. NLTK segmenta exactamente una oracion.
#   C3. El etiquetador identifica al menos un verbo finito.
#   C4. Antes del primer verbo finito aparece un sintagma nominal
#       candidato a sujeto (identificado por RegexpParser).
#
# Si todas las condiciones se cumplen: 'aceptada'.
# En otro caso: 'rechazada'. Esta decision es NUESTRA, no nativa
# de NLTK ni equivalente a reconocer la CFG del parser LL(1).
#
# Analisis empleado:
#   - NLTK sent_tokenize / wordpunct_tokenize.
#   - Etiquetador POS BigramTagger -> UnigramTagger -> DefaultTagger,
#     entrenado EXCLUSIVAMENTE en el corpus espanol CESS-ESP.
#   - nltk.RegexpParser para identificar sintagmas nominales.
#   - El corpus de evaluacion de 45 oraciones NO se usa para entrenar.
#
# Instalacion:
#   python -m pip install nltk
#   python -m nltk.downloader cess_esp punkt_tab
# Ejecucion:
#   python evaluar_nltk_es.py
#
# Crea una carpeta nueva por ejecucion con CSV, logs JSONL,
# metricas JSON y metadatos JSON. No modifica el corpus ni el
# parser, lexer, gramatica o tabla LL(1) existentes.
# ------------------------------------------------------------

import csv
import hashlib
import json
import platform
import random
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
CORPUS = BASE / "corpus_es_fase2.csv"
CARPETA_RESULTADOS = BASE / "resultados_nltk"
SEMILLA = 2026
PORCENTAJE_ENTRENAMIENTO = 0.80
CRITERIO_ID = "nltk_pos_sintagma_sujeto_v1"
DESCRIPCION_CRITERIO = (
    "Aceptada si termina en punto, NLTK identifica una sola oracion, "
    "detecta un verbo finito y existe un sintagma nominal candidato "
    "a sujeto antes del primer verbo finito. En otro caso, rechazada."
)

# Gramática de CHUNKS sobre etiquetas POS generales de NLTK.
# No representa la CFG del parser propio: solo detecta grupos nominales.
GRAMATICA_CHUNKS = r"""
SN:
    {<DET><ADJ>*<NOUN><ADJ>*}
    {<PRON>}
    {<NOUN><ADJ>*}
"""


def hora_local():
    """Registra hora del dispositivo con el desfase horario explicito."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def leer_corpus():
    with CORPUS.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        obligatorias = {"id", "nivel", "oracion", "etiqueta_esperada"}
        if not obligatorias.issubset(set(lector.fieldnames or [])):
            raise ValueError("El CSV no contiene las columnas requeridas.")
        filas = list(lector)

    if len(filas) < 40:
        raise ValueError("El corpus tiene menos de 40 oraciones.")
    if len({r["id"] for r in filas}) != len(filas):
        raise ValueError("Hay identificadores de oraciones duplicados.")
    for r in filas:
        if r["etiqueta_esperada"] not in {"aceptada", "rechazada"}:
            raise ValueError(f"Etiqueta de referencia incorrecta: {r['id']}")
        if r["nivel"] not in {"1", "2", "3"}:
            raise ValueError(f"Nivel incorrecto: {r['id']}")
    return filas


def categoria_simple(tag):
    """Convierte etiquetas morfologicas EAGLES de CESS-ESP a POS generales."""
    if not tag or tag == "UNK":
        return "UNK"
    prefijo = tag[0].lower()
    return {
        "d": "DET", "n": "NOUN", "p": "PRON", "v": "VERB",
        "a": "ADJ", "r": "ADV", "s": "ADP", "f": "PUNCT",
        "c": "CONJ", "z": "NUM", "i": "INTJ",
    }.get(prefijo, "OTHER")


def es_verbo_finito(tag):
    """En EAGLES el tercer caracter indica el modo de la forma verbal."""
    if not tag or len(tag) < 3 or tag[0].lower() != "v":
        return False
    # i = indicativo; s = subjuntivo; m = imperativo; c = condicional.
    # No se aceptan infinitivo (n), gerundio (g), participio (p).
    return tag[2].lower() in {"i", "s", "m", "c"}


def construir_etiquetador(nltk, cess_esp):
    """Entrena el POS tagger con CESS-ESP, nunca con el corpus evaluado."""
    from nltk.tag import BigramTagger, DefaultTagger, UnigramTagger

    oraciones_corpus = []
    digest = hashlib.sha256()
    for oracion in cess_esp.tagged_sents():
        if not oracion:
            continue
        normalizada = []
        for palabra, etiqueta in oracion:
            palabra_norm = palabra.casefold()
            normalizada.append((palabra_norm, etiqueta))
            digest.update((palabra_norm + "\t" + etiqueta + "\n").encode("utf-8"))
        oraciones_corpus.append(normalizada)
        digest.update(b"\n")

    indices = list(range(len(oraciones_corpus)))
    random.Random(SEMILLA).shuffle(indices)
    corte = int(len(indices) * PORCENTAJE_ENTRENAMIENTO)
    entrenamiento = [oraciones_corpus[i] for i in indices[:corte]]
    validacion = [oraciones_corpus[i] for i in indices[corte:]]

    etiqueta_base = DefaultTagger("UNK")
    unigramas = UnigramTagger(entrenamiento, backoff=etiqueta_base)
    bigramas = BigramTagger(entrenamiento, backoff=unigramas)

    info = {
        "corpus_entrenamiento": "CESS-ESP (NLTK)",
        "sha256_corpus_cess_esp": digest.hexdigest(),
        "semilla": SEMILLA,
        "total_oraciones_cess": len(oraciones_corpus),
        "entrenamiento_oraciones": len(entrenamiento),
        "validacion_oraciones": len(validacion),
        "exactitud_pos_validacion_cess": bigramas.accuracy(validacion) if validacion else None,
        "tagger": "BigramTagger -> UnigramTagger -> DefaultTagger(UNK)",
        "normalizacion": "casefold de las palabras (no de las etiquetas)",
    }
    return bigramas, info


def extraer_sintagmas(arbol, nltk):
    """Extrae los nodos SN y sus posiciones sin reanalizar la oracion."""
    sintagmas = []
    indice = 0
    for nodo in arbol:
        if isinstance(nodo, nltk.Tree):
            hojas = nodo.leaves()
            if nodo.label() == "SN":
                sintagmas.append({
                    "inicio": indice,
                    "fin_exclusivo": indice + len(hojas),
                    "texto": " ".join(palabra for palabra, _ in hojas),
                })
            indice += len(hojas)
        else:
            indice += 1
    return sintagmas


def criterio_nltk(texto, nltk, etiquetador, chunker):
    """Regla externa independiente de etiquetas esperadas y CFG propia."""
    from nltk.tokenize import sent_tokenize, wordpunct_tokenize

    fragmentos = sent_tokenize(texto, language="spanish")
    tokens = wordpunct_tokenize(texto)
    etiquetas = etiquetador.tag([t.casefold() for t in tokens])
    datos_tokens = [
        {
            "indice": i,
            "texto": token,
            "tag_cess_eagles": tag,
            "pos_general": categoria_simple(tag),
            "verbo_finito": es_verbo_finito(tag),
        }
        for i, (token, (_, tag)) in enumerate(zip(tokens, etiquetas))
    ]
    pares_chunk = [(d["texto"], d["pos_general"]) for d in datos_tokens]
    arbol = chunker.parse(pares_chunk)
    sintagmas = extraer_sintagmas(arbol, nltk)
    verbos = [d for d in datos_tokens if d["verbo_finito"]]
    primero = verbos[0]["indice"] if verbos else None
    sujetos_candidatos = [
        sn for sn in sintagmas
        if primero is not None and sn["fin_exclusivo"] <= primero
    ]

    indicadores = {
        "termina_en_punto": texto.rstrip().endswith("."),
        "una_sola_oracion": len(fragmentos) == 1,
        "numero_oraciones_nltk": len(fragmentos),
        "verbo_finito": len(verbos) > 0,
        "verbos_finitos": [{"texto": v["texto"], "indice": v["indice"], "tag": v["tag_cess_eagles"]} for v in verbos],
        "sintagma_nominal_antes_verbo": len(sujetos_candidatos) > 0,
        "sintagmas_nominales": sintagmas,
        "sujetos_candidatos": sujetos_candidatos,
    }

    if not indicadores["termina_en_punto"]:
        motivo = "No termina en punto."
    elif not indicadores["una_sola_oracion"]:
        motivo = "NLTK no detecto exactamente una oracion."
    elif not indicadores["verbo_finito"]:
        motivo = "El etiquetador NLTK no identifico verbo finito."
    elif not indicadores["sintagma_nominal_antes_verbo"]:
        motivo = "No se detecto sintagma nominal candidato a sujeto antes del verbo."
    else:
        motivo = "Cumple las cuatro condiciones del criterio NLTK."

    aceptada = motivo.startswith("Cumple")
    return aceptada, indicadores, motivo, datos_tokens, arbol.pformat(margin=150)


def dividir(a, b):
    return a / b if b else None


def calcular_metricas(registros):
    vp = sum(r["esperado"] == "aceptada" and r["obtenido"] == "aceptada" for r in registros)
    fp = sum(r["esperado"] == "rechazada" and r["obtenido"] == "aceptada" for r in registros)
    fn = sum(r["esperado"] == "aceptada" and r["obtenido"] == "rechazada" for r in registros)
    vn = sum(r["esperado"] == "rechazada" and r["obtenido"] == "rechazada" for r in registros)
    return {
        "total": len(registros), "VP": vp, "FP": fp, "FN": fn, "VN": vn,
        "precision": dividir(vp, vp + fp),
        "recall": dividir(vp, vp + fn),
        "tasa_rechazo_correcto": dividir(vn, vn + fp),
        "exactitud": dividir(vp + vn, len(registros)),
    }


def ejecutar():
    try:
        import nltk
        from nltk.corpus import cess_esp
        from nltk.tokenize import sent_tokenize
        # Comprobacion temprana: si faltan los recursos, ofrecer comandos.
        cess_esp.tagged_sents()[0]
        sent_tokenize("La nina corre.", language="spanish")
    except ImportError as e:
        raise SystemExit("Falta NLTK. Ejecuta: python -m pip install nltk") from e
    except LookupError as e:
        raise SystemExit(
            "Falta un recurso de NLTK. Ejecuta: "
            "python -m nltk.downloader cess_esp punkt_tab\n"
            "Detalle del recurso: " + str(e)
        ) from e

    filas = leer_corpus()
    etiquetador, info_entrenamiento = construir_etiquetador(nltk, cess_esp)
    chunker = nltk.RegexpParser(GRAMATICA_CHUNKS)

    inicio = hora_local()
    id_corrida = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    salida = CARPETA_RESULTADOS / id_corrida
    salida.mkdir(parents=True, exist_ok=False)

    registros = []
    with (salida / "logs_nltk.jsonl").open("w", encoding="utf-8") as archivo:
        for fila in filas:
            aceptada, indicadores, motivo, tags, chunks = criterio_nltk(
                fila["oracion"], nltk, etiquetador, chunker
            )
            obtenido = "aceptada" if aceptada else "rechazada"
            registro = {
                "id": fila["id"],
                "nivel": int(fila["nivel"]),
                "oracion": fila["oracion"],
                "esperado": fila["etiqueta_esperada"],
                "obtenido": obtenido,
                "coincide": obtenido == fila["etiqueta_esperada"],
                "criterio_id": CRITERIO_ID,
                "indicadores": indicadores,
                "motivo": motivo,
                "tokens_y_etiquetas_nltk": tags,
                "arbol_chunks_nltk": chunks,
                "timestamp_local": hora_local(),
            }
            registros.append(registro)
            archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            marca = "OK" if registro["coincide"] else "DIFERENCIA"
            print(f"[{marca}] {registro['id']} nivel {registro['nivel']}: {obtenido.upper()} - {registro['oracion']}")

    columnas = [
        "id", "nivel", "oracion", "esperado", "obtenido",
        "coincide", "motivo", "criterio_id", "timestamp_local",
    ]
    with (salida / "resultados_nltk.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=columnas)
        writer.writeheader()
        for r in registros:
            writer.writerow({k: r[k] for k in columnas})

    metricas = {
        "total": calcular_metricas(registros),
        "por_nivel": {
            str(n): calcular_metricas([r for r in registros if r["nivel"] == n])
            for n in (1, 2, 3)
        },
        "criterio_id": CRITERIO_ID,
        "criterio_texto": DESCRIPCION_CRITERIO,
        "etiquetas_referencia": "aceptacion/rechazo segun la CFG y el corpus etiquetado",
        "advertencia": (
            "El veredicto no es nativo de NLTK: lo emite el criterio externo. "
            "El tagger se entrena con CESS-ESP, no con las etiquetas del corpus evaluado. "
            "Un error relativo a la CFG no implica necesariamente un error linguistico."
        ),
    }
    (salida / "metricas_nltk.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    metadatos = {
        "inicio_local": inicio,
        "final_local": hora_local(),
        "configuracion_horaria": "dispositivo",
        "python": platform.python_version(),
        "nltk": nltk.__version__,
        "metodo": "Etiquetador POS NLTK entrenado con CESS-ESP + RegexpParser de chunks SN",
        "recursos_nltk": ["cess_esp", "punkt_tab"],
        "criterio_id": CRITERIO_ID,
        "criterio_texto": DESCRIPCION_CRITERIO,
        "gramatica_chunks": GRAMATICA_CHUNKS,
        "entrenamiento": info_entrenamiento,
        "numero_oraciones": len(registros),
        "corpus_sha256": sha256(CORPUS),
        "script_sha256": sha256(Path(__file__).resolve()),
    }
    (salida / "metadatos_nltk.json").write_text(
        json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nRESULTADOS NLTK (referencia: CFG)")
    print(json.dumps(metricas["total"], indent=2, ensure_ascii=False))
    print("Carpeta de evidencias:", salida)
    print("No se modificaron el corpus ni los componentes del parser propio.")


if __name__ == "__main__":
    ejecutar()
