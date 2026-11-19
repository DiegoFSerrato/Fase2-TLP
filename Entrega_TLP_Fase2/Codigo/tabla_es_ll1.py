# ------------------------------------------------------------
# TABLA LL(1) COMPACTA - SUBCONJUNTO DEL ESPANOL
# Fase 2 - Analisis sintactico de oraciones.
# ------------------------------------------------------------
# La tabla se construyo a partir de gramatica_es_ll1.py y de
# los conjuntos FIRST y FOLLOW de conjuntos_es_ll1.py.
#
# IMPORTANTE:
# - Esta tabla es FIJA: NO se reconstruye durante el analisis.
# - La clave externa es el NO TERMINAL.
# - La clave interna es el TOKEN ACTUAL (lookahead).
# - Una tupla representa los simbolos de la produccion.
# - () representa una produccion epsilon (valida).
# - Una celda no definida devuelve None (error sintactico).
# ------------------------------------------------------------


# 19 terminales del lenguaje y el marcador de fin de entrada.
TERMINALES = (
    'DET_MS',
    'DET_FS',
    'DET_MP',
    'DET_FP',
    'N_MS',
    'N_FS',
    'N_MP',
    'N_FP',
    'ADJ_MS',
    'ADJ_FS',
    'ADJ_MP',
    'ADJ_FP',
    'PRON_S',
    'PRON_P',
    'VERBO_S',
    'VERBO_P',
    'PREP',
    'ADV',
    'PUNTO',
    '$',
)


TABLA_LL1 = {

    # ========================================================
    # 1. ESTRUCTURA GENERAL DE LA ORACION
    # ========================================================

    # ORACION -> SUJETO_S PRED_S PUNTO
    #          | SUJETO_P PRED_P PUNTO
    'ORACION': {
        'PRON_S': ('SUJETO_S', 'PRED_S', 'PUNTO'),
        'DET_MS': ('SUJETO_S', 'PRED_S', 'PUNTO'),
        'DET_FS': ('SUJETO_S', 'PRED_S', 'PUNTO'),

        'PRON_P': ('SUJETO_P', 'PRED_P', 'PUNTO'),
        'DET_MP': ('SUJETO_P', 'PRED_P', 'PUNTO'),
        'DET_FP': ('SUJETO_P', 'PRED_P', 'PUNTO'),
    },

    # ========================================================
    # 2. SUJETOS EN SINGULAR Y PLURAL
    # ========================================================

    # SUJETO_S -> PRON_S | SN_S
    'SUJETO_S': {
        'PRON_S': ('PRON_S',),
        'DET_MS': ('SN_S',),
        'DET_FS': ('SN_S',),
    },

    # SUJETO_P -> PRON_P | SN_P
    'SUJETO_P': {
        'PRON_P': ('PRON_P',),
        'DET_MP': ('SN_P',),
        'DET_FP': ('SN_P',),
    },

    # ========================================================
    # 3. PREDICADOS Y COMPLEMENTOS OPCIONALES
    # ========================================================

    # PRED_S -> VERBO_S OBJETO_OPT CIRC_OPT
    'PRED_S': {
        'VERBO_S': ('VERBO_S', 'OBJETO_OPT', 'CIRC_OPT'),
    },

    # PRED_P -> VERBO_P OBJETO_OPT CIRC_OPT
    'PRED_P': {
        'VERBO_P': ('VERBO_P', 'OBJETO_OPT', 'CIRC_OPT'),
    },

    # OBJETO_OPT -> SN | epsilon
    'OBJETO_OPT': {
        'DET_MS': ('SN',),
        'DET_FS': ('SN',),
        'DET_MP': ('SN',),
        'DET_FP': ('SN',),

        'PREP': (),
        'ADV': (),
        'PUNTO': (),
    },

    # CIRC_OPT -> PREP SN | ADV | epsilon
    'CIRC_OPT': {
        'PREP': ('PREP', 'SN'),
        'ADV': ('ADV',),
        'PUNTO': (),
    },

    # ========================================================
    # 4. SINTAGMAS NOMINALES
    # ========================================================

    # SN -> SN_S | SN_P
    'SN': {
        'DET_MS': ('SN_S',),
        'DET_FS': ('SN_S',),
        'DET_MP': ('SN_P',),
        'DET_FP': ('SN_P',),
    },

    # SN_S -> NOM_MS | NOM_FS
    'SN_S': {
        'DET_MS': ('NOM_MS',),
        'DET_FS': ('NOM_FS',),
    },

    # SN_P -> NOM_MP | NOM_FP
    'SN_P': {
        'DET_MP': ('NOM_MP',),
        'DET_FP': ('NOM_FP',),
    },

    # ========================================================
    # 5. CONCORDANCIA: DETERMINANTE Y SUSTANTIVO
    # ========================================================

    # NOM_MS -> DET_MS N_MS ADJ_MS_OPT
    'NOM_MS': {
        'DET_MS': ('DET_MS', 'N_MS', 'ADJ_MS_OPT'),
    },

    # NOM_FS -> DET_FS N_FS ADJ_FS_OPT
    'NOM_FS': {
        'DET_FS': ('DET_FS', 'N_FS', 'ADJ_FS_OPT'),
    },

    # NOM_MP -> DET_MP N_MP ADJ_MP_OPT
    'NOM_MP': {
        'DET_MP': ('DET_MP', 'N_MP', 'ADJ_MP_OPT'),
    },

    # NOM_FP -> DET_FP N_FP ADJ_FP_OPT
    'NOM_FP': {
        'DET_FP': ('DET_FP', 'N_FP', 'ADJ_FP_OPT'),
    },

    # ========================================================
    # 6. ADJETIVOS OPCIONALES
    # ========================================================

    # ADJ_MS_OPT -> ADJ_MS | epsilon
    'ADJ_MS_OPT': {
        'ADJ_MS': ('ADJ_MS',),
        'VERBO_S': (),
        'PREP': (),
        'ADV': (),
        'PUNTO': (),
    },

    # ADJ_FS_OPT -> ADJ_FS | epsilon
    'ADJ_FS_OPT': {
        'ADJ_FS': ('ADJ_FS',),
        'VERBO_S': (),
        'PREP': (),
        'ADV': (),
        'PUNTO': (),
    },

    # ADJ_MP_OPT -> ADJ_MP | epsilon
    'ADJ_MP_OPT': {
        'ADJ_MP': ('ADJ_MP',),
        'VERBO_P': (),
        'PREP': (),
        'ADV': (),
        'PUNTO': (),
    },

    # ADJ_FP_OPT -> ADJ_FP | epsilon
    'ADJ_FP_OPT': {
        'ADJ_FP': ('ADJ_FP',),
        'VERBO_P': (),
        'PREP': (),
        'ADV': (),
        'PUNTO': (),
    },
}


def consultar_tabla(no_terminal, token_actual):
    """Consulta la tabla fija. Devuelve tupla, () o None."""
    return TABLA_LL1.get(no_terminal, {}).get(token_actual)


def mostrar_tabla():
    """Muestra solamente las entradas definidas de la tabla."""
    cantidad = sum(len(fila) for fila in TABLA_LL1.values())
    print('TABLA LL(1) DEL ESPANOL - VERSION COMPACTA')
    print(f'No terminales: {len(TABLA_LL1)}')
    print(f'Terminales (incluido $): {len(TERMINALES)}')
    print(f'Entradas validas: {cantidad}')
    print(f'Celdas de error omitidas: '
          f'{len(TABLA_LL1) * len(TERMINALES) - cantidad}')

    for no_terminal, fila in TABLA_LL1.items():
        print(f'\n{no_terminal}:')
        for token, produccion in fila.items():
            lado_derecho = ' '.join(produccion) if produccion else 'epsilon'
            print(f'  Con {token:9s} -> {no_terminal} -> {lado_derecho}')


if __name__ == '__main__':
    mostrar_tabla()
