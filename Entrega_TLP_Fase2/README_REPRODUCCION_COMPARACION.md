# PROYECTO TLP FASE 2 — INFORME Y EVIDENCIAS



## RESULTADOS EVALUADOS

Corpus: 45 oraciones (15 por nivel; 28 aceptadas, 17 rechazadas por la CFG).

* Parser LL(1): 45/45 coincidencias; exactitud 100 %.
* spaCy + criterio: 29/45; exactitud 64.44 %.
* NLTK + criterio: 20/45; exactitud 44.44 %.
* LLM zero-shot: 39/45; exactitud 86.67 %.
* LLM few-shot: 45/45; exactitud 100 %.

## REPRODUCIR LA COMPARACION SIN CONSUMIR API

1. Descomprimir este ZIP o clonar Repo.
2. Abrir PowerShell en la carpeta raiz Entrega\_TLP\_Fase2 (la carpeta que contiene Codigo, Corpus y Evidencias).
3. Instalar Python y matplotlib (solo para generar graficas): python -m pip install matplotlib
4. Ejecutar este comando en una sola linea, desde esa carpeta raiz:

python .\\Codigo\\comparar\_resultados\_fase2.py --corpus .\\Corpus\\corpus\_es\_fase2.csv --parser .\\Evidencias\\Parser\\resultados\_parser\_es.csv --spacy .\\Evidencias\\spaCy\\resultados\_spacy.csv --nltk .\\Evidencias\\NLTK\\resultados\_nltk.csv --llm .\\Evidencias\\LLM\\resultados\_llm.csv --salida .\\Comparacion\_REGENERADA

5. Comparar el nuevo archivo Comparacion\_REGENERADA/comparacion\_metricas.csv con Comparacion/comparacion\_metricas.csv. No se requiere llamar a la API. Para ejecutar sin instalar matplotlib, añadir --sin-graficas.

## EJECUTAR ENFOQUES (OPCIONAL)

Dependencias de Python: ply, spacy, nltk, openai, matplotlib.

* Parser: python parser\_es.py, luego python pruebas\_parser\_es.py.
* spaCy: python -m spacy download es\_core\_news\_sm; python evaluar\_spacy\_es.py.
* NLTK: python -m nltk.downloader cess\_esp punkt\_tab; python evaluar\_nltk\_es.py.
* LLM: configurar OPENAI\_API\_KEY en variable de entorno; revisar la vista previa del script; llamadas a API generan costo.



## NAVEGACION

Informe/: documento PDF.
Corpus/: base etiquetada.
Codigo/: fuentes y comparador.
Evidencias/: CSV, JSONL y metadatos originales de cada enfoque.
Comparacion/: tablas y figuras derivadas; no son logs originales.
MANIFIESTO\_SHA256.txt: hash de cada archivo del paquete.

No se incluye ninguna API key, token secreto ni dato de autenticación.

