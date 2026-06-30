from pathlib import Path
import unittest

from PIL import Image

from main1 import YearbookOptions, a4_canvas, box_blur_manual, build_yearbook, resize_manual


class YearbookTests(unittest.TestCase):
    def test_resize_manual_returns_expected_size(self) -> None:
        image = Image.new("RGB", (20, 20), "red")
        resized = resize_manual(image, 40, 10)
        self.assertEqual(resized.size, (40, 10))

    def test_box_blur_keeps_same_size(self) -> None:
        image = Image.new("RGB", (10, 10), "blue")
        blurred = box_blur_manual(image, radius=2)
        self.assertEqual(blurred.size, image.size)

    def test_a4_canvas_sizes(self) -> None:
        self.assertEqual(a4_canvas("paysage"), (3508, 2480))
        self.assertEqual(a4_canvas("portrait"), (2480, 3508))

    def test_build_yearbook_creates_cover_and_student_page(self) -> None:
        root = Path(__file__).resolve().parent
        options = YearbookOptions(
            title="Bachelor 1 - SUPINFO",
            orientation="paysage",
            show_quotes=True,
            color_mode="couleur",
            output_pdf=root / "out.pdf",
            csv_path=root / "etudiants.csv",
            photos_dir=root / "data - Copy" / "data" / "images",
            quotes_dir=root / "data - Copy" / "data" / "citations",
            class_photo_path=root / "data - Copy" / "data" / "photoClasse.png",
            logo_path=root / "ressources" / "ressources" / "SUPINFO_LOGO_QUADRI.png",
        )

        pages = build_yearbook(options)
        self.assertGreaterEqual(len(pages), 3)


if __name__ == "__main__":
    unittest.main()
