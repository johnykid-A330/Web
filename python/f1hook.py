import requests
import cv2
import pytesseract
import numpy as np
import os
import re
import sys

# === KONFIGURACE ===
WEBHOOK_URL = "https://discord.com/api/webhooks/1459845337597608048/txV_pv-TeHdzLrR7f_P7LTOy489HhcubX-9VAhSmVNGxDSsQd2ka-8dRe1z5ynoOK99l"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def parse_line_improved(line):
    """Rozdělí řádek na Driver (2 slova), Team (zbytek před čísly) a časy."""
    line = re.sub(r'[|@_~—;]', '', line).strip()
    times = re.findall(r'\d:\d{2}\.\d{3}|\+\d{1,2}\.\d{3}', line)
    if not times:
        return None

    best_time = times[0]
    gap = times[1] if len(times) > 1 else "---"
    prefix = line.split(best_time)[0].strip()
    words = prefix.split()

    if len(words) >= 2:
        driver = f"{words[0]} {words[1]}"
        remaining_parts = words[2:]
        team_parts = [part for part in remaining_parts if not part.isdigit()]
        team = " ".join(team_parts) if team_parts else "---"
        return [driver, team, best_time, gap]
    return None

def process_ocr_to_fancy_table(image_path):
    if not os.path.exists(image_path):
        return f"Chyba: Soubor {image_path} nenalezen."

    img = cv2.imread(image_path)
    if img is None:
        return "Chyba: Nepodařilo se načíst obrázek (OpenCV)."

    # Vylepšení obrazu
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

    # OCR
    raw_text = pytesseract.image_to_string(thresh, config=r'--oem 3 --psm 6')

    # Nastavení šířek sloupců
    w_pos, w_driver, w_team, w_best, w_gap = 3, 20, 20, 10, 10
    sep = f"+{'-'*(w_pos+2)}+{'-'*(w_driver+2)}+{'-'*(w_team+2)}+{'-'*(w_best+2)}+{'-'*(w_gap+2)}+"
    header = f"| {'P':<{w_pos}} | {'DRIVER':<{w_driver}} | {'TEAM':<{w_team}} | {'BEST':<{w_best}} | {'GAP':<{w_gap}} |"

    table_rows = []
    current_pos = 1

    for line in raw_text.splitlines():
        parsed = parse_line_improved(line)
        if parsed:
            dr, tm, bt, gp = parsed
            row = f"| {current_pos:>{w_pos}} | {dr[:w_driver]:<{w_driver}} | {tm[:w_team]:<{w_team}} | {bt:<{w_best}} | {gp:<{w_gap}} |"
            table_rows.append(row)
            current_pos += 1
            if current_pos > 20: break

    if not table_rows:
        return "⚠️ Nepodařilo se rozpoznat data v tabulce."

    return f"```text\n🏎️ F1 RACE RESULTS\n{sep}\n{header}\n{sep}\n" + "\n".join(table_rows) + f"\n{sep}\n```"

if __name__ == "__main__":
    # PHP posílá cestu k souboru jako první argument
    soubor = sys.argv[1] if len(sys.argv) > 1 else "obrazek.png"

    print(f"Analyzuji: {soubor}")
    vysledek = process_ocr_to_fancy_table(soubor)

    # Odeslání na Discord
    payload = {"content": vysledek}
    r = requests.post(WEBHOOK_URL, json=payload)

    if r.status_code == 204:
        print("Úspěšně odesláno na Discord.")
    else:
        print(f"Chyba Webhooku: {r.status_code}")
