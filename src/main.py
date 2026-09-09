import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tqdm import tqdm

from src.config import ProcessorConfig
from src.extractor import PdfExtractor
from src.manifest_builder import ManifestBuilder, slugify
from src.ocr_engine import OcrEngine

_ctx: dict = {}


def find_pdfs(input_dir: Path) -> list[Path]:
    return sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))


def _init_worker(pdf_path: Path, pages_dir: Path, config: ProcessorConfig, use_ocr: bool):
    # Cada proceso corre su propio Tesseract; sin esto, cada uno abre además su
    # pool de hilos OpenMP y los N procesos se pelean por los mismos núcleos.
    os.environ["OMP_THREAD_LIMIT"] = "1"
    _ctx["extractor"] = PdfExtractor(
        pdf_path, dpi=config.dpi, quality=config.quality, fmt=config.fmt
    )
    _ctx["ocr"] = (
        OcrEngine(lang=config.lang, min_conf=config.min_conf, psm=config.psm)
        if use_ocr
        else None
    )
    _ctx["pages_dir"] = pages_dir
    _ctx["fmt"] = config.fmt
    _ctx["force_ocr"] = config.force_ocr


def _process_page(page_number: int) -> dict:
    extractor: PdfExtractor = _ctx["extractor"]
    ocr: OcrEngine | None = _ctx["ocr"]

    img = extractor.render(page_number)
    filename = f"page_{page_number:03d}.{_ctx['fmt']}"
    extractor.save_page(img, _ctx["pages_dir"] / filename)

    # La capa de texto del PDF, cuando existe, es exacta y prácticamente
    # gratis; el OCR solo entra para páginas escaneadas.
    result = None if _ctx["force_ocr"] else extractor.text_layer(page_number)
    source = "pdf"
    if result is None:
        source = "ocr"
        result = (
            ocr.process_image(img)
            if ocr
            else {"text": "", "blocks": [], "wordCount": 0, "droppedWords": 0}
        )

    result["source"] = source
    result["pageNumber"] = page_number
    result["image"] = str(Path("pages") / filename)
    return result


def process_pdf(pdf_path: Path, config: ProcessorConfig) -> Path:
    manual_id = slugify(pdf_path.stem)
    output_base = config.output_dir / manual_id
    manifest_path = output_base / "manifest.json"

    if manifest_path.exists() and not config.force:
        print(f"⏭️  {manual_id}: ya procesado, se omite (usa --force para rehacerlo)")
        return None

    pages_dir = output_base / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    use_ocr = True
    try:
        OcrEngine(lang=config.lang).check()
    except RuntimeError as e:
        print(f"⚠️  {e}", file=sys.stderr)
        print("Continuando solo con extracción de imágenes (sin OCR)...", file=sys.stderr)
        use_ocr = False

    probe = PdfExtractor(pdf_path)
    total = len(probe)
    probe.close()

    builder = ManifestBuilder(manual_id, pdf_path.stem, pdf_path, config.lang)
    init_args = (pdf_path, pages_dir, config, use_ocr)

    with ProcessPoolExecutor(
        max_workers=config.workers, initializer=_init_worker, initargs=init_args
    ) as pool:
        results = list(
            tqdm(
                pool.map(_process_page, range(1, total + 1), chunksize=1),
                total=total,
                desc=f"Procesando {manual_id}",
            )
        )

    dropped = 0
    from_pdf = sum(1 for r in results if r.get("source") == "pdf")
    for r in sorted(results, key=lambda r: r["pageNumber"]):
        dropped += r.pop("droppedWords", 0)
        r.pop("source", None)
        builder.add_page(
            page_number=r["pageNumber"],
            image=r["image"],
            text=r["text"],
            blocks=r["blocks"],
            word_count=r["wordCount"],
        )

    print(f"   texto: {from_pdf} pág. de la capa del PDF, {total - from_pdf} por OCR")
    if dropped:
        print(f"   {dropped} palabras descartadas por confianza < {config.min_conf}")

    return builder.save(manifest_path)


def write_index(output_dir: Path) -> list[dict]:
    """Índice que la PWA lee para listar los manuales disponibles.

    Se reconstruye desde los manifiestos presentes en la carpeta, así que
    refleja también los manuales que esta corrida omitió por ya existir.
    """
    index = []
    for manifest_path in sorted(output_dir.glob("*/manifest.json")):
        with open(manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        index.append(
            {
                "id": m["id"],
                "title": m["title"],
                "pageCount": m["pageCount"],
                "language": m["language"],
                "processedAt": m["processedAt"],
                "coverPage": 1,
            }
        )
    with open(output_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index


def main():
    parser = argparse.ArgumentParser(description="Procesador de manuales V-Strom 250 SX")
    parser.add_argument("--input", default="input", help="Carpeta con PDFs")
    parser.add_argument("--output", default="output", help="Carpeta de salida")
    parser.add_argument("--dpi", type=int, default=200, help="DPI para renderizar páginas")
    parser.add_argument("--quality", type=int, default=85, help="Calidad WebP/JPEG")
    parser.add_argument("--lang", default="spa+eng", help="Idiomas OCR (ej: spa+eng)")
    parser.add_argument("--fmt", default="webp", choices=["webp", "jpeg", "png"], help="Formato de imagen")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Páginas en paralelo")
    parser.add_argument("--min-conf", type=int, default=30, help="Confianza mínima de OCR (0 conserva todo)")
    parser.add_argument("--psm", type=int, default=None, help="Page segmentation mode de Tesseract")
    parser.add_argument("--force", action="store_true", help="Reprocesar manuales ya generados")
    parser.add_argument("--force-ocr", action="store_true", help="Ignorar la capa de texto del PDF y usar solo OCR")
    args = parser.parse_args()

    config = ProcessorConfig(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        dpi=args.dpi,
        quality=args.quality,
        lang=args.lang,
        fmt=args.fmt,
        workers=args.workers,
        min_conf=args.min_conf,
        psm=args.psm,
        force=args.force,
        force_ocr=args.force_ocr,
    )

    if not config.input_dir.exists():
        print(f"Carpeta de entrada no existe: {config.input_dir}", file=sys.stderr)
        sys.exit(1)

    pdfs = find_pdfs(config.input_dir)
    if not pdfs:
        print(f"No se encontraron PDFs en {config.input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"PDFs encontrados: {len(pdfs)} · {config.workers} procesos en paralelo")
    for pdf in pdfs:
        manifest = process_pdf(pdf, config)
        if manifest:
            print(f"✅ Guardado: {manifest}")

    index = write_index(config.output_dir)
    print(f"📑 Índice con {len(index)} manuales: {config.output_dir / 'index.json'}")


if __name__ == "__main__":
    main()
