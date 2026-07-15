"""
Preview Composer — Tool (bukan agent).
Download foto produk dari URL, susun jadi 1 gambar kolase.
Murni image processing, tanpa reasoning.
"""

import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os


def download_image(url: str, timeout: int = 5) -> Image.Image | None:
    """Download gambar dari URL, return PIL Image."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"Gagal download: {url} — {e}")
        return None


def create_outfit_collage(products: list[dict], output_path: str = "reports/outfit_preview.png") -> str:
    """
    Buat kolase foto outfit dari list produk.

    Parameters:
        products: list dict dengan key 'gambar' (URL) dan 'nama'
        output_path: path untuk save hasil kolase

    Returns:
        Path ke file gambar yang disimpan
    """
    # Filter produk yang punya gambar
    valid_products = [p for p in products if p.get("gambar") and "error" not in p]

    if not valid_products:
        return ""

    # Settings
    thumb_size = (250, 250)
    padding = 20
    cols = min(len(valid_products), 4)
    rows = (len(valid_products) + cols - 1) // cols

    canvas_w = cols * (thumb_size[0] + padding) + padding
    canvas_h = rows * (thumb_size[1] + padding + 30) + padding  # +30 untuk label

    # Buat canvas
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Coba load font, fallback ke default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (IOError, OSError):
        font = ImageFont.load_default()

    for i, product in enumerate(valid_products):
        col = i % cols
        row = i // cols

        x = padding + col * (thumb_size[0] + padding)
        y = padding + row * (thumb_size[1] + padding + 30)

        # Download dan resize gambar
        img = download_image(product["gambar"])
        if img:
            img.thumbnail(thumb_size, Image.Resampling.LANCZOS)

            # Center gambar dalam thumbnail area
            offset_x = x + (thumb_size[0] - img.width) // 2
            offset_y = y + (thumb_size[1] - img.height) // 2

            canvas.paste(img, (offset_x, offset_y), img if img.mode == "RGBA" else None)
        else:
            # Placeholder kalau gagal download
            draw.rectangle([x, y, x + thumb_size[0], y + thumb_size[1]], fill=(230, 230, 230))
            draw.text((x + 10, y + thumb_size[1] // 2), "No image", fill=(150, 150, 150), font=font)

        # Label nama produk (truncate kalau kepanjangan)
        nama = product.get("nama", "Unknown")
        if len(nama) > 35:
            nama = nama[:32] + "..."
        label_y = y + thumb_size[1] + 5
        draw.text((x, label_y), nama, fill=(50, 50, 50), font=font)

    # Simpan
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas_rgb = canvas.convert("RGB")
    canvas_rgb.save(output_path, "PNG")
    return output_path


def preview_composer_node(state: dict) -> dict:
    """Node wrapper untuk Preview Composer."""
    products = state.get("product_results", [])
    path = create_outfit_collage(products)
    return {"preview_image_path": path}
