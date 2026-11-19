# ------------------------------------------------------------
# LEXER PARA UN SUBCONJUNTO CONTROLADO DEL ESPANOL
# Fase 2 - Parser predictivo LL(1)
# ------------------------------------------------------------
# Basado en el enfoque del lexer de la Fase 1 con PLY.
# Produce los 19 tokens terminales definidos en tabla_es_ll1.py.
# PALABRA es un token auxiliar de PLY: se reclasifica o se
# registra como error, pero NUNCA se devuelve al parser.
# ------------------------------------------------------------

from pathlib import Path

import ply.lex as lex


# 1. TIPOS DE TOKEN
# Son exactamente los terminales de la gramática española,
# excepto '$' (que corresponde al final de entrada del parser),
# más el token auxiliar PALABRA requerido por esta regla de PLY.

tokens = (
    'DET_MS', 'DET_FS', 'DET_MP', 'DET_FP',
    'N_MS', 'N_FS', 'N_MP', 'N_FP',
    'ADJ_MS', 'ADJ_FS', 'ADJ_MP', 'ADJ_FP',
    'PRON_S', 'PRON_P',
    'VERBO_S', 'VERBO_P',
    'PREP', 'ADV', 'PUNTO',
    'PALABRA',  # auxiliar; nunca llega al parser
)


# 2. VOCABULARIO CONTROLADO
# Cada palabra tiene una sola categoría para evitar ambigüedades.
# El vocabulario se fija ANTES de evaluar el corpus de la Fase 2.
# M/F = masculino/femenino; S/P = singular/plural.

VOCABULARIO_POR_TOKEN = {
    'DET_MS': ('el', 'un'),
    'DET_FS': ('la', 'una'),
    'DET_MP': ('los', 'unos'),
    'DET_FP': ('las', 'unas'),

    'N_MS': (
        'niño', 'profesor', 'perro', 'gato', 'libro', 'parque',
        'alumno', 'caballo', 'cuaderno', 'coche', 'jardín',
        'zapato', 'plato', 'pájaro', 'árbol',
    ),
    'N_FS': (
        'niña', 'profesora', 'perra', 'gata', 'casa', 'escuela',
        'mesa', 'manzana', 'puerta', 'flor', 'canción',
        'maestra', 'pelota', 'silla', 'biblioteca', 'ciudad',
    ),
    'N_MP': (
        'niños', 'profesores', 'perros', 'gatos', 'libros', 'parques',
        'alumnos', 'caballos', 'cuadernos', 'coches', 'jardines',
        'zapatos', 'platos', 'pájaros', 'árboles',
    ),
    'N_FP': (
        'niñas', 'profesoras', 'perras', 'gatas', 'casas', 'escuelas',
        'mesas', 'manzanas', 'puertas', 'flores', 'canciones',
        'maestras', 'pelotas', 'sillas', 'bibliotecas', 'ciudades',
    ),

    'ADJ_MS': (
        'bonito', 'pequeño', 'alto', 'rápido', 'nuevo',
        'blanco', 'rojo', 'contento', 'cansado', 'tranquilo',
    ),
    'ADJ_FS': (
        'bonita', 'pequeña', 'alta', 'rápida', 'nueva',
        'blanca', 'roja', 'contenta', 'cansada', 'tranquila',
    ),
    'ADJ_MP': (
        'bonitos', 'pequeños', 'altos', 'rápidos', 'nuevos',
        'blancos', 'rojos', 'contentos', 'cansados', 'tranquilos',
    ),
    'ADJ_FP': (
        'bonitas', 'pequeñas', 'altas', 'rápidas', 'nuevas',
        'blancas', 'rojas', 'contentas', 'cansadas', 'tranquilas',
    ),

    # Solo pronombres de tercera persona para concordar con los verbos.
    # 'el' (sin tilde) es determinante y 'él' (con tilde) es pronombre.
    'PRON_S': ('él', 'ella'),
    'PRON_P': ('ellos', 'ellas'),

    'VERBO_S': (
        'lee', 'corre', 'come', 'canta', 'estudia', 'escribe',
        'duerme', 'trabaja', 'camina', 'juega', 'salta',
        'observa', 'compra', 'mira', 'busca', 'escucha',
        'vive', 'cocina', 'pinta', 'dibuja', 'abre', 'cierra',
    ),
    'VERBO_P': (
        'leen', 'corren', 'comen', 'cantan', 'estudian', 'escriben',
        'duermen', 'trabajan', 'caminan', 'juegan', 'saltan',
        'observan', 'compran', 'miran', 'buscan', 'escuchan',
        'viven', 'cocinan', 'pintan', 'dibujan', 'abren', 'cierran',
    ),

    # La CFG solo permite PREP + SN: p. ej., 'en el parque'.
    # Contracciones 'al' y 'del' no se reconocen en esta versión.
    'PREP': ('en', 'con', 'sobre', 'bajo', 'para', 'sin', 'de', 'a'),
    'ADV': (
        'rápidamente', 'lentamente', 'silenciosamente',
        'cuidadosamente', 'alegremente', 'tranquilamente',
        'aquí', 'allí', 'bien', 'mal',
    ),
}


# Transformar las listas anteriores en un único diccionario:
# {"niña": "N_FS", "leen": "VERBO_P", ...}
# Detectar duplicados evita asignaciones léxicas contradictorias.
VOCABULARIO = {}
for categoria, palabras in VOCABULARIO_POR_TOKEN.items():
    for palabra in palabras:
        if palabra in VOCABULARIO:
            raise ValueError(f"Palabra repetida en el vocabulario: {palabra!r}")
        VOCABULARIO[palabra] = categoria


# 3. REGLAS LEXICAS

t_PUNTO = r'\.'


def t_PALABRA(t):
    r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+'
    palabra = t.value.casefold()
    categoria = VOCABULARIO.get(palabra)

    if categoria is None:
        t.lexer.errores.append(
            f"Palabra fuera del vocabulario: {t.value!r} "
            f"(linea {t.lineno}, columna {obtener_columna(t)})"
        )
        return None  # No entregar palabras desconocidas al parser.

    # Reemplazar el token provisional PALABRA por uno de la CFG.
    t.type = categoria
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


t_ignore = ' \t\r'


def obtener_columna(t):
    ultima_nueva_linea = lexer.lexdata.rfind('\n', 0, t.lexpos)
    return t.lexpos - ultima_nueva_linea


def t_error(t):
    t.lexer.errores.append(
        f"Caracter no reconocido: {t.value[0]!r} "
        f"(linea {t.lineno}, columna {obtener_columna(t)})"
    )
    t.lexer.skip(1)


# 4. CONSTRUCCION DEL LEXER
lexer = lex.lex()


# 5. FUNCION REUTILIZABLE POR EL FUTURO PARSER

def tokenizar(texto):
    """Devuelve (lista_tokens, errores_lexicos) para una oración."""
    lexer.lineno = 1
    lexer.errores = []
    lexer.input(texto)

    lista_tokens = []
    while True:
        token = lexer.token()
        if token is None:
            break
        lista_tokens.append(token)

    return lista_tokens, list(lexer.errores)


# 6. DEMOSTRACION INDEPENDIENTE

def miLexer():
    """Lee oracion.txt y muestra cada token con su posición."""
    archivo = Path(__file__).resolve().parent / 'oracion.txt'

    try:
        texto = archivo.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        print("No se encontro 'oracion.txt' junto a lexer_es.py")
        return

    lista_tokens, errores = tokenizar(texto)
    print('ORACION:', texto)
    print('\nTOKENS ENCONTRADOS')
    print('-' * 56)
    for tok in lista_tokens:
        print(f'{tok.type:<10} {tok.value:<16} linea={tok.lineno} columna={obtener_columna(tok)}')

    if errores:
        print('\nERRORES LEXICOS')
        for error in errores:
            print('-', error)
    else:
        print('\nNo se encontraron errores lexicos.')


if __name__ == '__main__':
    miLexer()
