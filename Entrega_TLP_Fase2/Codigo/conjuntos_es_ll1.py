# ------------------------------------------------------------
# Conjuntos FIRST y FOLLOW para la CFG del espanol.
# ------------------------------------------------------------

SIMBOLO_INICIAL = "ORACION"

# epsilon: produccion vacia (no consume ningun token).
EPSILON = "ε"

FIRST = {
    "ORACION": {"DET_FP", "DET_FS", "DET_MP", "DET_MS", "PRON_P", "PRON_S"},
    "SUJETO_S": {"DET_FS", "DET_MS", "PRON_S"},
    "SUJETO_P": {"DET_FP", "DET_MP", "PRON_P"},
    "PRED_S": {"VERBO_S"},
    "PRED_P": {"VERBO_P"},
    "OBJETO_OPT": {"DET_FP", "DET_FS", "DET_MP", "DET_MS", "ε"},
    "CIRC_OPT": {"ADV", "PREP", "ε"},
    "SN": {"DET_FP", "DET_FS", "DET_MP", "DET_MS"},
    "SN_S": {"DET_FS", "DET_MS"},
    "SN_P": {"DET_FP", "DET_MP"},
    "NOM_MS": {"DET_MS"},
    "NOM_FS": {"DET_FS"},
    "NOM_MP": {"DET_MP"},
    "NOM_FP": {"DET_FP"},
    "ADJ_MS_OPT": {"ADJ_MS", "ε"},
    "ADJ_FS_OPT": {"ADJ_FS", "ε"},
    "ADJ_MP_OPT": {"ADJ_MP", "ε"},
    "ADJ_FP_OPT": {"ADJ_FP", "ε"},
}

FOLLOW = {
    "ORACION": {"$"},
    "SUJETO_S": {"VERBO_S"},
    "SUJETO_P": {"VERBO_P"},
    "PRED_S": {"PUNTO"},
    "PRED_P": {"PUNTO"},
    "OBJETO_OPT": {"ADV", "PREP", "PUNTO"},
    "CIRC_OPT": {"PUNTO"},
    "SN": {"ADV", "PREP", "PUNTO"},
    "SN_S": {"ADV", "PREP", "PUNTO", "VERBO_S"},
    "SN_P": {"ADV", "PREP", "PUNTO", "VERBO_P"},
    "NOM_MS": {"ADV", "PREP", "PUNTO", "VERBO_S"},
    "NOM_FS": {"ADV", "PREP", "PUNTO", "VERBO_S"},
    "NOM_MP": {"ADV", "PREP", "PUNTO", "VERBO_P"},
    "NOM_FP": {"ADV", "PREP", "PUNTO", "VERBO_P"},
    "ADJ_MS_OPT": {"ADV", "PREP", "PUNTO", "VERBO_S"},
    "ADJ_FS_OPT": {"ADV", "PREP", "PUNTO", "VERBO_S"},
    "ADJ_MP_OPT": {"ADV", "PREP", "PUNTO", "VERBO_P"},
    "ADJ_FP_OPT": {"ADV", "PREP", "PUNTO", "VERBO_P"},
}

def mostrar_conjuntos():
    """Muestra los conjuntos ya calculados, sin reconstruirlos."""
    print("FIRST Y FOLLOW - CFG DEL ESPANOL\n")
    for no_terminal in FIRST:
        primeros = ", ".join(sorted(FIRST[no_terminal]))
        siguientes = ", ".join(sorted(FOLLOW[no_terminal]))
        print(f"{no_terminal}")
        print(f"  FIRST  = {{{primeros}}}")
        print(f"  FOLLOW = {{{siguientes}}}\n")

if __name__ == "__main__":
    mostrar_conjuntos()
