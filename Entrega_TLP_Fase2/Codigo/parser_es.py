# ------------------------------------------------------------
# PARSER PREDICTIVO LL(1) PARA UN SUBCONJUNTO DEL ESPANOL
# Fase 2 - Analisis sintactico de oraciones
# ------------------------------------------------------------
# Utiliza el lexer_es.py y consulta la tabla fija tabla_es_ll1.py.
# NO calcula FIRST ni FOLLOW, y NO reconstruye la tabla.
# ------------------------------------------------------------

from pathlib import Path

from lexer_es import tokenizar
from gramatica_es_ll1 import SIMBOLO_INICIAL, FIN_ENTRADA
from tabla_es_ll1 import TABLA_LL1, TERMINALES


# Un conjunto permite comprobar rapidamente si un simbolo es terminal.
TERMINALES = set(TERMINALES)


# ------------------------------------------------------------
# 1. FUNCIONES AUXILIARES PARA LOS ERRORES
# ------------------------------------------------------------

def obtener_ubicacion(token, texto):
    """Devuelve la linea y columna del token, o del fin de entrada."""
    if token is not None:
        ultima_nueva_linea = texto.rfind('\n', 0, token.lexpos)
        columna = token.lexpos - ultima_nueva_linea
        return token.lineno, columna

    linea = texto.count('\n') + 1
    columna = len(texto.rsplit('\n', 1)[-1]) + 1
    return linea, columna


def describir_token(token):
    """Describe el token actual para imprimirlo en la terminal."""
    if token is None:
        return 'fin de entrada ($)'
    return f'{token.value!r} ({token.type})'


def crear_error_sintactico(simbolo, token, texto, esperados):
    """Crea un mensaje que indica el error y los tokens esperados."""
    linea, columna = obtener_ubicacion(token, texto)
    esperado = ', '.join(esperados) if esperados else 'sin opciones validas'
    return (
        f'Error sintactico en linea {linea}, columna {columna}: '
        f'se encontro {describir_token(token)} al procesar {simbolo}. '
        f'Se esperaba: {esperado}.'
    )


def mostrar_fila(pila, token, accion):
    """Muestra una fila del recorrido de la pila."""
    contenido = ' '.join(pila)
    if len(contenido) > 58:
        # Mostrar la parte derecha, donde se encuentra la cima.
        contenido = '...' + contenido[-55:]
    actual = describir_token(token)
    print(f'{contenido:<58} | {actual:<24} | {accion}')


# ------------------------------------------------------------
# 2. ALGORITMO DEL PARSER PREDICTIVO LL(1)
# ------------------------------------------------------------

def analizar_tokens(lista_tokens, texto='', mostrar_pasos=False):
    """
    Comprueba si la secuencia de tokens pertenece a nuestra CFG.

    Retorna:
        (True, []) si la oracion es aceptada.
        (False, [mensaje]) si se produce un error sintactico.
    """

    # La cima de la pila esta a la DERECHA.
    pila = [FIN_ENTRADA, SIMBOLO_INICIAL]
    indice = 0

    if mostrar_pasos:
        print('\nANALISIS SINTACTICO LL(1) - ESPANOL')
        print('=' * 115)
        print(f'{"PILA (cima a la derecha)":<58} | {"TOKEN ACTUAL":<24} | ACCION')
        print('-' * 115)

    while pila:
        # 1) Consultar la cima y el token actual.
        cima = pila[-1]
        token_actual = lista_tokens[indice] if indice < len(lista_tokens) else None
        tipo_actual = token_actual.type if token_actual is not None else FIN_ENTRADA

        # 2) Si la cima es TERMINAL, debe coincidir con el token actual.
        if cima in TERMINALES:
            if cima != tipo_actual:
                error = crear_error_sintactico(cima, token_actual, texto, [cima])
                if mostrar_pasos:
                    mostrar_fila(pila, token_actual, 'ERROR: terminal inesperado')
                return False, [error]

            if mostrar_pasos:
                accion = 'ENTRADA ACEPTADA' if cima == FIN_ENTRADA else f'Coincide {cima}; avanzar'
                mostrar_fila(pila, token_actual, accion)

            pila.pop()

            # El marcador de fin no corresponde a un token del lexer.
            if cima == FIN_ENTRADA:
                return True, []

            indice += 1
            continue

        # 3) Si la cima es NO TERMINAL, buscar la produccion fija.
        if cima not in TABLA_LL1:
            return False, [f'Error interno: simbolo no reconocido en la pila: {cima}']

        # Una sola CONSULTA a la tabla, sin construirla nuevamente.
        produccion = TABLA_LL1[cima].get(tipo_actual)

        # None significa celda vacia: error sintactico.
        # () significa epsilon: produccion valida que no consume tokens.
        if produccion is None:
            esperados = sorted(TABLA_LL1[cima].keys())
            error = crear_error_sintactico(cima, token_actual, texto, esperados)
            if mostrar_pasos:
                mostrar_fila(pila, token_actual, 'ERROR: celda sin produccion')
            return False, [error]

        if mostrar_pasos:
            derecha = 'epsilon' if produccion == () else ' '.join(produccion)
            mostrar_fila(pila, token_actual, f'Aplicar {cima} -> {derecha}')

        # Reemplazar el no terminal por su produccion.
        pila.pop()
        for simbolo in reversed(produccion):
            pila.append(simbolo)

    return False, ['Error interno: la pila quedo vacia antes de reconocer $.']


# ------------------------------------------------------------
# 3. CONEXION DEL LEXER CON EL PARSER
# ------------------------------------------------------------

def analizar(texto, mostrar_pasos=False):
    """Tokeniza una oracion y luego ejecuta el parser LL(1)."""
    lista_tokens, errores_lexicos = tokenizar(texto)

    if errores_lexicos:
        return False, [
            'No se realizo el analisis sintactico porque hay errores lexicos.'
        ] + errores_lexicos

    return analizar_tokens(lista_tokens, texto, mostrar_pasos)


# ------------------------------------------------------------
# 4. EJECUCION PRINCIPAL
# ------------------------------------------------------------

def main():
    """Lee oracion.txt, analiza su contenido y muestra el resultado."""
    archivo = Path(__file__).resolve().parent / 'oracion.txt'

    try:
        texto = archivo.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        print("No se encontro 'oracion.txt' junto a parser_es.py")
        return

    print('ORACION ANALIZADA:', texto)
    aceptada, mensajes = analizar(texto, mostrar_pasos=True)

    print('\nRESULTADO')
    print('=' * 70)
    if aceptada:
        print('ORACION ACEPTADA: cumple con nuestra gramatica LL(1).')
    else:
        print('ORACION RECHAZADA.')
        for mensaje in mensajes:
            print('-', mensaje)


if __name__ == '__main__':
    main()
