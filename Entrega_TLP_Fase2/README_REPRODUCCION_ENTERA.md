# Reproducción completa del proyecto — Fase 2

## 1. Objetivo

Esta sección explica cómo reproducir completamente el proyecto de la Fase 2 de Teoría de Lenguajes de Programación, desde el análisis léxico y sintáctico mediante nuestro parser LL(1) hasta las evaluaciones experimentales con spaCy, NLTK y un modelo de lenguaje (LLM) mediante API.

A diferencia de la reproducción de comparaciones existentes, este procedimiento permite **ejecutar los programas, analizar oraciones, generar nuevos resultados, calcular métricas y construir gráficas utilizando las nuevas ejecuciones**.

Los archivos de resultados incluidos originalmente en `Evidencias/` no son necesarios para realizar estas pruebas. Se conservan únicamente como referencia de los experimentos originales.

## 2. Requisitos e instalación

Se necesita Python 3, una terminal de PowerShell y las bibliotecas utilizadas por el proyecto.

Abrir la carpeta principal `Entrega_TLP_Fase2` en Visual Studio Code.

Desde la terminal, instalar las dependencias:

```powershell
python -m pip install ply spacy nltk openai matplotlib
```

Descargar el modelo de español utilizado por spaCy:

```powershell
python -m spacy download es_core_news_sm
```

Descargar los recursos utilizados por NLTK:

```powershell
python -m nltk.downloader cess_esp punkt_tab
```

Comprobar que Python funciona correctamente:

```powershell
python --version
```

Las bibliotecas PLY, spaCy, NLTK y Matplotlib pueden utilizarse localmente. La evaluación con LLM requiere una API Key válida, conexión a Internet y acceso al modelo configurado.

## 3. Preparar la carpeta de trabajo

El proyecto se distribuye con esta estructura:

```text
Entrega_TLP_Fase2/
|
|-- Codigo/
|   |-- gramatica_es_ll1.py
|   |-- conjuntos_es_ll1.py
|   |-- tabla_es_ll1.py
|   |-- lexer_es.py
|   |-- parser_es.py
|   |-- oracion.txt
|   |-- pruebas_parser_es.py
|   |-- evaluar_spacy_es.py
|   |-- evaluar_nltk_es.py
|   |-- evaluar_llm_es.py
|   `-- comparar_resultados_fase2.py
|
|-- Corpus/
|   `-- corpus_es_fase2.csv
|
|-- Evidencias/
|-- Comparacion/
|-- Informe/
`-- README_REPRODUCCION.md
```

Los scripts de evaluación buscan `corpus_es_fase2.csv` dentro de la misma carpeta donde se encuentran los archivos Python.

Por ello, desde la carpeta principal del proyecto, copiar el corpus:

```powershell
Copy-Item .\Corpus\corpus_es_fase2.csv .\Codigo\corpus_es_fase2.csv
```

Después acceder a la carpeta de código:

```powershell
cd .\Codigo
```

Todos los comandos de las siguientes secciones deben ejecutarse desde esta carpeta.

## 4. Primera etapa: ejecutar el analizador léxico

El archivo `lexer_es.py` reconoce las palabras de una oración y las transforma en tokens definidos por nuestro vocabulario controlado.

Abrir `oracion.txt` e introducir una oración, por ejemplo:

```text
Las niñas bonitas leen unos libros en la escuela.
```

Ejecutar:

```powershell
python lexer_es.py
```

El analizador mostrará los tokens identificados, sus valores y sus posiciones dentro del texto.

Esto permite verificar que las palabras sean reconocidas correctamente antes de iniciar el análisis sintáctico.

Si se introduce una palabra que no pertenece al vocabulario, el lexer informará del error correspondiente.

Para realizar otra prueba, modificar nuevamente `oracion.txt` y repetir el comando.

## 5. Segunda etapa: ejecutar nuestro parser LL(1)

El archivo `parser_es.py` utiliza los tokens generados por `lexer_es.py` y la tabla predictiva definida en `tabla_es_ll1.py`.

El parser aplica un algoritmo basado en pila y selecciona producciones de la gramática de acuerdo con el token de entrada.

Ejecutar:

```powershell
python parser_es.py
```

El programa mostrará el procedimiento realizado, incluyendo:

- Estado de la pila.
- Token que está siendo procesado.
- Producción gramatical aplicada.
- Coincidencias entre terminales y tokens.
- Errores sintácticos, si existen.
- Resultado final de aceptación o rechazo.

Por ejemplo:

```text
La niña lee.
```

Resultado esperado: **aceptada**.

```text
Los niños corre.
```

Resultado esperado: **rechazada**, debido a que no cumple con las producciones de concordancia entre sujeto y verbo establecidas en nuestra CFG.

Es importante señalar que el parser comprueba la pertenencia a nuestra gramática formal, no la corrección general de cualquier oración del español.

## 6. Tercera etapa: ejecutar las pruebas automatizadas del parser

Para evaluar múltiples oraciones automáticamente se utiliza:

```powershell
python pruebas_parser_es.py
```

Este script lee el archivo `corpus_es_fase2.csv`, ejecuta el parser sobre cada oración y compara su resultado con la etiqueta de referencia.

El corpus original contiene 45 oraciones distribuidas en tres niveles de complejidad.

Al finalizar, se crea la carpeta:

```text
Codigo/
`-- resultados_es/
    |-- resultados_parser_es.csv
    |-- logs_parser_es.jsonl
    |-- metricas_parser_es.json
    `-- metadatos_ejecucion.json
```

Estos archivos contienen las clasificaciones obtenidas, los registros de análisis, las métricas y la información necesaria para documentar la ejecución.

**Nota:** esta etapa utiliza una carpeta de resultados fija. Si se ejecuta nuevamente, los archivos anteriores de `resultados_es/` pueden sobrescribirse. Se recomienda guardar una copia de los resultados que se deseen conservar.

## 7. Cuarta etapa: ejecutar la evaluación con spaCy

spaCy realiza análisis lingüístico mediante tokenización, identificación de categorías gramaticales y relaciones de dependencia.

No acepta ni rechaza oraciones automáticamente. El proyecto incorpora un criterio externo de equivalencia para transformar su análisis en una clasificación comparable con la CFG.

Ejecutar:

```powershell
python evaluar_spacy_es.py
```

El programa analizará las oraciones del corpus utilizando el modelo `es_core_news_sm`.

Se creará una carpeta identificada con la fecha y hora de ejecución:

```text
Codigo/
`-- resultados_spacy/
    `-- carpeta_de_ejecucion/
        |-- logs_spacy.jsonl
        |-- resultados_spacy.csv
        |-- metricas_spacy.json
        `-- metadatos_spacy.json
```

Los resultados muestran qué análisis realizó spaCy y cómo fueron clasificados mediante el criterio definido para el experimento.

Las diferencias respecto al parser LL(1) constituyen resultados experimentales y no necesariamente errores lingüísticos de spaCy.

## 8. Quinta etapa: ejecutar la evaluación con NLTK

El enfoque de NLTK utiliza un etiquetador de categorías gramaticales entrenado con CESS-ESP y un analizador de sintagmas nominales mediante `RegexpParser`.

Al igual que spaCy, NLTK no proporciona directamente decisiones de aceptación o rechazo. El proyecto utiliza un criterio externo documentado.

Ejecutar:

```powershell
python evaluar_nltk_es.py
```

En esta ejecución, el programa prepara el etiquetador, analiza las oraciones y calcula las métricas correspondientes.

Se creará:

```text
Codigo/
`-- resultados_nltk/
    `-- carpeta_de_ejecucion/
        |-- logs_nltk.jsonl
        |-- resultados_nltk.csv
        |-- metricas_nltk.json
        `-- metadatos_nltk.json
```

Los archivos registran las etiquetas gramaticales, los sintagmas detectados, las clasificaciones resultantes y los datos de la evaluación.

## 9. Sexta etapa: configurar y ejecutar el LLM mediante API

La última herramienta utiliza un modelo de lenguaje al que se le proporcionan explícitamente las producciones de nuestra gramática y el vocabulario permitido.

El experimento considera dos modalidades:

**Zero-shot:** el modelo recibe las reglas de la gramática, pero ningún ejemplo resuelto.

**Few-shot:** el modelo recibe las mismas reglas y seis ejemplos adicionales de aceptación y rechazo.

### Configurar la API Key

Primero se debe disponer de una API Key válida de OpenAI.

En PowerShell, configurar la variable de entorno temporalmente:

```powershell
$clave = Read-Host "Introduce tu API Key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $clave).Password
Remove-Variable clave
```

La clave debe mantenerse privada y nunca incluirse en el código, en el repositorio ni en los archivos de entrega.

### Revisar los prompts sin consumir API

Ejecutar:

```powershell
python evaluar_llm_es.py --limite 1
```

Este comando muestra las instrucciones preparadas sin enviar solicitudes a la API.

### Ejecutar una prueba piloto

Antes de procesar todas las oraciones, se recomienda utilizar:

```powershell
python evaluar_llm_es.py --ejecutar --limite 1
```

Esto realiza dos solicitudes reales: una zero-shot y otra few-shot para la primera oración.

Las consultas a la API pueden generar cargos.

### Ejecutar el experimento completo

Cuando la prueba piloto funcione correctamente:

```powershell
python evaluar_llm_es.py --ejecutar
```

Con el corpus original de 45 oraciones y las dos modalidades activadas, se realizarán 90 consultas.

También es posible ejecutar una sola modalidad:

```powershell
python evaluar_llm_es.py --ejecutar --modo zero-shot
```

O bien:

```powershell
python evaluar_llm_es.py --ejecutar --modo few-shot
```

Para generar la comparación completa con ambos modos, se recomienda ejecutar el experimento completo en una sola corrida.

### Resultados generados

La ejecución creará una carpeta nueva:

```text
Codigo/
`-- resultados_llm/
    `-- carpeta_de_ejecucion/
        |-- prompts_plantilla.json
        |-- prompts_exactos.jsonl
        |-- logs_llm.jsonl
        |-- resultados_llm.csv
        |-- metricas_llm.json
        `-- metadatos_llm.json
```

Los archivos permiten estudiar los prompts enviados, las respuestas originales del modelo, las justificaciones y los resultados de ambas modalidades.

Para reproducir las condiciones económicas del experimento original, se debe utilizar la versión optimizada de `evaluar_llm_es.py` cuya configuración era `reasoning.effort="none"`, `max_output_tokens=200` y sin reintentos automáticos.

La versión no optimizada del script puede utilizar mayor cantidad de tokens. Se recomienda revisar sus parámetros antes de realizar consultas.

## 10. Séptima etapa: construir comparaciones a partir de los nuevos resultados

Una vez ejecutados los cuatro enfoques, es posible generar las tablas y gráficas utilizando exclusivamente los archivos producidos en las nuevas pruebas.

**No es necesario utilizar los resultados originales incluidos en `Evidencias/`.**

Los programas de spaCy, NLTK y LLM crean carpetas distintas en cada ejecución. Por ello, primero debemos identificar las más recientes.

Desde PowerShell, permaneciendo en `Codigo`, ejecutar:

```powershell
$rutaSpaCy = (Get-ChildItem .\resultados_spacy -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName

$rutaNLTK = (Get-ChildItem .\resultados_nltk -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName

$rutaLLM = (Get-ChildItem .\resultados_llm -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

Después ejecutar el comparador con los resultados recién generados:

```powershell
python .\comparar_resultados_fase2.py `
  --corpus .\corpus_es_fase2.csv `
  --parser .\resultados_es\resultados_parser_es.csv `
  --spacy "$rutaSpaCy\resultados_spacy.csv" `
  --nltk "$rutaNLTK\resultados_nltk.csv" `
  --llm "$rutaLLM\resultados_llm.csv" `
  --salida .\comparacion_propia
```

El comparador comprobará que los resultados correspondan al mismo corpus y generará:

```text
Codigo/
`-- comparacion_propia/
    |-- comparacion_metricas.csv
    |-- comparacion_oracion_por_oracion.csv
    |-- comparacion_por_nivel.csv
    |-- errores_comparados.csv
    |-- resultados_recalculados.json
    |-- resumen_comparativo.md
    |-- grafico_metricas.png
    `-- grafico_por_nivel.png
```

Esta etapa no realiza consultas al LLM y no consume tokens de API, ya que utiliza los resultados generados anteriormente.

Si solamente se desean obtener tablas sin instalar Matplotlib, puede agregarse el parámetro `--sin-graficas`.

## 11. Utilizar oraciones propias y generar un experimento nuevo

También es posible elaborar un corpus personalizado y repetir la evaluación completa.

Para hacerlo:

1. Conservar una copia del archivo `Corpus/corpus_es_fase2.csv` original.
2. Modificar la copia ubicada en `Codigo/corpus_es_fase2.csv` para introducir nuevas oraciones.
3. Mantener las columnas obligatorias, los identificadores únicos y los niveles de complejidad.
4. Definir previamente las etiquetas esperadas de aceptación o rechazo de acuerdo con la CFG.
5. Ejecutar nuevamente los programas en el orden indicado en las secciones anteriores.

Para las pruebas automatizadas, el corpus debe contener al menos 40 oraciones, distribuidas entre los niveles 1, 2 y 3.

Las columnas del corpus son:

| Columna | Descripción |
|---|---|
| `id` | Identificador único de la oración. |
| `nivel` | Complejidad: 1, 2 o 3. |
| `oracion` | Texto que se analizará. |
| `etiqueta_esperada` | Aceptada o rechazada según la CFG. |
| `etapa_esperada` | Aceptada, error léxico o error sintáctico. |
| `estructura_esperada` | Estructura prevista cuando corresponda. |
| `justificacion` | Explicación de la etiqueta de referencia. |

El mismo archivo debe utilizarse en todos los enfoques para que sus resultados sean comparables.

Adicionalmente, el script del LLM comprueba que las oraciones utilizadas como ejemplos few-shot no aparezcan en el corpus de evaluación. Si existe alguna coincidencia, será necesario utilizar otro conjunto de oraciones de prueba o revisar los ejemplos para evitar que se filtren respuestas al experimento.

**Importante:** modificar el corpus y generar resultados nuevos no implica necesariamente obtener los mismos porcentajes del experimento original. Las métricas dependerán de las oraciones utilizadas, las etiquetas de referencia y el comportamiento de los modelos en cada ejecución.

## 12. Diferencia entre reproducir resultados y ejecutar el proyecto

Este repositorio permite realizar dos procedimientos diferentes:

**Reproducción de las comparaciones originales:** se utilizan los archivos ya guardados en `Evidencias/` para volver a calcular métricas y generar gráficas. No se ejecutan nuevamente los analizadores.

**Reproducción completa del proyecto:** se ejecutan el lexer, el parser LL(1), las pruebas automatizadas, spaCy, NLTK y el LLM. Cada herramienta produce nuevos registros, que posteriormente pueden utilizarse para generar una comparación independiente.

La segunda opción permite comprobar el funcionamiento real de cada componente y realizar experimentos propios.

## 13. Consideraciones finales

Los modelos de NLP y los servicios de LLM pueden producir diferencias entre ejecuciones debido a cambios de versión, configuración o comportamiento del modelo.

Los resultados del parser corresponden a la gramática formal implementada, mientras que los de spaCy y NLTK utilizan criterios externos de equivalencia. El LLM recibe directamente las reglas de producción, pero sus decisiones no constituyen una demostración formal de pertenencia a la gramática.

Los registros, prompts y métricas permiten documentar estas diferencias y respaldar los resultados experimentales.

Con este procedimiento es posible **reproducir toda la Fase 2 de forma independiente**, obtener nuevas evidencias y construir comparaciones basadas en ejecuciones propias, sin depender de los resultados previamente incluidos en el repositorio.