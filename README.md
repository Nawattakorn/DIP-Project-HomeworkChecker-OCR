# HomeworkChecker-OCR
## โครงการวิชา Digital Image Processing

**HomeworkChecker-OCR** เป็นระบบตรวจการบ้านอัตโนมัติโดยใช้เทคโนโลยี Optical Character Recognition (OCR) และ Digital Image Processing สามารถอ่านคำตอบจากภาพถ่ายกระดาษคำตอบและเปรียบเทียบกับเฉลยเพื่อให้คะแนนอัตโนมัติ โครงการนี้เปรียบเทียบประสิทธิภาพของ 3 เทคนิค OCR ได้แก่ Template Matching (Corr2), Tesseract OCR และ TrOCR

### วัตถุประสงค์
- พัฒนาระบบตรวจการบ้านอัตโนมัติที่รับภาพถ่ายกระดาษคำตอบและให้คะแนนทันที
- ศึกษาและเปรียบเทียบประสิทธิภาพของเทคนิค OCR 3 วิธี: Corr2, Tesseract และ TrOCR
- ประยุกต์ใช้เทคนิค Digital Image Processing เพื่อปรับปรุงคุณภาพภาพก่อนการอ่านตัวอักษร
- สร้างเว็บแอปพลิเคชันที่ใช้งานง่ายสำหรับครูและนักเรียน

### ฟีเจอร์หลัก
- **รองรับ 3 เทคนิค OCR**:
  - **Corr2 (Template Matching)**: เหมาะกับตัวเลขตัวพิมพ์ ประมวลผลเร็วที่สุด
  - **Tesseract OCR**: รองรับทั้งตัวเลขและตัวอักษรภาษาอังกฤษตัวพิมพ์
  - **TrOCR (Microsoft)**: เหมาะกับลายมือเขียน ใช้ Vision Transformer
- **โหมดเปรียบเทียบ**: แสดงผลการทำงานของทั้ง 3 วิธีพร้อมกันในหน้าเดียว
- **Image Preprocessing Pipeline**: ใช้เทคนิค Gaussian Blur, Otsu Threshold, Morphological Operations และ Connected Components
- **การตรวจจับกล่องคำตอบอัตโนมัติ**: ใช้ Contour Detection และ Aspect Ratio Filtering
- **Web Interface**: หน้าเว็บที่สร้างด้วย Flask, Bootstrap พร้อม UI ที่ใช้งานง่าย
- **API Endpoint**: รองรับการเรียกใช้ผ่าน REST API

### โครงสร้างโฟลเดอร์
```
DIP-Project-HomeworkChecker-OCR/
│
├── source_code/
│   ├── app.py                      # Flask web application หลัก
│   ├── ocr_corr2.py               # OCR วิธีที่ 1: Template Matching
│   ├── ocr_teserract.py           # OCR วิธีที่ 2: Tesseract Engine
│   ├── ocr_trocr.py               # OCR วิธีที่ 3: Microsoft TrOCR
│   ├── checker_corr2.py           # Grading logic สำหรับ Corr2
│   ├── checker_teserract.py       # Grading logic สำหรับ Tesseract
│   ├── checker_trocr.py           # Grading logic สำหรับ TrOCR
│   └── templates/                 # HTML templates
│       ├── base.html              # Template หลัก
│       ├── index.html             # หน้าแรก - อัปโหลดภาพ
│       ├── result.html            # แสดงผลการตรวจ
│       └── compare.html           # เปรียบเทียบ 3 วิธี
│
├── test_image/                    # ภาพตัวอย่างสำหรับทดสอบ
│   ├── test_sample.jpg           # ตัวอย่างข้อสอบ
│   ├── test_grade1_add_sub.png   # โจทย์คณิตศาสตร์
│   ├── handwritting1.jpg         # ลายมือเขียน
│   └── ...
│
├── รายงาน_updated.pdf            # รายงานโครงการ (ภาษาไทย)
├── Homework_Checker_OCR_Comparison_Silde.pdf  # สไลด์นำเสนอ
└── README.md                      # คู่มือการใช้งาน (ไฟล์นี้)
```

### สถาปัตยกรรมระบบ

```
┌─────────────────────────────────────────────────┐
│           Web Interface (Flask)                 │
│  index.html → app.py → result.html/compare.html │
└────────────────┬────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌─────────────┐      ┌──────────────┐
│ OCR Engine  │      │ Checker      │
│ (3 วิธี)    │      │ (Grading)    │
├─────────────┤      ├──────────────┤
│ ocr_corr2   │◄────►│ checker_corr2│
│ ocr_tesser..│◄────►│ checker_tes..│
│ ocr_trocr   │◄────►│ checker_trocr│
└─────────────┘      └──────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Image Preprocessing         │
│  - Grayscale                 │
│  - Gaussian Blur             │
│  - Otsu Threshold            │
│  - Connected Components      │
│  - Contour Detection         │
└──────────────────────────────┘
```

### การทำงานของระบบ

#### 1. Image Preprocessing Pipeline (ทั้ง 3 วิธี)
```
ภาพต้นฉบับ
    ↓
1. Grayscale Conversion (cv2.cvtColor)
    ↓
2. Gaussian Blur (ลด noise ก่อน threshold)
    ↓
3. Otsu Threshold (แปลงเป็น Binary Image อัตโนมัติ)
    ↓
4. Connected Components Analysis (กำจัด noise เล็กๆ)
    ↓
5. Contour Detection + Aspect Ratio Filter
    ↓
ได้กล่องคำตอบทั้งหมด
```

#### 2. OCR Methods Comparison

| วิธี | หลักการ | เหมาะกับ | ความเร็ว | ความแม่นยำ |
|------|---------|----------|----------|-----------|
| **Corr2** | Template Matching (2D Correlation) | ตัวเลขตัวพิมพ์ | เร็วที่สุด (CPU) | ✅ ดีมาก |
| **Tesseract** | LSTM + CTC (Rule-based) | ตัวเลข + อักษรตัวพิมพ์ | เร็ว (CPU) | ✅ ดีมาก |
| **TrOCR** | Vision Transformer | ตัวอักษรลายมือ | ช้า (ต้องการ GPU) | ✅ ดี |

#### 3. OCR Pipeline แต่ละวิธี

**Corr2 (Template Matching)**:
```
ROI → Resize to 42x24 → matchTemplate → max correlation score → ตัวเลข
```

**Tesseract OCR**:
```
ROI → Upscale x3 → Threshold + Padding → LSTM Engine → Filter → ข้อความ
```

**TrOCR (Microsoft)**:
```
ROI → Padding → PIL Image → Vision Encoder → Transformer Decoder → ข้อความ
```

### วิธีติดตั้งและใช้งาน

#### 1. Clone โครงการ
```bash
git clone https://github.com/Nawattakorn/DIP-Project-HomeworkChecker-OCR.git
cd DIP-Project-HomeworkChecker-OCR/source_code
```

#### 2. ติดตั้ง Dependencies

**สำหรับ Corr2 (วิธีพื้นฐาน)**:
```bash
pip install flask opencv-python-headless pillow numpy werkzeug
```

**สำหรับ Tesseract OCR** (ต้องติดตั้ง Tesseract Engine ก่อน):

- **Windows**: ดาวน์โหลดจาก [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

จากนั้นติดตั้ง Python wrapper:
```bash
pip install pytesseract
```

**สำหรับ TrOCR** (ต้องการ GPU แนะนำ):
```bash
pip install torch transformers pillow
```

#### 3. รันเว็บแอปพลิเคชัน
```bash
python app.py
```
เปิดเว็บเบราว์เซอร์ที่ `http://localhost:5000`

### การใช้งานผ่าน Web Interface

1. **เลือกไฟล์ภาพ**: อัปโหลดภาพกระดาษคำตอบ (รองรับ PNG, JPG, JPEG, BMP)
2. **ใส่เฉลย**: กรอกคำตอบที่ถูกต้อง (คั่นด้วยเครื่องหมายจุลภาคหรือขึ้นบรรทัดใหม่)
3. **เลือก OCR Engine**:
   - Corr2: สำหรับตัวเลขตัวพิมพ์
   - Tesseract: สำหรับตัวเลข/อักษรตัวพิมพ์
   - TrOCR: สำหรับลายมือเขียน
   - Compare: เปรียบเทียบทั้ง 3 วิธีพร้อมกัน
4. **ดูผลลัพธ์**: ระบบจะแสดงคะแนน, คำตอบที่ตรวจพบ และภาพประกอบแต่ละขั้นตอน

### ผลการทดสอบ

#### ตารางสรุปความแม่นยำ

| ประเภทข้อมูล | Corr2 | Tesseract | TrOCR |
|--------------|-------|-----------|-------|
| ตัวเลขตัวพิมพ์ | ✅ ดีมาก | ✅ ดีมาก | ✅ ดี |
| ตัวเลขลายมือ | ❌ ไม่ดี | ❌ ไม่ดี | ❌ ไม่ดี |
| อักษร EN ตัวพิมพ์ | ❌ ไม่รองรับ | ✅ ดีมาก | ✅ ดีมาก |
| อักษร EN ลายมือ | ❌ ไม่รองรับ | ❌ ไม่ดี | ✅ ดี |

**ข้อสังเกต**:
- **Corr2**: เหมาะที่สุดสำหรับตัวเลขตัวพิมพ์ที่มี font ชัดเจน ประมวลผลเร็วที่สุด
- **Tesseract**: เหมาะกับเอกสารตัวพิมพ์ทั่วไป รองรับหลายภาษา
- **TrOCR**: เหมาะกับลายมือเขียนภาษาอังกฤษ แต่ต้องการทรัพยากรมาก

### เทคนิค Digital Image Processing ที่ใช้

| คำสั่ง/ฟังก์ชัน | คำอธิบาย | เทียบเท่า MATLAB |
|-----------------|----------|-----------------|
| `cv2.imread()` | โหลดภาพจากไฟล์ | `imread` |
| `cv2.cvtColor(BGR2GRAY)` | แปลงเป็น Grayscale | `rgb2gray` |
| `cv2.GaussianBlur()` | Gaussian blur ลด noise | `imgaussfilt` |
| `cv2.threshold(THRESH_OTSU)` | Otsu threshold อัตโนมัติ | `graythresh + imbinarize` |
| `cv2.connectedComponentsWithStats()` | หา connected components | `bwlabel` |
| `cv2.findContours()` | ค้นหา contour | `bwboundaries` |
| `cv2.morphologyEx(MORPH_OPEN)` | Opening (กัดเซาะแล้วขยาย) | `imopen` |
| `cv2.morphologyEx(MORPH_CLOSE)` | Closing (ขยายแล้วกัดเซาะ) | `imclose` |
| `cv2.resize()` | Resize ภาพ | `imresize` |
| `cv2.matchTemplate()` | Template Matching | `normxcorr2` |
| `pytesseract.image_to_string()` | อ่านข้อความด้วย Tesseract | - |
| `model.generate()` | อ่านข้อความด้วย Transformer | - |

### การพัฒนาต่อยอด

- [ ] รองรับภาษาไทย (ต้อง fine-tune TrOCR model)
- [ ] ปรับปรุง accuracy สำหรับตัวเลขลายมือ
- [ ] เพิ่ม confidence score แต่ละข้อ
- [ ] รองรับ multiple choice (a, b, c, d)
- [ ] Mobile application (React Native/Flutter)
- [ ] Batch processing (ตรวจหลายคนพร้อมกัน)
- [ ] Export ผลเป็น Excel/CSV

### ปัญหาที่พบและแนวทางแก้ไข

| ปัญหา | สาเหตุ | แนวทางแก้ไข |
|-------|--------|--------------|
| ตัวเลขลายมือจับไม่ได้ | Template สร้างจาก font ตัวพิมพ์ | ใช้ TrOCR หรือ fine-tune ด้วย handwritten dataset |
| กล่องคำตอบจับไม่หมด | Contour filter เข้มเกินไป | ปรับค่า aspect ratio และ area threshold |
| TrOCR ช้ามาก | ใช้ Transformer ขนาดใหญ่ | ใช้ GPU หรือเปลี่ยนเป็น trocr-small |
| Tesseract อ่านผิด | ROI มี noise | เพิ่ม preprocessing (denoise, deskew) |

### ข้อมูลเพิ่มเติม

- **รายงานฉบับเต็ม**: [รายงาน_updated.pdf](./รายงาน_updated.pdf)
- **สไลด์นำเสนอ**: [Homework_Checker_OCR_Comparison_Silde.pdf](./Homework_Checker_OCR_Comparison_Silde.pdf)
- **ภาพตัวอย่าง**: โฟลเดอร์ [test_image/](./test_image/)

### ผู้พัฒนา
- **นวัตกร** - [Nawattakorn](https://github.com/Nawattakorn)
- **อัทธเมศร์** - [Autthamet](https://github.com/b3y0und)

### License
โครงการนี้พัฒนาขึ้นเพื่อการศึกษาในรายวิชา Digital Image Processing

---

**หมายเหตุ**: 
- ควรติดตั้ง Tesseract OCR Engine บนเครื่องก่อนใช้งาน Tesseract method
- TrOCR ต้องการ RAM อย่างน้อย 4GB และแนะนำให้ใช้ GPU
- สำหรับการใช้งานจริง แนะนำให้ใช้ Corr2 สำหรับตัวเลขตัวพิมพ์ (เร็วและแม่นที่สุด)
