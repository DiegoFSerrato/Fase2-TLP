# ------------------------------------------------------------
# FASE 2 - EVALUACION DE CFG EN ESPANOL CON UN LLM VIA API
# ZERO-SHOT Y FEW-SHOT (MISMO CORPUS Y MISMA GRAMATICA)
# ------------------------------------------------------------
# Por seguridad, sin --ejecutar SOLO previsualiza los prompts.
# Requiere OPENAI_API_KEY y la biblioteca openai para ejecutarse.
# Las llamadas via API pueden generar cargos.
# No cambia la CFG, el lexer, el parser ni el corpus.
# ------------------------------------------------------------
import argparse
import ast
import csv
import hashlib
import json
import os
import platform
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUTA_CORPUS = BASE / "corpus_es_fase2.csv"
RUTA_GRAMATICA = BASE / "gramatica_es_ll1.py"
RUTA_LEXER = BASE / "lexer_es.py"
CARPETA_RESULTADOS = BASE / "resultados_llm"
MODELO_DEFECTO = "gpt-6-luna"
ESFUERZO_DEFECTO = "none"  # GPT-6 Luna admite none
MAX_SALIDA_DEFECTO = 200
CRITERIO_ID = "llm_cfg_es_v1"

# Los ejemplos few-shot fueron creados APARTE del corpus de 45 oraciones.
# No se modificaran despues de observar los resultados.
EJEMPLOS_FEWSHOT = [
    {"oracion": "El gato corre.", "veredicto": "aceptada",
     "justificacion": "DET_MS N_MS VERBO_S PUNTO: sujeto y verbo singulares."},
    {"oracion": "Unas profesoras leen unos libros.", "veredicto": "aceptada",
     "justificacion": "Sujeto plural y verbo plural; objeto con determinante y sustantivo concordantes."},
    {"oracion": "Ella compra una manzana en la casa.", "veredicto": "aceptada",
     "justificacion": "Pronombre singular, verbo singular, objeto y un circunstancial PREP + SN."},
    {"oracion": "La gato corre.", "veredicto": "rechazada",
     "justificacion": "DET_FS no puede iniciar un sintagma masculino singular N_MS."},
    {"oracion": "Los gatos corre.", "veredicto": "rechazada",
     "justificacion": "Sujeto plural con VERBO_S: no hay produccion compatible."},
    {"oracion": "El gato corre rapidamente en la casa.", "veredicto": "rechazada",
     "justificacion": "Dos complementos circunstanciales consecutivos exceden CIRC_OPT."},
]

# Acento correcto en la palabra 'rápidamente' (ejemplo fuera del corpus).
EJEMPLOS_FEWSHOT[-1]["oracion"] = "El gato corre rápidamente en la casa."

ESQUEMA_SALIDA = {
    "type": "object",
    "properties": {
        "veredicto": {"type": "string", "enum": ["aceptada", "rechazada"]},
        "justificacion": {"type": "string"},
    },
    "required": ["veredicto", "justificacion"],
    "additionalProperties": False,
}


def hora_local():
    """Conserva el desfase horario del dispositivo (por ejemplo -06:00)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def cargar_constante_python(ruta, nombre):
    """Lee solo los literales originales del archivo: no ejecuta ni altera la CFG."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"), filename=str(ruta))
    for instruccion in arbol.body:
        if isinstance(instruccion, ast.Assign):
            for target in instruccion.targets:
                if isinstance(target, ast.Name) and target.id == nombre:
                    return ast.literal_eval(instruccion.value)
    raise ValueError(f"No se encontro la constante {nombre} en {ruta.name}")


def leer_configuracion_gramatica():
    gramatica = cargar_constante_python(RUTA_GRAMATICA, "GRAMATICA")
    vocab = cargar_constante_python(RUTA_LEXER, "VOCABULARIO_POR_TOKEN")
    terminales = set()
    no_terminales = set(gramatica)
    for producciones in gramatica.values():
        for p in producciones:
            terminales.update(s for s in p if s not in no_terminales)
    categorias = set(vocab) | {"PUNTO"}
    if terminales != categorias:
        raise ValueError(
            "Las categorias del lexer y los terminales de la CFG difieren. "
            f"Solo_CFG={sorted(terminales-categorias)}, "
            f"Solo_lexer={sorted(categorias-terminales)}"
        )
    return gramatica, vocab


def leer_corpus():
    with RUTA_CORPUS.open(encoding="utf-8-sig", newline="") as h:
        lector = csv.DictReader(h)
        requeridas = {"id", "nivel", "oracion", "etiqueta_esperada"}
        if not requeridas.issubset(lector.fieldnames or []):
            raise ValueError("Faltan columnas requeridas del corpus.")
        filas = list(lector)
    if len(filas) < 40 or len({r["id"] for r in filas}) != len(filas):
        raise ValueError("Corpus invalido: menos de 40 oraciones o IDs duplicados.")
    if any(r["nivel"] not in {"1", "2", "3"} for r in filas):
        raise ValueError("Hay niveles fuera de 1, 2 o 3.")
    if any(r["etiqueta_esperada"] not in {"aceptada", "rechazada"} for r in filas):
        raise ValueError("Hay etiquetas de referencia desconocidas.")
    return filas


def instrucciones_llm(gramatica, vocabulario, modo):
    partes = [
        "Eres un evaluador de una GRAMATICA FORMAL para un subconjunto controlado del espanol.",
        "Tu tarea NO es juzgar si una oracion suena natural o es gramatical en espanol general.",
        "Decide SOLO si la oracion puede derivarse desde ORACION usando EXACTAMENTE las producciones y el vocabulario siguientes.",
        "Cada palabra reconocida corresponde a una sola categoria de su lista; no inventes categorias.",
        "Las palabras se comparan sin distinguir mayusculas/minusculas; conserva las tildes.",
        "El unico signo de puntuacion permitido es el punto final PUNTO.",
        "Una palabra fuera del vocabulario implica 'rechazada'.",
        "Si no existe una derivacion completa para todos los tokens, responde 'rechazada'.",
        "No agregues reglas; no aceptes por intuicion linguistica.",
        "Responde UNICAMENTE con JSON: {\"veredicto\":\"aceptada|rechazada\",\"justificacion\":\"explicacion breve\"}.",
        "La justificacion debe tener maximo 12 palabras, sin repetir reglas ni la oracion.",
        "\nPRODUCCIONES EXACTAS DE LA CFG (ε indica produccion vacia):",
    ]
    for simbolo, producciones in gramatica.items():
        opciones = [" ".join(p) if p else "ε" for p in producciones]
        partes.append(f"{simbolo} -> " + " | ".join(opciones))
    partes.append("\nVOCABULARIO EXACTO DEL LEXER (categoria: palabras permitidas):")
    for categoria, palabras in vocabulario.items():
        partes.append(categoria + ": " + ", ".join(palabras))
    partes.append("PUNTO: .")
    if modo == "few-shot":
        partes.append("\nEJEMPLOS RESUELTOS, INDEPENDIENTES DEL CORPUS DE EVALUACION:")
        for i, ex in enumerate(EJEMPLOS_FEWSHOT, 1):
            partes.append(
                f"Ejemplo {i}: {ex['oracion']}\n"
                + json.dumps({"veredicto": ex["veredicto"], "justificacion": ex["justificacion"]}, ensure_ascii=False)
            )
    return "\n".join(partes)


def prompt_usuario(oracion):
    return "Clasifica exclusivamente con la CFG y vocabulario proporcionados.\nORACION A ANALIZAR: " + oracion


def metricas(filas):
    vp = sum(r["esperado"] == "aceptada" and r["obtenido"] == "aceptada" for r in filas)
    fp = sum(r["esperado"] == "rechazada" and r["obtenido"] == "aceptada" for r in filas)
    fn = sum(r["esperado"] == "aceptada" and r["obtenido"] == "rechazada" for r in filas)
    vn = sum(r["esperado"] == "rechazada" and r["obtenido"] == "rechazada" for r in filas)
    dividir = lambda a, b: a / b if b else None
    return {
        "total_evaluado": len(filas), "VP": vp, "FP": fp, "FN": fn, "VN": vn,
        "precision": dividir(vp, vp + fp),
        "recall": dividir(vp, vp + fn),
        "tasa_rechazo_correcto": dividir(vn, vn + fp),
        "exactitud": dividir(vp + vn, len(filas)),
    }


def escribir_json(ruta, obj):
    ruta.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Evaluacion LLM zero-shot / few-shot de la CFG espanola.")
    ap.add_argument("--ejecutar", action="store_true", help="Realiza llamadas de pago a la API. Sin esto: vista previa sin cargos.")
    ap.add_argument("--modo", choices=["zero-shot", "few-shot", "ambos"], default="ambos")
    ap.add_argument("--limite", type=int, default=None, help="Solo las primeras N oraciones, para una prueba piloto.")
    ap.add_argument("--modelo", default=os.environ.get("OPENAI_MODEL", MODELO_DEFECTO))
    ap.add_argument("--esfuerzo", choices=["none", "low", "medium"], default=ESFUERZO_DEFECTO,
                    help="Esfuerzo del modelo. Para gpt-6-luna, none reduce tokens de razonamiento.")
    ap.add_argument("--max-salida-tokens", type=int, default=MAX_SALIDA_DEFECTO,
                    help="Limite maximo de tokens de salida por respuesta (por defecto: 200).")
    args = ap.parse_args()
    if args.limite is not None and args.limite < 1:
        raise SystemExit("--limite debe ser un entero positivo.")
    if not 60 <= args.max_salida_tokens <= 800:
        raise SystemExit("--max-salida-tokens debe estar entre 60 y 800.")

    corpus = leer_corpus()
    grammar, vocab = leer_configuracion_gramatica()
    usadas = corpus[:args.limite] if args.limite else corpus
    textos_corpus = {r["oracion"].casefold() for r in corpus}
    repetidos = [ex["oracion"] for ex in EJEMPLOS_FEWSHOT if ex["oracion"].casefold() in textos_corpus]
    if repetidos:
        raise SystemExit("Fuga de datos: ejemplos few-shot incluidos en corpus: " + ", ".join(repetidos))

    modos = ["zero-shot", "few-shot"] if args.modo == "ambos" else [args.modo]
    instrucciones = {modo: instrucciones_llm(grammar, vocab, modo) for modo in modos}

    if not args.ejecutar:
        print("VISTA PREVIA SIN LLAMADAS A API")
        print("Modelo configurado:", args.modelo)
        print("Esfuerzo de razonamiento:", args.esfuerzo)
        print("Limite de tokens de salida:", args.max_salida_tokens)
        print("Oraciones seleccionadas:", len(usadas), "/", len(corpus))
        print("Modos:", ", ".join(modos))
        print("Llamadas estimadas si se ejecuta:", len(usadas) * len(modos))
        print("La vista previa no utiliza API key ni genera cargos.")
        for modo in modos:
            print("\n--- INSTRUCCIONES", modo, "---\n")
            print(instrucciones[modo])
            print("\n--- EJEMPLO PROMPT USUARIO ---\n", prompt_usuario(usadas[0]["oracion"]))
        return

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Falta OPENAI_API_KEY en las variables de entorno. No compartas la clave ni la guardes en Git.")
    try:
        from openai import OpenAI
        import openai
    except ImportError as exc:
        raise SystemExit("Instala el SDK: python -m pip install -U openai") from exc

    # No utilizamos resultados anteriores ni datos de referencia en prompts.
    client = OpenAI(max_retries=0, timeout=60.0)  # sin reintentos automaticos
    nombre = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    destino = CARPETA_RESULTADOS / nombre
    destino.mkdir(parents=True, exist_ok=False)
    completo = len(usadas) == len(corpus)
    inicio = hora_local()

    config = {
        "inicio_local": inicio,
        "modelo_solicitado": args.modelo,
        "proveedor": "OpenAI",
        "endpoint": "Responses API",
        "sdk_openai": getattr(openai, "__version__", "desconocida"),
        "python": platform.python_version(),
        "modos": modos,
        "estudio_completo": completo,
        "oraciones_corpus": len(corpus),
        "oraciones_seleccionadas": len(usadas),
        "llamadas_planificadas": len(usadas)*len(modos),
        "criterio_id": CRITERIO_ID,
        "nota_metodologica": "La referencia es aceptacion por la CFG, NO correccion general del espanol.",
        "corpus_sha256": sha256(RUTA_CORPUS),
        "gramatica_sha256": sha256(RUTA_GRAMATICA),
        "lexer_sha256": sha256(RUTA_LEXER),
        "script_sha256": sha256(Path(__file__).resolve()),
        "ejemplos_fewshot": EJEMPLOS_FEWSHOT,
        "parametros_api": {
            "reasoning_effort": args.esfuerzo,
            "max_output_tokens": args.max_salida_tokens,
            "store": False,
            "prompt_cache_options": {"mode": "implicit"},
            "max_retries": 0,
            "schema": ESQUEMA_SALIDA,
        },
    }
    escribir_json(destino/"prompts_plantilla.json", {
        "criterio_id": CRITERIO_ID, "modelo_solicitado": args.modelo,
        "instrucciones_por_modo": instrucciones,
        "esquema_salida": ESQUEMA_SALIDA,
        "ejemplos_fewshot": EJEMPLOS_FEWSHOT,
    })
    registros = []
    print("CARPETA DE RESULTADOS:", destino)

    with (destino/"prompts_exactos.jsonl").open("w", encoding="utf-8") as p_file, \
         (destino/"logs_llm.jsonl").open("w", encoding="utf-8") as l_file:
        for modo in modos:
            for fila in usadas:
                inicio_llamada = hora_local()
                mensaje_usuario = prompt_usuario(fila["oracion"])
                solicitud = {
                    "id":fila["id"], "modo":modo, "timestamp_local":inicio_llamada,
                    "instrucciones":instrucciones[modo], "mensaje_usuario":mensaje_usuario,
                    "modelo":args.modelo,
                    "reasoning_effort": args.esfuerzo,
                    "max_output_tokens": args.max_salida_tokens,
                    "prompt_cache_options": {"mode": "implicit"},
                    "text_format":{"type":"json_schema","name":"veredicto_cfg_es","schema":ESQUEMA_SALIDA,"strict":True},
                }
                p_file.write(json.dumps(solicitud,ensure_ascii=False)+"\n");p_file.flush()
                base = {
                    "id": fila["id"], "nivel": int(fila["nivel"]),
                    "oracion":fila["oracion"], "esperado":fila["etiqueta_esperada"],
                    "modo":modo, "criterio_id":CRITERIO_ID, "timestamp_inicio_local":inicio_llamada,
                }
                response = None
                texto = ""
                try:
                    response = client.responses.create(
                        model=args.modelo,
                        instructions=instrucciones[modo],
                        input=mensaje_usuario,
                        text={"format":{"type":"json_schema", "name":"veredicto_cfg_es", "schema":ESQUEMA_SALIDA, "strict":True}},
                        reasoning={"effort": args.esfuerzo},
                        max_output_tokens=args.max_salida_tokens,
                        prompt_cache_options={"mode": "implicit"},
                        store=False,
                    )
                    respuesta_completa = response.model_dump(mode="json")
                    if getattr(response, "status", None) == "incomplete":
                        raise ValueError(
                            "Respuesta incompleta por limite de tokens; "
                            "consulta response.incomplete_details y sube --max-salida-tokens."
                        )
                    texto = response.output_text or ""
                    respuesta = json.loads(texto)
                    veredicto = respuesta.get("veredicto")
                    if veredicto not in {"aceptada", "rechazada"}:
                        raise ValueError("La respuesta no contiene un veredicto permitido.")
                    registro = {
                        **base,
                        "estado":"ok", "obtenido":veredicto,
                        "coincide":veredicto==fila["etiqueta_esperada"],
                        "justificacion":respuesta.get("justificacion", ""),
                        "respuesta_texto_original":texto,
                        "respuesta_api_completa":respuesta_completa,
                        "uso_tokens_api":response.usage.model_dump(mode="json") if response.usage else None,
                        "modelo_respondio":getattr(response, "model", None),
                        "response_id":getattr(response, "id", None),
                        "timestamp_final_local":hora_local(),
                    }
                except Exception as exc:
                    # Un error de API/formato no equivale a 'rechazada'.
                    registro = {
                        **base,
                        "estado":"error", "obtenido":None,
                        "coincide":None, "justificacion":None,
                        "error_tipo":type(exc).__name__, "error_detalle":str(exc),
                        "respuesta_texto_original":texto,
                        "respuesta_api_completa":response.model_dump(mode="json") if response is not None else None,
                        "uso_tokens_api":response.usage.model_dump(mode="json") if response is not None and response.usage else None,
                        "response_id":getattr(response, "id", None) if response is not None else None,
                        "timestamp_final_local":hora_local(),
                    }
                l_file.write(json.dumps(registro,ensure_ascii=False,default=str)+"\n");l_file.flush()
                registros.append(registro)
                marca = "OK" if registro["estado"]=="ok" and registro["coincide"] else "DIFERENCIA" if registro["estado"]=="ok" else "ERROR"
                print(f"[{marca}] {modo} {fila['id']}: {registro['obtenido'] or registro.get('error_tipo')}")

    campos = ["id","nivel","oracion","modo","esperado","obtenido","coincide","estado", "justificacion", "modelo_respondio", "response_id", "timestamp_inicio_local","timestamp_final_local"]
    with (destino/"resultados_llm.csv").open("w",encoding="utf-8-sig",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=campos);writer.writeheader()
        for r in registros:writer.writerow({k:r.get(k) for k in campos})

    resumen = {"criterio_id":CRITERIO_ID, "estudio_completo":completo,
               "aviso":"PILOTO: no usar estas metricas como resultado final" if not completo else "Resultados del corpus completo; revisar errores de API si existen.",
               "por_modo":{}}
    for modo in modos:
        grupo=[r for r in registros if r['modo']==modo]
        validos=[r for r in grupo if r['estado']=='ok']
        info={"total_planificado":len(grupo),"respuestas_validas":len(validos),"errores_api_o_formato":len(grupo)-len(validos),"total":metricas(validos),
             "por_nivel":{str(n):metricas([r for r in validos if r['nivel']==n]) for n in (1,2,3)}}
        if len(validos)!=len(grupo):info["advertencia"]="Metricas calculadas solo con respuestas validas: no son comparables directamente si hay faltantes."
        resumen['por_modo'][modo]=info
    # Registrar los tokens que informo la API, incluidas lecturas de cache y razonamiento.
    usos = [r.get("uso_tokens_api") for r in registros if r.get("uso_tokens_api")]
    resumen_uso = {
        "solicitudes_con_uso": len(usos),
        "input_tokens": sum(u.get("input_tokens", 0) or 0 for u in usos),
        "output_tokens": sum(u.get("output_tokens", 0) or 0 for u in usos),
        "total_tokens": sum(u.get("total_tokens", 0) or 0 for u in usos),
        "cached_input_tokens": sum(
            (u.get("input_tokens_details") or {}).get("cached_tokens", 0) or 0
            for u in usos
        ),
        "cache_write_tokens": sum(
            (u.get("input_tokens_details") or {}).get("cache_write_tokens", 0) or 0
            for u in usos
        ),
        "reasoning_tokens": sum(
            (u.get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0
            for u in usos
        ),
    }
    resumen["uso_tokens_api"] = resumen_uso
    escribir_json(destino/"metricas_llm.json",resumen)
    config["uso_tokens_api"] = resumen_uso
    print("\nUSO DE TOKENS INFORMADO POR LA API:")
    print(json.dumps(resumen_uso,ensure_ascii=False,indent=2))
    config["final_local"]=hora_local()
    config["llamadas_registradas"]=len(registros)
    config["errores_api_o_formato"]=sum(r["estado"]!="ok" for r in registros)
    config["carpeta_salida"]=str(destino)
    escribir_json(destino/"metadatos_llm.json",config)
    print("\nREGISTROS:",len(registros))
    print("Completos para informe:",completo and config["errores_api_o_formato"]==0)
    print("Evidencias guardadas en:",destino)


if __name__ == "__main__":
    main()
