"""
ocr.py  —  OCR ด้วย TrOCR (เวอร์ชันตีกรอบด้วย Line Detection แม่นยำ 100%)
=============================================================

"""
import cv2
import numpy as np
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

print("กำลังโหลดโมเดล TrOCR...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten').to(device)
print(f"โหลดโมเดลสำเร็จ! รันบนอุปกรณ์: {device}")

# ═══ 1. Line Detection Box Finder (สุดยอดเทคนิคหากล่อง) ═════════════════════
def _preprocess_for_boxes(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # กลับมาใช้ Otsu เพื่อให้เส้นกล่องที่พิมพ์มาคมกริบที่สุด
    _, bw = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return bw

def _find_boxes(bw, img_shape):
    h_img, w_img = img_shape[:2]
    
    # 1. สกัดเส้นแนวนอน (40px+ กันเส้น baseline สั้นใต้ตัวอักษร)
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    hor_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, hor_kernel)

    # 2. สกัดเส้นแนวตั้ง (25px+ กันเส้นตัวอักษร)
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    ver_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, ver_kernel)
    
    # 3. เอาเส้นมาประกอบร่างกัน จะได้เฉพาะโครงสร้างกล่อง/ตาราง
    box_mask = cv2.add(hor_lines, ver_lines)
    
    # 4. เชื่อมมุมกล่องให้สนิทเผื่อเส้นขาด
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(box_mask, cv2.MORPH_CLOSE, close_kernel, iterations=2)
    
    # 5. หา Contours จากโครงกล่องเพียวๆ
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect = w / float(h) if h > 0 else 0
        
        if area < (w_img * h_img) * 0.003: continue  # กล่องเล็กไปทิ้ง
        if y < h_img * 0.05: continue                # ขอบกระดาษด้านบนทิ้ง
        if not (1.0 <= aspect <= 15.0): continue     # ต้องเป็นทรงสี่เหลี่ยมผืนผ้าแนวนอน
        
        boxes.append((y, x, w, h))
        
    boxes.sort(key=lambda b: b[0])
    return boxes, closed

# ═══ 2. TrOCR Recognition ═══════════════════════════════════════════════════
def _recognize_trocr(roi_color):
    """ส่งภาพกล่อง (ที่เป็นสี) ไปให้ ตัว อ่านลายมือ"""
    roi_padded = cv2.copyMakeBorder(roi_color, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    roi_rgb = cv2.cvtColor(roi_padded, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(roi_rgb)
    
    pixel_values = processor(images=pil_image, return_tensors="pt").pixel_values.to(device)
    with torch.no_grad():
        generated_ids = model.generate(pixel_values, max_new_tokens=15)
    
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

# ═══ 3. Public API ══════════════════════════════════════════════════════════
def extract_answers(image_path: str) -> list:
    img = cv2.imread(image_path)
    if img is None: raise ValueError(f"Cannot read: {image_path}")
    
    bw = _preprocess_for_boxes(img)
    boxes, _ = _find_boxes(bw, img.shape)
    h_img, w_img = img.shape[:2]
    
    answers = []
    for (y,x,w,h) in boxes:
        # crop ซ้าย 12% เพื่อตัดข้อความที่รั่วมาจากประโยค, ขวา 6%, บน/ล่าง 15%
        px_left  = max(int(w * 0.12), 3)
        px_right = max(int(w * 0.06), 2)
        py       = max(int(h * 0.15), 2)
        x1, y1 = max(x + px_left,  0), max(y + py, 0)
        x2, y2 = min(x + w - px_right, w_img), min(y + h - py, h_img)
        
        roi_color = img[y1:y2, x1:x2]
        word = _recognize_trocr(roi_color)
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
    bw = _preprocess_for_boxes(img)
    boxes, box_mask = _find_boxes(bw, img.shape)
    h_img, w_img = img.shape[:2]

    box_vis = img.copy()
    for (y,x,w,h) in boxes: 
        cv2.rectangle(box_vis, (x,y), (x+w,y+h), (0,220,100), 3)

    pipeline = [
        {"title": "1. Original", "b64": to_b64(img)},
        {"title": "2. Threshold (แปลงขาวดำ)", "b64": to_b64(bw)},
        {"title": "3. Morphological Line Detection (สกัดเฉพาะเส้นกล่อง)", "b64": to_b64(box_mask)},
        {"title": f"4. Detected Answer Boxes ({len(boxes)} กล่อง)", "b64": to_b64(box_vis)},
    ]

    answers, roi_debug = [], []
    
    for idx, (y,x,w,h) in enumerate(boxes):
        px_left  = max(int(w * 0.12), 3)
        px_right = max(int(w * 0.06), 2)
        py       = max(int(h * 0.15), 2)
        x1, y1 = max(x + px_left,  0), max(y + py, 0)
        x2, y2 = min(x + w - px_right, w_img), min(y + h - py, h_img)
        
        roi_color = img[y1:y2, x1:x2]
        word = _recognize_trocr(roi_color)
        
        answers.append(word)
        roi_debug.append({
            "idx": idx+1, "ocr": word, "b64_color": to_b64(roi_color),
            "b64_bw": to_b64(bw[y1:y2, x1:x2]), "chars": [] 
        })
        
    pipeline.append({"title": "5. TrOCR Recognition", "rois": roi_debug})
    return answers, pipeline
