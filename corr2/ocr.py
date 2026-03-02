"""
ocr.py  —  OCR ด้วย OpenCV Template Matching
=============================================================
ปรับปรุงจากวิธี corr2 ของอาจารย์ โดยเปลี่ยนมาใช้ cv2.matchTemplate
(Normalized Cross-Correlation) ซึ่งประมวลผลด้วย C++ Backend 
ทำให้โค้ดสั้นลง ทำงานเร็วขึ้น และมีความแม่นยำสูง
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TMPL_H, TMPL_W = 42, 24
DIGITS         = "0123456789"

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/calibri.ttf", "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
]

# ═══ 1. Template Creation (สร้างแม่แบบ 0-9) ═════════════════════════════════
def _make_template(char: str, font) -> np.ndarray:
    canvas = 128
    img = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(img)
    try: draw.text((canvas//2, canvas//2), char, font=font, fill=0, anchor="mm")
    except Exception: draw.text((40, 40), char, font=font, fill=0)
    arr = np.array(img)
    rows, cols = np.any(arr < 200, axis=1), np.any(arr < 200, axis=0)
    if not rows.any(): return np.zeros((TMPL_H, TMPL_W), dtype=np.float32)
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    crop = arr[r0:r1+1, c0:c1+1]
    resized = cv2.resize(crop, (TMPL_W, TMPL_H), interpolation=cv2.INTER_AREA)
    _, bw = cv2.threshold(resized, 127, 1, cv2.THRESH_BINARY_INV)
    return bw.astype(np.float32)

def create_templates():
    templates = {d: [] for d in DIGITS}
    loaded_fonts = []
    for fp in _FONT_CANDIDATES:
        try: loaded_fonts.append(ImageFont.truetype(fp, size=80))
        except Exception: continue
    
    if loaded_fonts:
        for font in loaded_fonts:
            for d in DIGITS:
                t = _make_template(d, font)
                if t.sum() > 0: templates[d].append(t)
    
    for d in DIGITS:
        if not templates[d]: templates[d].append(np.zeros((TMPL_H, TMPL_W), dtype=np.float32))
    return templates

_TEMPLATES = create_templates()

# ═══ 2. OpenCV Correlation Engine (แทนที่ corr2 เดิม) ═════════════════════
def match_score(img: np.ndarray, tmpl: np.ndarray) -> float:
    """คำนวณความเหมือนด้วย Normalized Cross-Correlation ของ OpenCV"""
    res = cv2.matchTemplate(img.astype(np.float32), tmpl.astype(np.float32), cv2.TM_CCOEFF_NORMED)
    return float(res[0][0])

def _recognize(char_img, templates):
    if char_img is None or char_img.size == 0: return "?", -2.0
    resized = cv2.resize(char_img, (TMPL_W, TMPL_H), interpolation=cv2.INTER_AREA)
    if resized.dtype != np.uint8: resized = (resized > 0).astype("uint8") * 255
    _, bw = cv2.threshold(resized, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bw = bw.astype(np.float32)

    digit_scores = {}
    for digit, tlist in templates.items():
        # ใช้ฟังก์ชันของ OpenCV ค้นหาคะแนนสูงสุด
        digit_scores[digit] = max(match_score(bw, tmpl) for tmpl in tlist)

    ranked = sorted(digit_scores.items(), key=lambda kv: -kv[1])
    best_label, best_score = ranked[0] if ranked else ("?", -2.0)
    second_label, second_score = ranked[1] if len(ranked) > 1 else ("?", -2.0)

    # แก้ปัญหา 2 คล้าย 3 (Heuristic เดิมที่ได้ผลดี)
    if best_label == "3" and second_label == "2" and (best_score - second_score) < 0.08:
        best_label = "2"
        
    return best_label, best_score

# ═══ 3. Image Preprocessing & Segmenting ══════════════════════════════════
def _preprocess_full(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bw = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bw_raw = cv2.medianBlur(bw, 3)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    bw_clean = np.zeros_like(bw)
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] >= 300: bw_clean[labels == i] = 255
    return bw_clean, bw_raw

def _find_boxes(bw_clean, img_shape):
    h_img, w_img = img_shape[:2]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7,7))
    closed = cv2.morphologyEx(bw_clean, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if w*h < (w_img*h_img)*0.005 or y < h_img*0.10 or not (1.2 <= w/h <= 12): continue
        boxes.append((y,x,w,h))
    boxes.sort(key=lambda b: b[0])
    return boxes

def _segment_chars(roi_bw, min_area=100):
    if roi_bw is None or roi_bw.size == 0: return []
    roi = roi_bw.copy()
    if roi.dtype != np.uint8: roi = (roi > 0).astype("uint8") * 255
    roi = cv2.medianBlur(roi, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, kernel, iterations=1)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(roi, connectivity=8)
    chars = []
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] < min_area: continue
        x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        chars.append((x, roi[y : y + h, x : x + w]))
    chars.sort(key=lambda c: c[0])
    return [c[1] for c in chars]

# ═══ 4. Public API ══════════════════════════════════════════════════════════
def extract_answers(image_path: str) -> list:
    img = cv2.imread(image_path)
    if img is None: raise ValueError(f"Cannot read: {image_path}")
    bw_clean, bw_raw = _preprocess_full(img)
    boxes = _find_boxes(bw_clean, img.shape)
    h_img, w_img = img.shape[:2]
    
    answers = []
    for (y,x,w,h) in boxes:
        px, py = max(int(w * 0.06), 2), max(int(h * 0.08), 2)
        x1, y1 = max(x+px, 0), max(y+py, 0)
        x2, y2 = min(x+w-px, w_img), min(y+h-py, h_img)
        
        roi_bw = bw_raw[y1:y2, x1:x2]
        chars = _segment_chars(roi_bw)
        
        word = ""
        for c in chars:
            label, score = _recognize(c, _TEMPLATES)
            if score >= 0.40:  # ลดเกณฑ์ลงนิดหน่อยให้จับเส้นบางๆ ได้ดีขึ้น
                word += label
        answers.append(word)
        
    return answers

def extract_answers_debug(image_path: str):
    import base64
    def to_b64(arr):
        if arr.dtype != np.uint8: arr = arr.astype(np.uint8)
        if len(arr.shape) == 2: arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        _, buf = cv2.imencode(".png", arr)
        return base64.b64encode(buf).decode()

    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bw_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bw_clean, bw_raw = _preprocess_full(img)
    boxes = _find_boxes(bw_clean, img.shape)
    h_img, w_img = img.shape[:2]

    box_vis = img.copy()
    for (y,x,w,h) in boxes: cv2.rectangle(box_vis, (x,y), (x+w,y+h), (0,220,100), 3)

    pipeline = [
        {"title": "1. Original", "b64": to_b64(img)},
        {"title": "2. Grayscale", "b64": to_b64(gray)},
        {"title": "3. Otsu Threshold + Invert", "b64": to_b64(bw_otsu)},
        {"title": "4. bwareaopen (ลบ noise)", "b64": to_b64(bw_clean)},
        {"title": f"5. Detected Boxes ({len(boxes)} กล่อง)", "b64": to_b64(box_vis)},
    ]

    answers, roi_debug = [], []
    for idx, (y,x,w,h) in enumerate(boxes):
        px, py = max(int(w * 0.06), 2), max(int(h * 0.08), 2)
        x1, y1 = max(x+px, 0), max(y+py, 0)
        x2, y2 = min(x+w-px, w_img), min(y+h-py, h_img)
        
        roi_color = img[y1:y2, x1:x2]
        roi_bw = bw_raw[y1:y2, x1:x2]
        chars = _segment_chars(roi_bw)
        
        char_debug, word = [], ""
        for char_img in chars:
            label, score = _recognize(char_img, _TEMPLATES)
            if score >= 0.40: word += label
            
            scale = 4
            char_disp = cv2.resize(char_img, (char_img.shape[1]*scale, char_img.shape[0]*scale), interpolation=cv2.INTER_NEAREST)
            tmpl_arr = (_TEMPLATES.get(label, [np.zeros((TMPL_H,TMPL_W))])[0] * 255).astype(np.uint8)
            tmpl_disp = cv2.resize(tmpl_arr, (TMPL_W*scale, TMPL_H*scale), interpolation=cv2.INTER_NEAREST)

            # หา top 3 scores
            all_scores = {}
            for d, tlist in _TEMPLATES.items():
                resized = cv2.resize(char_img, (TMPL_W, TMPL_H), interpolation=cv2.INTER_AREA)
                _, bwc = cv2.threshold(resized, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                all_scores[d] = max(match_score(bwc.astype(np.float32), t) for t in tlist)
            top3 = sorted(all_scores.items(), key=lambda kv: -kv[1])[:3]

            char_debug.append({
                "label": label, "score": round(score, 4), "top3": [(d, round(s,4)) for d,s in top3],
                "noise": score < 0.40, "b64_char": to_b64(char_disp), "b64_tmpl": to_b64(tmpl_disp)
            })
            
        answers.append(word)
        roi_debug.append({
            "idx": idx+1, "ocr": word, "b64_color": to_b64(roi_color),
            "b64_bw": to_b64(roi_bw), "chars": char_debug
        })
        
    pipeline.append({"title": "6. OpenCV MatchTemplate Recognition", "rois": roi_debug})
    return answers, pipeline