"""Run once to generate the PWA app icons (needs Pillow, already in requirements.txt)."""
from PIL import Image, ImageDraw, ImageFont


def make_icon(size, path):
    img = Image.new("RGB", (size, size), "#06070d")
    for i in range(size):
        t = i / size
        r = int(139 + (34 - 139) * t)
        g = int(92 + (211 - 92) * t)
        b = int(246 + (238 - 246) * t)
        ImageDraw.Draw(img).line([(0, i), (size, i)], fill=(r, g, b))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=size // 5, fill=255)
    bg = Image.new("RGB", (size, size), "#06070d")
    bg.paste(img, (0, 0), mask)

    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.5))
    except OSError:
        font = ImageFont.load_default()
    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), text, fill="white", font=font)

    bg.save(path)
    print("saved", path)


if __name__ == "__main__":
    make_icon(192, "app/static/img/icon-192.png")
    make_icon(512, "app/static/img/icon-512.png")
