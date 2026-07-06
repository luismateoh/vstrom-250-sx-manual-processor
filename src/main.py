import argparse
import sys
from pathlib import Path

from tqdm import tqdm

from src.config import ProcessorConfig
from src.extractor import PdfExtractor
from src.manifest_builder import ManifestBuilder
from src.ocr_engine import OcrEngine


def find_pdfs(input_dir: Path) -> list[Path]:
    pdfs = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    return pdfs


def process_pdf(pdf_path: Path, config: ProcessorConfig) -> Path:
    manual_id = pdf_path.stem
    title = manual_id.replace("_", " ").replace("-", " ").title()
    output_base = config.output_dir / manual_id
    pages_dir = output_base / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    extractor = PdfExtractor(pdf_path, dpi=config.dpi, quality=config.quality, fmt=config.fmt)
    ocr = OcrEngine(lang=config.lang)

    try:
        ocr.check()
    except RuntimeError as e:
        print(f"⚠️  {e}", file=sys.stderr)
        print("Continuando solo con extracción de imágenes (sin OCR)...", file=sys.stderr)
        ocr = None

    builder = ManifestBuilder(manual_id, title, pdf_path, config.lang)

    for page_number, img in tqdm(extractor, total=len(extractor), desc=f"Procesando {manual_id}"):
        filename = f"page_{page_number:03d}.{config.fmt}"
        img_path = pages_dir / filename
        extractor.save_page(img, img_path)

        relative_image = str(Path("pages") / filename)

        if ocr:
            result = ocr.process_image(img)
            builder.add_page(
                page_number=page_number,
                image=relative_image,
                text=result["text"],
                blocks=result["blocks"],
                word_count=result["wordCount"],
            )
        else:
            builder.add_page(
                page_number=page_number,
                image=relative_image,
                text="",
                blocks=[],
                word_count=0,
            )

    extractor.close()

    manifest_path = builder.save(output_base / "manifest.json")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="Procesador de manuales V-Strom 250 SX")
    parser.add_argument("--input", default="input", help="Carpeta con PDFs")
    parser.add_argument("--output", default="output", help="Carpeta de salida")
    parser.add_argument("--dpi", type=int, default=200, help="DPI para renderizar páginas")
    parser.add_argument("--quality", type=int, default=85, help="Calidad WebP/JPEG")
    parser.add_argument("--lang", default="spa+eng", help="Idiomas OCR (ej: spa+eng)")
    parser.add_argument("--fmt", default="webp", choices=["webp", "jpeg", "png"], help="Formato de imagen")
    args = parser.parse_args()

    config = ProcessorConfig(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        dpi=args.dpi,
        quality=args.quality,
        lang=args.lang,
        fmt=args.fmt,
    )

    if not config.input_dir.exists():
        print(f"Carpeta de entrada no existe: {config.input_dir}", file=sys.stderr)
        sys.exit(1)

    pdfs = find_pdfs(config.input_dir)
    if not pdfs:
        print(f"No se encontraron PDFs en {config.input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"PDFs encontrados: {len(pdfs)}")
    for pdf in pdfs:
        manifest = process_pdf(pdf, config)
        print(f"✅ Guardado: {manifest}")


if __name__ == "__main__":
    main()
