# ------------------------------------------------------------
# Gramatica LL(1) para un subconjunto controlado del espanol.
# Fase 2 - Analisis sintactico de oraciones en espanol.
# ------------------------------------------------------------


SIMBOLO_INICIAL = "ORACION"
FIN_ENTRADA = "$"

# Los simbolos de las claves son no terminales.
# Los simbolos no incluidos como claves son terminales (tokens).
# () representa epsilon: la cadena vacia.
GRAMATICA = {
    # 1. Una oracion tiene sujeto, predicado y punto final.
    #    Separar el singular del plural permite controlar
    #    concordancia de numero entre sujeto y verbo.
    "ORACION": [
        ("SUJETO_S", "PRED_S", "PUNTO"),
        ("SUJETO_P", "PRED_P", "PUNTO"),
    ],

    # 2. Sujetos en singular y plural.
    "SUJETO_S": [
        ("PRON_S",),
        ("SN_S",),
    ],
    "SUJETO_P": [
        ("PRON_P",),
        ("SN_P",),
    ],

    # 3. Predicados: verbo, objeto opcional y circunstancial opcional.
    "PRED_S": [
        ("VERBO_S", "OBJETO_OPT", "CIRC_OPT"),
    ],
    "PRED_P": [
        ("VERBO_P", "OBJETO_OPT", "CIRC_OPT"),
    ],

    "OBJETO_OPT": [
        ("SN",),
        (),
    ],
    "CIRC_OPT": [
        ("PREP", "SN"),
        ("ADV",),
        (),
    ],

    # 4. Sintagma nominal de cualquier genero y numero,
    #    utilizado como objeto o dentro de un circunstancial.
    "SN": [
        ("SN_S",),
        ("SN_P",),
    ],
    "SN_S": [
        ("NOM_MS",),
        ("NOM_FS",),
    ],
    "SN_P": [
        ("NOM_MP",),
        ("NOM_FP",),
    ],

    # 5. Concordancia entre determinante, sustantivo y adjetivo:
    #    M/F = masculino/femenino; S/P = singular/plural.
    "NOM_MS": [
        ("DET_MS", "N_MS", "ADJ_MS_OPT"),
    ],
    "NOM_FS": [
        ("DET_FS", "N_FS", "ADJ_FS_OPT"),
    ],
    "NOM_MP": [
        ("DET_MP", "N_MP", "ADJ_MP_OPT"),
    ],
    "NOM_FP": [
        ("DET_FP", "N_FP", "ADJ_FP_OPT"),
    ],

    # 6. Adjetivos opcionales, concordantes con el sustantivo.
    "ADJ_MS_OPT": [
        ("ADJ_MS",),
        (),
    ],
    "ADJ_FS_OPT": [
        ("ADJ_FS",),
        (),
    ],
    "ADJ_MP_OPT": [
        ("ADJ_MP",),
        (),
    ],
    "ADJ_FP_OPT": [
        ("ADJ_FP",),
        (),
    ],
}


def mostrar_gramatica():
    """Imprime las reglas de la CFG con notacion legible."""
    print("Gramatica LL(1) - Subconjunto del espanol\n")
    for no_terminal, alternativas in GRAMATICA.items():
        producciones = [" ".join(p) if p else "ε" for p in alternativas]
        print(f"{no_terminal} -> " + " | ".join(producciones))


if __name__ == "__main__":
    mostrar_gramatica()
