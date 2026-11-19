# Comparacion experimental - TLP Fase 2

Referencia: etiquetas de aceptacion/rechazo de la CFG para las mismas 45 oraciones.
Los veredictos de spaCy y NLTK proceden de criterios externos definidos previamente; no son una funcion nativa de aceptacion/rechazo.

| Metodo | VP | FP | FN | VN | Precision | Recall | Rechazo correcto | Exactitud |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Parser LL(1) | 28 | 0 | 0 | 17 | 100.00% | 100.00% | 100.00% | 100.00% |
| spaCy + criterio | 25 | 13 | 3 | 4 | 65.79% | 89.29% | 23.53% | 64.44% |
| NLTK + criterio | 16 | 13 | 12 | 4 | 55.17% | 57.14% | 23.53% | 44.44% |
| LLM zero-shot | 23 | 1 | 5 | 16 | 95.83% | 82.14% | 94.12% | 86.67% |
| LLM few-shot | 28 | 0 | 0 | 17 | 100.00% | 100.00% | 100.00% | 100.00% |

## Interpretacion y limites

- La referencia gold se construyo segun el alcance de la CFG. Por ello la coincidencia del parser LL(1) con sus propias reglas no equivale a comprender todo el espanol.
- Las discrepancias de spaCy y NLTK incluyen diferencias de cobertura y de criterio de equivalencia, no necesariamente errores de analisis linguistico.
- Zero-shot y few-shot son una ejecucion por oracion y condicion; no se estima variabilidad entre ejecuciones. Few-shot incluye seis ejemplos externos al corpus.
- Una clasificacion correcta no garantiza una explicacion correcta. Consultar logs de la API para errores de justificacion.
- En el nivel 1 no hay rechazos de referencia: la tasa de rechazo correcto es indefinida (N/D), no cero.
