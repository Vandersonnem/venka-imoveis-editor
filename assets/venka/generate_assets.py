"""Reproduce Venka packaging assets from the included, unchanged brand sources.

Requires Python 3.10+ and Pillow. No AI generation, logo tracing or recolouring.
The isolated symbol keeps the source RGBA pixels and removes only unrelated text
and transparent-canvas speckles with an alpha-connected-component crop.
"""
from __future__ import annotations

import base64
from collections import Counter, deque
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
NAVY = "#101C2D"
GOLD = "#DCBC64"
SITE_GOLD = "#DABB65"
ORANGE = "#E48C34"
SIZES = (16, 32, 64, 128, 256, 512, 1024)


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(size, Image.Resampling.LANCZOS)
    return result


def centred(image: Image.Image, size: tuple[int, int], padding: float = 0.18) -> Image.Image:
    canvas = Image.new("RGBA", size, NAVY)
    mark = fit(image, (round(size[0] * (1 - 2 * padding)), round(size[1] * (1 - 2 * padding))))
    canvas.alpha_composite(mark, ((size[0] - mark.width) // 2, (size[1] - mark.height) // 2))
    return canvas


def isolated_symbol(source: Image.Image) -> Image.Image:
    bounds = (75, 370, 651, 890)
    crop = source.crop(bounds)
    width, height = crop.size
    alpha = crop.getchannel("A")
    candidates = bytearray(value >= 64 for value in alpha.tobytes())
    retained = Image.new("L", crop.size)
    output = retained.load()
    components = []
    for start in range(width * height):
        if not candidates[start]:
            continue
        queue = deque([start])
        candidates[start] = 0
        points = []
        while queue:
            current = queue.popleft()
            points.append(current)
            x, y = current % width, current // width
            neighbours = []
            if x:
                neighbours.append(current - 1)
            if x + 1 < width:
                neighbours.append(current + 1)
            if y:
                neighbours.append(current - width)
            if y + 1 < height:
                neighbours.append(current + width)
            for neighbour in neighbours:
                if candidates[neighbour]:
                    candidates[neighbour] = 0
                    queue.append(neighbour)
        xs = [point % width for point in points]
        ys = [point // width for point in points]
        box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        # One large orange outline plus the four detached house windows.
        keep = len(points) > 20000 or (len(points) > 500 and box[2] < 400)
        if keep:
            for point in points:
                output[point % width, point // width] = 255
        if len(points) > 100:
            components.append({"pixels": len(points), "box": box, "retained": keep})
    # Include the unchanged antialiasing border around the selected pieces.
    retained = retained.filter(ImageFilter.MaxFilter(5))
    # The original horizontal wordmark approaches the V's diagonal. A crop along
    # the outside-right edge removes the adjacent letter's isolated fragment;
    # it does not trace, repaint or change any of the retained RGB pixels.
    crop_mask = retained.load()
    for y in range(height):
        source_y = bounds[1] + y
        right_edge = round(649 - (source_y - 378) * (255 / 505)) + 3 - bounds[0]
        for x in range(max(0, right_edge + 1), width):
            crop_mask[x, y] = 0
    crop.putalpha(ImageChops.multiply(alpha, retained))
    crop.putdata([pixel if pixel[3] else (0, 0, 0, 0) for pixel in crop.getdata()])
    symbol = crop.crop(crop.getbbox())
    (HERE / "symbol-crop.json").write_text(json.dumps({
        "source": "source/venka-logo-local-original.png",
        "source_crop": bounds,
        "alpha_threshold_for_component_detection": 64,
        "antialias_border_pixels": 2,
        "outside_right_diagonal_crop": "source x <= round(649 - (y - 378) * 255/505) + 3",
        "components": components,
        "source_rgb_values_changed": False,
    }, indent=2), encoding="utf-8")
    return symbol


def svg_icon(icon: Image.Image, radius: int) -> str:
    buffer = io.BytesIO()
    icon.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512">
  <title>Venka Imóveis Editor</title>
  <desc>Existing Venka symbol, original colours, on editorial navy. Raster source preserved in assets/venka/source.</desc>
  <defs><clipPath id="shape"><rect width="512" height="512" rx="{radius}"/></clipPath></defs>
  <image width="512" height="512" clip-path="url(#shape)" xlink:href="data:image/png;base64,{data}"/>
</svg>
'''


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    filename = "segoeuib.ttf" if bold else "segoeui.ttf"
    windows = Path("C:/Windows/Fonts") / filename
    if windows.exists():
        return ImageFont.truetype(str(windows), size)
    return ImageFont.load_default(size=size)


def splash(size: tuple[int, int], symbol: Image.Image, horizontal: Image.Image) -> Image.Image:
    width, height = size
    canvas = Image.new("RGB", size, NAVY)
    draw = ImageDraw.Draw(canvas)
    if height > width:
        mark = fit(symbol, (round(width * .46), round(height * .30)))
        y = round(height * .29)
        canvas.paste(mark, ((width - mark.width) // 2, y), mark)
        title_y = y + mark.height + round(height * .045)
        title_size = round(width * .055)
    else:
        mark = fit(horizontal, (round(width * .48), round(height * .28)))
        y = round(height * .30)
        canvas.paste(mark, ((width - mark.width) // 2, y), mark)
        title_y = y + mark.height + round(height * .06)
        title_size = round(width * .027)
    draw.text((width // 2, title_y), "Venka Imóveis Editor", font=font(title_size, True), fill=GOLD, anchor="mt")
    draw.text((width // 2, title_y + title_size * 1.7), "Zona Sul · Rio de Janeiro", font=font(round(title_size * .48)), fill="#D6DAE0", anchor="mt")
    return canvas


def ios_icons(icon: Image.Image) -> None:
    catalog = HERE / "ios" / "Assets.xcassets"
    folder = catalog / "AppIcon.appiconset"
    folder.mkdir(parents=True, exist_ok=True)
    (catalog / "Contents.json").write_text(json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2), encoding="utf-8")
    entries = []
    for idiom, points, scales in (
        ("iphone", (20, 29, 40, 60), (2, 3)),
        ("ipad", (20, 29, 40, 76), (1, 2)),
        ("ipad", (83.5,), (2,)),
        ("ios-marketing", (1024,), (1,)),
    ):
        for point in points:
            for scale in scales:
                size = round(point * scale)
                filename = f"icon-{point:g}@{scale}x.png"
                icon.resize((size, size), Image.Resampling.LANCZOS).convert("RGB").save(folder / filename)
                entries.append({"filename": filename, "idiom": idiom, "scale": f"{scale}x", "size": f"{point:g}x{point:g}"})
    (folder / "Contents.json").write_text(json.dumps({"images": entries, "info": {"author": "xcode", "version": 1}}, indent=2), encoding="utf-8")


def main() -> None:
    source = Image.open(HERE / "source" / "venka-logo-local-original.png").convert("RGBA")
    stacked = Image.open(HERE / "source" / "logoTopo.webp").convert("RGBA")
    # Crop only the known main-content rectangle; keep the exact source pixels.
    horizontal = source.crop((81, 375, 1962, 886))
    horizontal.save(HERE / "venka-logo-horizontal.png")
    stacked.save(HERE / "venka-logo-stacked.png")
    symbol = isolated_symbol(source)
    symbol.save(HERE / "venka-symbol.png")
    icon = centred(symbol, (1024, 1024), padding=.19).convert("RGB")
    for size in SIZES:
        rendered = icon.resize((size, size), Image.Resampling.LANCZOS)
        rendered.save(HERE / f"venka-icon-{size}.png")
        if size <= 512:
            rendered.save(ROOT / "assets" / "icons" / f"concat_logo_{size}.png")
    icon.save(ROOT / "assets" / "icons" / "concat.ico", format="ICO", sizes=[(size, size) for size in SIZES if size <= 256])
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(ROOT / "assets" / "concat_logo_512.png")
    for filename in ("concat-mark.png", "concat-mark-dark.png"):
        icon.resize((512, 512), Image.Resampling.LANCZOS).save(ROOT / "assets" / filename)
    for filename in ("new_concat_logo_512_rounded_light_theme.svg", "new_concat_logo_512_dark_theme_rounded.svg"):
        (ROOT / "assets" / filename).write_text(svg_icon(icon.resize((512, 512), Image.Resampling.LANCZOS), 95), encoding="utf-8")
    for filename in ("new_concat_logo_512_square_light_theme.svg", "new_concat_logo_512_square_dark_theme.svg"):
        (ROOT / "assets" / filename).write_text(svg_icon(icon.resize((512, 512), Image.Resampling.LANCZOS), 0), encoding="utf-8")
    (HERE / "venka-icon.svg").write_text(svg_icon(icon.resize((512, 512), Image.Resampling.LANCZOS), 0), encoding="utf-8")
    for density, size in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
        icon.resize((size, size), Image.Resampling.LANCZOS).save(ROOT / "src" / "crates" / "concat-android" / "res" / f"mipmap-{density}" / "ic_launcher.png")
    android_drawable = ROOT / "src" / "crates" / "concat-android" / "res" / "drawable-nodpi"
    android_drawable.mkdir(parents=True, exist_ok=True)
    fit(horizontal, (960, 260)).save(android_drawable / "venka_launch_logo.png")
    android_symbol = Image.new("RGBA", (432, 432))
    small_symbol = fit(symbol, (260, 260))
    android_symbol.alpha_composite(small_symbol, ((432 - small_symbol.width) // 2, (432 - small_symbol.height) // 2))
    android_symbol.save(android_drawable / "venka_splash_symbol.png")
    splash((1080, 1920), symbol, horizontal).save(HERE / "venka-splash-portrait.png")
    splash((1920, 1080), symbol, horizontal).save(HERE / "venka-splash-landscape.png")
    ios_icons(icon)
    (HERE / "ios").mkdir(exist_ok=True)
    fit(horizontal, (960, 260)).save(HERE / "ios" / "VenkaLaunchLogo.png")
    # Contact sheet makes the actual 16/32/64px payload visible for inspection.
    preview = Image.new("RGB", (1400, 1000), "#EBEDF0")
    draw = ImageDraw.Draw(preview)
    draw.text((34, 24), "VENKA · ativos de identidade e ícones", font=font(30, True), fill=NAVY)
    draw.text((34, 68), "Logo original preservado | navy editorial #101C2D | dourado #DCBC64", font=font(20), fill=NAVY)
    for index, size in enumerate((16, 32, 48, 64, 128, 256)):
        mark = icon.resize((size, size), Image.Resampling.LANCZOS)
        x = 34 + index * 220
        preview.paste(mark, (x, 135))
        draw.text((x, 410), f"{size} × {size}", font=font(20), fill=NAVY)
    preview.paste(icon.resize((350, 350), Image.Resampling.LANCZOS), (34, 500))
    preview.paste(splash((270, 480), symbol, horizontal), (420, 475))
    preview.paste(splash((640, 360), symbol, horizontal), (725, 500))
    preview.save(HERE / "branding-preview.png")
    records = []
    covered = list(HERE.rglob("*"))
    covered.extend((ROOT / "assets" / "icons").glob("*"))
    covered.extend(ROOT / "assets" / filename for filename in (
        "concat_logo_512.png", "concat-mark.png", "concat-mark-dark.png",
        "new_concat_logo_512_rounded_light_theme.svg", "new_concat_logo_512_dark_theme_rounded.svg",
        "new_concat_logo_512_square_light_theme.svg", "new_concat_logo_512_square_dark_theme.svg",
    ))
    covered.extend((ROOT / "src" / "crates" / "concat-android" / "res").rglob("*"))
    for path in sorted(set(covered)):
        if path.is_file() and path.name not in ("asset-manifest.json",):
            record = {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            if path.suffix.lower() in (".png", ".webp", ".ico"):
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    record.update(size=list(image.size), mode=image.mode)
                    if path.suffix.lower() == ".ico":
                        record["ico_sizes"] = sorted(list(size) for size in image.ico.sizes())
            elif path.suffix.lower() in (".svg", ".xml", ".storyboard"):
                ET.parse(path)
                record["xml_parse"] = "passed"
            records.append(record)
    (HERE / "asset-manifest.json").write_text(json.dumps({
        "name": "Venka Imóveis Editor",
        "palette": {"navy_editorial": NAVY, "gold_ui": GOLD, "gold_public_site": SITE_GOLD, "orange_logo_approximate": ORANGE},
        "recoloured_logo": False,
        "files": records,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"files": len(records), "icon": list(icon.size), "symbol": list(symbol.size), "horizontal": list(horizontal.size), "verified": True}))


if __name__ == "__main__":
    main()
