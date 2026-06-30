from __future__ import annotations

import argparse
import csv
import math
import os
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


BLUE = (0, 81, 147)
LIGHT_BLUE = (228, 238, 248)
GOLD = (226, 182, 62)
SILVER = (170, 176, 184)
TEXT = (25, 38, 51)
WHITE = (255, 255, 255)


@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    role: int
    blur: bool
    photo_path: Path
    quote: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class YearbookOptions:
    title: str
    orientation: str
    show_quotes: bool
    color_mode: str
    output_pdf: Path
    csv_path: Path
    photos_dir: Path
    quotes_dir: Path | None
    class_photo_path: Path
    logo_path: Path


def parse_args() -> YearbookOptions:
    root = Path(__file__).resolve().parent
    default_data_root = root / "data - Copy" / "data"
    parser = argparse.ArgumentParser(description="Generateur de yearbook SUPINFO")
    parser.add_argument(
        "--title",
        default="Bachelor 1 - SUPINFO Tours - 2025-2026",
        help="Titre affiche sur la page de garde.",
    )
    parser.add_argument(
        "--orientation",
        choices=("portrait", "paysage"),
        default="paysage",
        help="Format du yearbook.",
    )
    parser.add_argument(
        "--quotes",
        choices=("oui", "non"),
        default="oui",
        help="Afficher ou non les citations.",
    )
    parser.add_argument(
        "--color",
        choices=("couleur", "nb"),
        default="couleur",
        help="Mode de couleur des photos.",
    )
    parser.add_argument(
        "--csv",
        default=str(root / "etudiants.csv"),
        help="Chemin du fichier CSV des etudiants.",
    )
    parser.add_argument(
        "--photos-dir",
        default=str(default_data_root / "images"),
        help="Dossier contenant les photos individuelles.",
    )
    parser.add_argument(
        "--quotes-dir",
        default=str(default_data_root / "citations"),
        help="Dossier contenant les citations texte.",
    )
    parser.add_argument(
        "--class-photo",
        default=str(default_data_root / "photoClasse.png"),
        help="Chemin de la photo de classe.",
    )
    parser.add_argument(
        "--logo",
        default=str(root / "ressources" / "ressources" / "SUPINFO_LOGO_QUADRI.png"),
        help="Chemin du logo de l'ecole.",
    )
    parser.add_argument(
        "--output",
        default=str(root / "yearbook_genere.pdf"),
        help="Chemin du PDF de sortie.",
    )
    args = parser.parse_args()
    return YearbookOptions(
        title=args.title,
        orientation=args.orientation,
        show_quotes=args.quotes == "oui",
        color_mode=args.color,
        output_pdf=Path(args.output),
        csv_path=Path(args.csv),
        photos_dir=Path(args.photos_dir),
        quotes_dir=Path(args.quotes_dir) if args.quotes_dir else None,
        class_photo_path=Path(args.class_photo),
        logo_path=Path(args.logo),
    )


def a4_canvas(orientation: str) -> tuple[int, int]:
    return (3508, 2480) if orientation == "paysage" else (2480, 3508)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def resize_nearest(image: Image.Image, width: int, height: int) -> Image.Image:
    source = image.convert("RGB")
    src_w, src_h = source.size
    result = Image.new("RGB", (width, height))
    for y in range(height):
        src_y = min(int(y * src_h / height), src_h - 1)
        for x in range(width):
            src_x = min(int(x * src_w / width), src_w - 1)
            result.putpixel((x, y), source.getpixel((src_x, src_y)))
    return result


def bilinear_sample(image: Image.Image, x: float, y: float) -> tuple[int, int, int]:
    src_w, src_h = image.size
    x0 = max(0, min(int(math.floor(x)), src_w - 1))
    y0 = max(0, min(int(math.floor(y)), src_h - 1))
    x1 = min(x0 + 1, src_w - 1)
    y1 = min(y0 + 1, src_h - 1)

    dx = x - x0
    dy = y - y0
    p00 = image.getpixel((x0, y0))
    p10 = image.getpixel((x1, y0))
    p01 = image.getpixel((x0, y1))
    p11 = image.getpixel((x1, y1))

    channels = []
    for i in range(3):
        top = p00[i] * (1 - dx) + p10[i] * dx
        bottom = p01[i] * (1 - dx) + p11[i] * dx
        value = top * (1 - dy) + bottom * dy
        channels.append(int(round(value)))
    return tuple(channels)


def resize_interpolated(image: Image.Image, width: int, height: int) -> Image.Image:
    source = image.convert("RGB")
    src_w, src_h = source.size
    result = Image.new("RGB", (width, height))
    scale_x = src_w / width
    scale_y = src_h / height
    for y in range(height):
        src_y = (y + 0.5) * scale_y - 0.5
        for x in range(width):
            src_x = (x + 0.5) * scale_x - 0.5
            result.putpixel((x, y), bilinear_sample(source, src_x, src_y))
    return result


def resize_manual(image: Image.Image, width: int, height: int) -> Image.Image:
    if width >= image.width and height >= image.height:
        return resize_nearest(image, width, height)
    return resize_interpolated(image, width, height)


def box_blur_manual(image: Image.Image, radius: int = 4) -> Image.Image:
    source = image.convert("RGB")
    width, height = source.size
    blurred = Image.new("RGB", (width, height))
    for y in range(height):
        for x in range(width):
            red = green = blue = count = 0
            for dy in range(-radius, radius + 1):
                py = y + dy
                if py < 0 or py >= height:
                    continue
                for dx in range(-radius, radius + 1):
                    px = x + dx
                    if px < 0 or px >= width:
                        continue
                    pixel = source.getpixel((px, py))
                    red += pixel[0]
                    green += pixel[1]
                    blue += pixel[2]
                    count += 1
            blurred.putpixel((x, y), (red // count, green // count, blue // count))
    return blurred


def fit_dimensions(src_w: int, src_h: int, max_w: int, max_h: int) -> tuple[int, int]:
    ratio = min(max_w / src_w, max_h / src_h)
    return max(1, int(src_w * ratio)), max(1, int(src_h * ratio))


def center_crop(image: Image.Image, width: int, height: int) -> Image.Image:
    src_w, src_h = image.size
    target_ratio = width / height
    source_ratio = src_w / src_h
    if source_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        box = (left, 0, left + new_w, src_h)
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        box = (0, top, src_w, top + new_h)
    return image.crop(box)


def discover_photo(photos_dir: Path, raw_id: str) -> Path:
    candidate = photos_dir / raw_id
    if candidate.exists():
        return candidate
    stem = Path(raw_id).stem.lower()
    for path in photos_dir.iterdir():
        if path.is_file() and path.stem.lower() == stem:
            return path
    for suffix in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"):
        candidate = photos_dir / f"{Path(raw_id).stem}{suffix}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Photo introuvable pour {raw_id}")


def read_quote(student_id: str, csv_row: dict[str, str], quotes_dir: Path | None) -> str:
    if quotes_dir:
        for suffix in (".txt", ""):
            path = quotes_dir / f"{student_id}{suffix}"
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
    return (csv_row.get("citation") or "").strip()


def normalize_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "vrai", "yes", "oui"}


def read_students(csv_path: Path, photos_dir: Path, quotes_dir: Path | None) -> list[Student]:
    students: list[Student] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            student_id = (
                row.get("id")
                or row.get("ID")
                or row.get("nom_fichier_photo")
                or row.get("photo")
                or ""
            ).strip()
            if not student_id:
                continue

            role_raw = (row.get("role") or row.get("delegue") or "0").strip()
            try:
                role = int(role_raw)
            except ValueError:
                role = 0

            photo_path = discover_photo(photos_dir, student_id)
            quote_id = Path(student_id).stem
            students.append(
                Student(
                    student_id=quote_id,
                    first_name=(row.get("prenom") or row.get("first_name") or "").strip(),
                    last_name=(row.get("nom") or row.get("last_name") or "").strip(),
                    role=role,
                    blur=normalize_bool(row.get("flouter") or row.get("blur")),
                    photo_path=photo_path,
                    quote=read_quote(quote_id, row, quotes_dir),
                )
            )
    return students


def draw_background(page: Image.Image) -> None:
    draw = ImageDraw.Draw(page)
    width, height = page.size
    draw.rectangle((0, 0, width, height), fill=WHITE)
    draw.rectangle((0, 0, width, int(height * 0.14)), fill=BLUE)
    draw.rectangle((0, int(height * 0.9), width, height), fill=LIGHT_BLUE)
    draw.line((80, int(height * 0.14), width - 80, int(height * 0.14)), fill=LIGHT_BLUE, width=6)


def draw_header_footer(page: Image.Image, title: str, page_number: int | None = None) -> None:
    draw = ImageDraw.Draw(page)
    width, height = page.size
    title_font = load_font(42, bold=True)
    footer_font = load_font(28)
    draw.text((90, 48), title, font=title_font, fill=WHITE)
    footer = "SUPINFO Yearbook"
    footer_box = draw.textbbox((0, 0), footer, font=footer_font)
    draw.text((90, height - 85), footer, font=footer_font, fill=TEXT)
    if page_number is not None:
        number = f"{page_number}"
        number_box = draw.textbbox((0, 0), number, font=footer_font)
        draw.text((width - 90 - (number_box[2] - number_box[0]), height - 85), number, font=footer_font, fill=TEXT)


def create_cover_page(options: YearbookOptions) -> Image.Image:
    width, height = a4_canvas(options.orientation)
    page = Image.new("RGB", (width, height), WHITE)
    draw_background(page)
    draw = ImageDraw.Draw(page)

    logo = Image.open(options.logo_path).convert("RGBA")
    logo_w, logo_h = fit_dimensions(logo.width, logo.height, int(width * 0.28), int(height * 0.22))
    logo = resize_manual(logo.convert("RGB"), logo_w, logo_h).convert("RGBA")
    page.paste(logo, ((width - logo_w) // 2, int(height * 0.23)), logo)

    title_font = load_font(88, bold=True)
    subtitle_font = load_font(46)
    title_lines = textwrap.wrap(options.title, width=28)
    y = int(height * 0.52)
    for line in title_lines:
        box = draw.textbbox((0, 0), line, font=title_font)
        draw.text(((width - (box[2] - box[0])) // 2, y), line, font=title_font, fill=TEXT)
        y += 100
    subtitle = "Promotion annuelle"
    box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(((width - (box[2] - box[0])) // 2, y + 20), subtitle, font=subtitle_font, fill=BLUE)
    return page


def create_class_photo_page(options: YearbookOptions, page_number: int) -> Image.Image:
    width, height = a4_canvas(options.orientation)
    page = Image.new("RGB", (width, height), WHITE)
    draw_background(page)
    draw_header_footer(page, options.title, page_number)
    draw = ImageDraw.Draw(page)
    photo = Image.open(options.class_photo_path).convert("RGB")
    if options.color_mode == "nb":
        photo = photo.convert("L").convert("RGB")
    target_w, target_h = fit_dimensions(photo.width, photo.height, width - 240, height - 620)
    photo = resize_manual(photo, target_w, target_h)
    x = (width - target_w) // 2
    y = 260
    draw.rounded_rectangle((x - 18, y - 18, x + target_w + 18, y + target_h + 18), radius=26, fill=WHITE, outline=LIGHT_BLUE, width=6)
    page.paste(photo, (x, y))

    caption_font = load_font(42, bold=True)
    caption = "Photo de classe"
    box = draw.textbbox((0, 0), caption, font=caption_font)
    draw.text(((width - (box[2] - box[0])) // 2, y + target_h + 40), caption, font=caption_font, fill=TEXT)
    return page


def grid_settings(orientation: str, show_quotes: bool) -> tuple[int, int]:
    if orientation == "paysage":
        return (2, 5) if show_quotes else (3, 5)
    return (3, 3) if show_quotes else (5, 3)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        box = draw.textbbox((0, 0), test, font=font)
        if box[2] - box[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break
    if len(lines) < max_lines:
        lines.append(current)
    remaining = words[len(" ".join(lines).split()):]
    if remaining:
        lines[-1] = lines[-1].rstrip(". ") + "..."
    return lines[:max_lines]


def prepare_photo(student: Student, width: int, height: int, color_mode: str) -> Image.Image:
    photo = Image.open(student.photo_path).convert("RGB")
    photo = center_crop(photo, width, height)
    photo = resize_manual(photo, width, height)
    if student.blur:
        photo = box_blur_manual(photo)
    if color_mode == "nb":
        photo = photo.convert("L").convert("RGB")
    return photo


def draw_badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, fill: tuple[int, int, int]) -> None:
    font = load_font(20, bold=True)
    draw.rounded_rectangle(box, radius=18, fill=fill)
    text_box = draw.textbbox((0, 0), label, font=font)
    x = box[0] + ((box[2] - box[0]) - (text_box[2] - text_box[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (text_box[3] - text_box[1])) // 2 - 2
    draw.text((x, y), label, font=font, fill=TEXT)


def create_student_pages(students: list[Student], options: YearbookOptions, start_page_number: int) -> list[Image.Image]:
    width, height = a4_canvas(options.orientation)
    rows, cols = grid_settings(options.orientation, options.show_quotes)
    per_page = rows * cols
    pages: list[Image.Image] = []
    page_number = start_page_number

    top_margin = 240
    bottom_margin = 150
    side_margin = 90
    gap_x = 55 if cols == 5 else 80
    gap_y = 42
    usable_w = width - 2 * side_margin - gap_x * (cols - 1)
    usable_h = height - top_margin - bottom_margin - gap_y * (rows - 1)
    cell_w = usable_w // cols
    cell_h = usable_h // rows
    photo_h = int(cell_h * (0.62 if options.show_quotes else 0.74))
    photo_w = int(cell_w * 0.88)

    for offset in range(0, len(students), per_page):
        page = Image.new("RGB", (width, height), WHITE)
        draw_background(page)
        draw_header_footer(page, options.title, page_number)
        draw = ImageDraw.Draw(page)

        for index, student in enumerate(students[offset : offset + per_page]):
            row = index // cols
            col = index % cols
            x0 = side_margin + col * (cell_w + gap_x)
            y0 = top_margin + row * (cell_h + gap_y)
            card_box = (x0, y0, x0 + cell_w, y0 + cell_h)
            draw.rounded_rectangle(card_box, radius=28, fill=(249, 251, 253), outline=(214, 224, 235), width=3)

            photo = prepare_photo(student, photo_w, photo_h, options.color_mode)
            photo_x = x0 + (cell_w - photo_w) // 2
            photo_y = y0 + 24
            page.paste(photo, (photo_x, photo_y))

            if student.role == 1:
                draw_badge(draw, (photo_x + 10, photo_y + 10, photo_x + 150, photo_y + 48), "DELEGUE", GOLD)
            elif student.role == 2:
                draw_badge(draw, (photo_x + 10, photo_y + 10, photo_x + 190, photo_y + 48), "SUPPLEANT", SILVER)

            name_font = load_font(28, bold=True)
            quote_font = load_font(20)
            name_box = draw.textbbox((0, 0), student.full_name, font=name_font)
            name_x = x0 + (cell_w - (name_box[2] - name_box[0])) // 2
            name_y = photo_y + photo_h + 18
            draw.text((name_x, name_y), student.full_name, font=name_font, fill=TEXT)

            if options.show_quotes:
                quote_text = student.quote.strip()
                if quote_text:
                    lines = wrap_text(draw, f'"{quote_text}"', quote_font, cell_w - 40, 4)
                    quote_y = name_y + 42
                    for line in lines:
                        line_box = draw.textbbox((0, 0), line, font=quote_font)
                        line_x = x0 + (cell_w - (line_box[2] - line_box[0])) // 2
                        draw.text((line_x, quote_y), line, font=quote_font, fill=BLUE)
                        quote_y += 28

        pages.append(page)
        page_number += 1
    return pages


def save_pdf(pages: Iterable[Image.Image], output_pdf: Path) -> None:
    images = [page.convert("RGB") for page in pages]
    if not images:
        raise ValueError("Aucune page a sauvegarder.")
    images[0].save(output_pdf, save_all=True, append_images=images[1:], resolution=300.0)


def build_yearbook(options: YearbookOptions) -> list[Image.Image]:
    students = read_students(options.csv_path, options.photos_dir, options.quotes_dir)
    cover = create_cover_page(options)
    class_page = create_class_photo_page(options, page_number=2)
    student_pages = create_student_pages(students, options, start_page_number=3)
    return [cover, class_page, *student_pages]


def validate_paths(options: YearbookOptions) -> None:
    required_paths = [
        options.csv_path,
        options.photos_dir,
        options.class_photo_path,
        options.logo_path,
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"Chemin introuvable : {path}")


def main() -> None:
    options = parse_args()
    validate_paths(options)
    pages = build_yearbook(options)
    save_pdf(pages, options.output_pdf)
    print(f"Yearbook genere : {options.output_pdf}")


if __name__ == "__main__":
    main()
