import os
import re
import time
import random
import base64
import subprocess
import socket
from pathlib import Path

from config import cfg, DOWNLOADS_DIR

PAUSE = lambda: random.uniform(1.5, 3.0)
PAUSE_SHORT = lambda: random.uniform(0.5, 1.0)
PAUSE_LONG = lambda: random.uniform(3.0, 5.0)

BRAVE_EXE = cfg.BRAVE_PATH


def _clean_prompt(raw):
    text = raw.strip()
    text = re.sub(r'^["\'*]+\s*', '', text)
    text = re.sub(r'\s*["\'*]+$', '', text)
    if "1:1" not in text and "square" not in text.lower():
        text = text + " Square 1:1 aspect ratio."
    return text.strip()


def _set_input_via_js(page, text):
    return page.evaluate("""(t) => {
        const el = document.querySelector('#prompt-textarea');
        if (!el) return false;
        el.focus();
        el.innerHTML = '';
        el.textContent = t;
        el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
        return true;
    }""", text)


def _scan_images(page):
    return page.evaluate("""() => {
        const results = [];
        const seen = new Set();
        for (const img of document.querySelectorAll('img')) {
            const src = img.src || '';
            if (!src || src.startsWith('data:image/svg')) continue;
            if (src.startsWith('data:image/gif;base64,R0lGOD')) continue;
            const r = img.getBoundingClientRect();
            if (r.width * r.height < 5000) continue;
            if (seen.has(src)) continue;
            seen.add(src);
            results.push({ src, w: r.width, h: r.height });
        }
        results.sort((a, b) => (b.w * b.h) - (a.w * a.h));
        return results;
    }""")


def _wait_for_image(page, total_timeout=240):
    print("[chatgpt] Waiting for image generation (min 60s)...")
    start = time.time()
    while time.time() - start < 60:
        time.sleep(1)
    while time.time() - start < total_timeout:
        imgs = _scan_images(page)
        if imgs:
            print(f"[chatgpt] Image found ({time.time()-start:.0f}s) {imgs[0]['w']}x{imgs[0]['h']}")
            return imgs[0]["src"]
        time.sleep(2)
    return None


def _download_image(page, url, output_path):
    if url.startswith("data:"):
        try:
            data = base64.b64decode(url.split(",", 1)[1])
            Path(output_path).write_bytes(data)
            print(f"[image] Saved ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"[image] Failed: {e}")
            return False

    r = page.evaluate("""async (url) => {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;
            const blob = await resp.blob();
            return await new Promise(r => { const rd = new FileReader(); rd.onloadend = () => r(rd.result); rd.onerror = () => r(null); rd.readAsDataURL(blob); });
        } catch(e) { return null; }
    }""", url)
    if r and r.startswith("data:"):
        Path(output_path).write_bytes(base64.b64decode(r.split(",", 1)[1]))
        print(f"[image] Saved ({Path(output_path).stat().st_size} bytes)")
        return True

    r2 = page.evaluate("""(url) => {
        try {
            const img = document.querySelector('img[src="' + url + '"]');
            if (!img) return null;
            const c = document.createElement('canvas');
            c.width = img.naturalWidth || img.width;
            c.height = img.naturalHeight || img.height;
            c.getContext('2d').drawImage(img, 0, 0);
            return c.toDataURL('image/png');
        } catch(e) { return null; }
    }""", url)
    if r2 and r2.startswith("data:"):
        Path(output_path).write_bytes(base64.b64decode(r2.split(",", 1)[1]))
        print(f"[image] Saved via canvas ({Path(output_path).stat().st_size} bytes)")
        return True

    print("[image] Failed")
    return False


def _add_watermark(image_path):
    from PIL import Image, ImageDraw, ImageFont

    for fp in ["arial.ttf", "segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"]:
        try:
            font = ImageFont.truetype(fp, 12)
            break
        except Exception:
            font = None
    if font is None:
        font = ImageFont.load_default()

    img = Image.open(image_path).convert("RGBA")

    draw = ImageDraw.Draw(img)

    text = "AI generated"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    txt = Image.new("RGBA", (tw + 6, th + 6), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((3, 3), text, fill=(255, 255, 255, 255), font=font)
    txt = txt.rotate(90, expand=True)

    tx, ty = img.width - txt.width - 1, (img.height - txt.height) // 2
    for dy in range(txt.height):
        for dx in range(txt.width):
            r, g, b, a = txt.getpixel((dx, dy))
            if a == 0:
                continue
            pr, pg, pb, pa = img.getpixel((tx + dx, ty + dy))
            fade = a * 50 // 255
            nr = pr + (r - pr) * fade // 255
            ng = pg + (g - pg) * fade // 255
            nb = pb + (b - pb) * fade // 255
            img.putpixel((tx + dx, ty + dy), (nr, ng, nb, 255))

    img.convert("RGB").save(image_path, quality=98)
    print(f"[watermark] Applied to {image_path}")


def _add_logo(image_path, logo_path, corner="br"):
    from PIL import Image
    if not logo_path or not os.path.exists(logo_path):
        return
    img = Image.open(image_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    logo_w = int(img.width * 0.08)
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    pad = 12
    corners = {
        "br": (img.width - logo_w - pad, img.height - logo_h - pad),
        "bl": (pad, img.height - logo_h - pad),
        "tr": (img.width - logo_w - pad, pad),
        "tl": (pad, pad),
    }
    x, y = corners.get(corner, corners["br"])

    if logo.mode == "RGBA":
        img.paste(logo, (x, y), logo)
    else:
        img.paste(logo, (x, y))

    img.convert("RGB").save(image_path, quality=98)
    print(f"[logo] Applied to {image_path}")


def _find_input(page):
    for sel in ["#prompt-textarea", "textarea[placeholder*='Message ChatGPT']", "textarea[placeholder*='Message']", "div[contenteditable='true']"]:
        el = page.query_selector(sel)
        if el and el.is_visible():
            return el, sel
    return None, None


def generate_image(prompt, output_path, logo_path=None, logo_corner="br"):
    from playwright.sync_api import sync_playwright

    prompt = _clean_prompt(prompt)
    print(f"[image] Cleaned prompt ({len(prompt)} chars)")

    if not os.path.exists(BRAVE_EXE):
        raise FileNotFoundError(f"Brave not found at: {BRAVE_EXE}")

    print("[brave] Closing existing Brave instances...")
    subprocess.run(["taskkill", "/F", "/IM", "brave.exe"],
                   capture_output=True, timeout=10)
    time.sleep(3)

    port = 9222
    brave_proc = subprocess.Popen([
        BRAVE_EXE, f"--remote-debugging-port={port}",
        "--no-first-run", "--no-default-browser-check",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for i in range(20):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                s.close()
                break
            s.close()
        except Exception:
            pass
        time.sleep(1)

    print(f"[brave] CDP ready")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0] or browser.new_context()
        page = context.new_page()

        page.evaluate("window.location.href = 'https://chatgpt.com'")
        try:
            page.wait_for_selector("#prompt-textarea", timeout=120000)
        except Exception:
            pass
        time.sleep(3)

        input_el, input_sel = _find_input(page)
        if not input_el:
            print("")
            print("  LOGIN REQUIRED — Log into ChatGPT in the Brave window")
            print("")
            while True:
                time.sleep(2)
                try:
                    input_el, input_sel = _find_input(page)
                    if input_el:
                        print("[chatgpt] Logged in!")
                        break
                except Exception:
                    pass

        if not input_el:
            raise Exception("Could not find ChatGPT input")

        print("[chatgpt] Setting prompt via JS...")
        _set_input_via_js(page, prompt)
        time.sleep(PAUSE())

        print("[chatgpt] Submitting...")
        page.keyboard.press("Enter")

        img_url = _wait_for_image(page)
        if img_url and _download_image(page, img_url, output_path):
            _add_watermark(output_path)
            _add_logo(output_path, logo_path, logo_corner)
            if brave_proc:
                try:
                    brave_proc.terminate()
                    brave_proc.wait(timeout=5)
                except Exception:
                    try:
                        brave_proc.kill()
                    except Exception:
                        pass
            return output_path

        raise Exception("Could not extract image")


if __name__ == "__main__":
    tp = (
        "A clean, minimalist top-down shot of a wooden desk. "
        "An open laptop showing a simple line chart trending upward. "
        "A coffee cup next to it. Natural lighting. "
        "Text overlay bold serif at top: 'YOUR PROCESS IS BROKEN.' "
        "Beige/navy palette. 1:1 square."
    )
    out = os.path.join(str(DOWNLOADS_DIR), "test_generated.png")
    try:
        result = generate_image(tp, out)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
