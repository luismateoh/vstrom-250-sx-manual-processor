# Memoria del proyecto: V-Strom 250 SX Manual Processor

## Propósito

Herramienta local para convertir los manuales de la moto (PDFs escaneados, es decir, imágenes dentro de PDF) en un paquete de datos optimizado para consumir por la PWA `vstrom-250-sx`.

## Stack

- **Python 3.12**
- **PyMuPDF (fitz)**: renderiza cada página del PDF a imagen PNG a alta resolución.
- **Pillow**: convierte y optimiza las imágenes a WebP.
- **pytesseract**: extrae texto de las imágenes (OCR) usando Tesseract.
- **tqdm**: barras de progreso.

## Flujo de procesamiento

1. Lee todos los PDFs de `input/`.
2. Para cada página:
   - Renderiza a imagen usando PyMuPDF al DPI configurado (default 200).
   - Guarda como WebP con calidad configurable (default 85).
   - Ejecuta OCR con Tesseract para obtener:
     - Texto completo de la página.
     - Bloques de texto con coordenadas (`bbox`) y confianza.
3. Genera un `manifest.json` por manual con metadata y todos los datos de las páginas.

## Estructura de salida

```
output/
  <manual-id>/
    pages/
      page_001.webp
      page_002.webp
      ...
    manifest.json
```

## Cómo usar

```bash
# Activar entorno
source .venv/bin/activate

# Procesar todos los PDFs de input/
python -m src.main --lang eng+spa

# Opciones
python -m src.main --lang eng+spa --dpi 200 --quality 85
```

## Requisitos del sistema

Tesseract OCR debe estar instalado:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang
```

## Decisiones técnicas

- **OCR en Python, no en el navegador**: Tesseract.js en el cliente es pesado y lento. Procesar una vez en local y servir texto listo es más eficiente.
- **WebP**: mejor relación calidad/tamaño que JPEG/PNG para documentos escaneados.
- **Bloques con coordenadas**: permiten resaltar palabras buscadas sobre la imagen en la PWA.
- **Idioma OCR `eng+spa`**: los manuales actuales están en inglés pero pueden tener términos en español.

## Formato del manifest.json

```json
{
  "id": "vstrom-250-sx-owners-manual-2024-en",
  "title": "V-Strom 250 SX Owners Manual 2024 EN",
  "source": "input/vstrom-250-sx-owners-manual-2024-en.pdf",
  "processedAt": "2026-07-06T...",
  "pageCount": 204,
  "language": "eng+spa",
  "pages": [
    {
      "pageNumber": 1,
      "image": "pages/page_001.webp",
      "text": "...",
      "wordCount": 123,
      "blocks": [
        {
          "text": "FOREWORD",
          "bbox": {"x": 103, "y": 63, "width": 184, "height": 23},
          "conf": 96
        }
      ]
    }
  ]
}
```

## Manuales actuales

| Archivo | ID generado | Páginas | Tipo |
|---------|-------------|---------|------|
| `vstrom-sx-specifications.pdf` | `vstrom-sx-specifications` | 3 | Especificaciones/folleto |
| `vstrom-250-parts-catalogue-ds250rlm3.pdf` | `vstrom-250-parts-catalogue-ds250rlm3` | 114 | Catálogo de partes |
| `vstrom-250-sx-owners-manual-2024-en.pdf` | `vstrom-250-sx-owners-manual-2024-en` | 204 | Manual del propietario (inglés) |

## Problemas conocidos

- Los PDFs escaneados con imágenes de baja calidad producen OCR menos preciso.
- `ds250rlm3` se mantiene en mayúsculas mediante mapeo especial en `manifest_builder.py`.

## Próximos pasos sugeridos

- Mejorar el título automático detectando portada/índice.
- Generar índice de capítulos automáticamente.
- Opción de procesar solo imágenes (sin OCR) para PDFs no escaneados.
- Reducir más el tamaño de las imágenes si la PWA se vuelve muy pesada.
