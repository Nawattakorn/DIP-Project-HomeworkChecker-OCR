"""
ocr.py  —  OCR ด้วย Tesseract (อ่านคำศัพท์ภาษาอังกฤษ + ตัวเลข)
=============================================================
"""

import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ═══ Preprocessing ════════════════════════════════════════════════════════════
def _preprocess_full(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bw = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bw_raw = cv2.medianBlur(bw, 3)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    bw_clean = np.zeros_like(bw)
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] >= 300:
            bw_clean[labels == i] = 255
    return bw_clean, bw_raw

def _find_boxes(bw_clean, img_shape):
    h_img, w_img = img_shape[:2]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7,7))
    closed = cv2.morphologyEx(bw_clean, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        area   = w*h
        aspect = w/h if h else 0
        if area < (w_img*h_img)*0.005: continue
        if y < h_img*0.10:             continue
        # ปรับ Aspect Ratio เพื่อรองรับกล่องคำศัพท์ยาวๆ
        if not (1.0 <= aspect <= 15):  continue
        boxes.append((y,x,w,h))
    boxes.sort(key=lambda b: b[0])
    return boxes

# ═══ Public API ═══════════════════════════════════════════════════════════════
def extract_answers(image_path: str) -> list:
    img = cv2.imread(image_path)
    if img is None: raise ValueError(f"Cannot read: {image_path}")
    bw_clean, bw_raw = _preprocess_full(img)
    boxes = _find_boxes(bw_clean, img.shape)
    h_img, w_img = img.shape[:2]
    
    answers = []
    #  ใช้ psm 7 และไม่ล็อค whitelist เพื่อให้อ่านภาษาอังกฤษได้เต็มที่
    custom_config = r'--oem 3 --psm 7'
    
    for (y,x,w,h) in boxes:
        px, py = max(int(w * 0.05), 2), max(int(h * 0.15), 2)
        x1, y1 = max(x+px, 0), max(y+py, 0)
        x2, y2 = min(x+w-px, w_img), min(y+h-py, h_img)
        
        roi_color = img[y1:y2, x1:x2]
        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        roi_resized = cv2.resize(roi_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, roi_tess = cv2.threshold(roi_resized, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        roi_tess = cv2.copyMakeBorder(roi_tess, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        
        text = pytesseract.image_to_string(roi_tess, config=custom_config)
        # คัดกรองเอาเฉพาะตัวอักษรภาษาอังกฤษและตัวเลข (เอาสัญลักษณ์ขยะออก) 
        word = "".join(char for char in text if char.isalnum())
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
    custom_config = r'--oem 3 --psm 7'
    
    for idx, (y,x,w,h) in enumerate(boxes):
        px, py = max(int(w * 0.05), 2), max(int(h * 0.15), 2)
        x1, y1 = max(x+px, 0), max(y+py, 0)
        x2, y2 = min(x+w-px, w_img), min(y+h-py, h_img)
        
        roi_color = img[y1:y2,x1:x2]
        
        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        roi_resized = cv2.resize(roi_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, roi_tess = cv2.threshold(roi_resized, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        roi_tess = cv2.copyMakeBorder(roi_tess, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        
        text = pytesseract.image_to_string(roi_tess, config=custom_config)
        word = "".join(char for char in text if char.isalnum())
        
        answers.append(word)
        roi_debug.append({
            "idx": idx+1, "ocr": word, "b64_color": to_b64(roi_color),
            "b64_bw": to_b64(roi_tess), "chars": [] 
        })
        
    pipeline.append({"title": "6. Tesseract OCR Recognition", "rois": roi_debug})
    return answers, pipeline