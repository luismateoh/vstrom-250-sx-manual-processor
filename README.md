# V-Strom 250 SX - Procesador de Manuales

Herramienta local para convertir los manuales de la moto (PDFs escaneados en imágenes) en un paquete de datos optimizado para la PWA.

## ¿Qué hace?

1. Convierte cada página del PDF en una imagen WebP optimizada.
2. Extrae el texto de cada página usando OCR (Tesseract).
3. Genera un `manifest.json` con el texto, metadatos y coordenadas de cada bloque de texto.
4. Produce una estructura lista para copiar a la PWA.

## Requisitos

- Python 3.10+
- Tesseract OCR instalado en tu sistema

### Instalar Tesseract

- **macOS**: `brew install tesseract tesseract-lang` (recomendado instalar idiomas adicionales)
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng`
- **Windows**: descarga el instalador desde [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

1. Copia tus PDFs a la carpeta `input/`.
2. Ejecuta el procesador:

```bash
python -m src.main
```

Opcionalmente puedes especificar idioma y calidad:

```bash
python -m src.main --lang spa+eng --quality 80 --dpi 200
```

3. Los resultados quedan en `output/<nombre-del-pdf>/`:

```
output/
  owner-manual/
    pages/
      page_001.webp
      page_002.webp
      ...
    manifest.json
```

## Estructura del manifest.json

```json
{
  "id": "owner-manual",
  "title": "owner-manual",
  "source": "input/owner-manual.pdf",
  "processedAt": "2026-07-06T12:00:00",
  "pageCount": 200,
  "language": "spa+eng",
  "pages": [
    {
      "pageNumber": 1,
      "image": "pages/page_001.webp",
      "text": "Texto completo de la página...",
      "blocks": [
        {
          "text": "Bloque de texto",
          "bbox": { "x": 10, "y": 20, "width": 100, "height": 30 }
        }
      ]
    }
  ]
}
```

## Copiar a la PWA

Copia la carpeta generada dentro de `vstrom-250-sx/public/manuals/`:

```bash
cp -r output/owner-manual ../vstrom-250-sx/public/manuals/
```

La PWA leerá los manifiestos desde esa carpeta.
