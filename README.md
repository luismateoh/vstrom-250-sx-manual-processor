# V-Strom 250 SX - Procesador de Manuales

Herramienta local para convertir los manuales de la moto (PDFs escaneados en imágenes) en un paquete de datos optimizado para la PWA.

## ¿Qué hace?

1. Convierte cada página del PDF en una imagen WebP optimizada.
2. Extrae el texto de cada página: usa la **capa de texto del PDF** cuando la
   tiene, y recurre al **OCR (Tesseract)** solo en páginas escaneadas.
3. Genera un `manifest.json` con el texto, metadatos y coordenadas de cada palabra.
4. Escribe un `index.json` con todos los manuales, listo para copiar a la PWA.

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

Las páginas se procesan en paralelo, una por núcleo disponible.

### Opciones

| Opción | Por defecto | Para qué sirve |
|---|---|---|
| `--input` | `input` | Carpeta con los PDFs |
| `--output` | `output` | Carpeta de salida |
| `--lang` | `spa+eng` | Idiomas de Tesseract |
| `--dpi` | `200` | Resolución de render. Subirlo mejora el OCR en escaneos pobres, a costa de tiempo y peso |
| `--quality` | `85` | Calidad WebP/JPEG |
| `--fmt` | `webp` | `webp`, `jpeg` o `png` |
| `--workers` | nº de núcleos | Páginas en paralelo. `1` fuerza el modo secuencial |
| `--min-conf` | `30` | Confianza mínima del OCR. Las palabras por debajo se descartan por ruido; `0` conserva todo |
| `--psm` | auto | Page segmentation mode de Tesseract, para páginas con maquetación difícil |
| `--force` | — | Reprocesa manuales que ya tienen `manifest.json` (por defecto se omiten) |
| `--force-ocr` | — | Ignora la capa de texto del PDF y usa OCR en todas las páginas |

```bash
python -m src.main --lang spa+eng --dpi 300 --min-conf 40
```

3. Los resultados quedan en `output/<id-del-manual>/`, donde el id es el nombre
   del PDF convertido a slug (`Manual de PARTES 250SX.pdf` -> `manual-de-partes-250sx`):

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
          "bbox": { "x": 10, "y": 20, "width": 100, "height": 30 },
          "conf": 96
        }
      ],
      "wordCount": 412
    }
  ]
}
```

## Copiar a la PWA

Copia la carpeta generada dentro de `public/manuals/` de la PWA
[vstrom-250-sx](https://github.com/luismateoh/vstrom-250-sx):

```bash
cp -r output/* ../vstrom-250-sx/public/manuals/
```

La PWA lee `index.json` para listar los manuales y cada `manifest.json` para
mostrarlos. Ambos los genera el procesador, no hay que editarlos a mano.

## Notas sobre la extracción de texto

- **La capa de texto del PDF manda.** Muchos manuales "escaneados" en realidad
  traen texto embebido: es exacto (tildes incluidas), conserva las coordenadas
  por palabra y se lee unas 1000x más rápido que pasar el OCR. El procesador la
  usa cuando existe y solo cae al OCR en las páginas que no la tienen. Cada
  manual informa cuántas páginas salieron de cada vía.
- Si la capa de texto de un PDF está corrupta o mal codificada, `--force-ocr`
  la ignora por completo.

### Sobre el OCR

- Tesseract corre **una sola vez por página**: `image_to_data` ya devuelve el
  texto palabra por palabra, así que el texto completo se reconstruye a partir
  de sus coordenadas en vez de invocar a Tesseract por segunda vez.
- La imagen se convierte a escala de grises antes del OCR.
- Las palabras por debajo de `--min-conf` se descartan. Son en su mayoría ruido
  del escaneo (`17-Inch/(4358cm)lreariwheel` y similares) que ensucia la
  búsqueda de la PWA. El proceso informa cuántas descartó.
