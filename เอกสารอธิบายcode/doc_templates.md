# 📄 อธิบายโค้ด: HTML Templates

---

# 🌐 [base.html](file:///d:/Workspace/Project/DIP-Project-HomeworkChecker-OCR/corr2/templates/base.html) — Layout หลัก

ทุกหน้าสืบทอด (extends) จากไฟล์นี้ ไม่ต้องเขียน boilerplate ซ้ำ

### DOCTYPE & HTML Tag

```html
<!DOCTYPE html>
<html lang="th">
```
- `<!DOCTYPE html>` = บอก browser ว่าเป็น HTML5
- `lang="th"` = ภาษาไทย ช่วย screen reader และ SEO

### Head

```html
<meta charset="UTF-8">
```
- รองรับอักขระ Unicode ทั้งหมด รวมถึงภาษาไทย

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```
- ทำให้หน้าเว็บ responsive บนมือถือ (ไม่ zoom out อัตโนมัติ)

```html
<title>{% block title %}Homework Checker{% endblock %}</title>
```
- Jinja2 block: หน้าลูกสามารถ override ชื่อ tab เหมือน: `{% block title %}ผลการตรวจ{% endblock %}`
- Default = `"Homework Checker"` ถ้าหน้าลูกไม่ override

### CSS — Design System

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
```
- Reset margin/padding ทุก element ให้เป็น 0 (ลบ browser default styles)
- `box-sizing: border-box` = ขนาด element รวม padding/border แล้ว (ไม่ขยายออก)

```css
:root {
  --bg:#0d1117;       /* พื้นหลัง: เกือบดำ (GitHub Dark style) */
  --surface:#161b22;  /* Card/Surface: เข้มน้อยกว่าพื้นหลัง */
  --border:#30363d;   /* เส้นขอบ: เทาเข้ม */
  --accent:#58a6ff;   /* สีหลัก: น้ำเงินฟ้า */
  --green:#3fb950;    /* สำหรับ "ถูก" */
  --red:#f85149;      /* สำหรับ "ผิด" */
  --text:#e6edf3;     /* ข้อความหลัก: เกือบขาว */
  --muted:#8b949e;    /* ข้อความรอง: เทา */
}
```
- CSS Custom Properties (Variables) ใช้ได้ทั่วทุก stylesheet
- ออกแบบตาม GitHub Dark Theme

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  display: flex; flex-direction: column; align-items: center;
  padding: 2rem 1rem;
}
```
- Font Stack: ใช้ System Font ที่ OS ให้มา → เร็ว ไม่ต้องโหลดจาก Google Fonts
- Flexbox: จัดทุกอย่างตรงกลางแนวแกน X

```css
.wrap { width: 100%; max-width: 800px; }
```
- Container ของทุกหน้า กว้างสูงสุด 800px แต่เล็กกว่าบน mobile

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1.25rem;
}
```
- Card component ใช้สำหรับจัดกลุ่ม content ให้ดูเป็น section ชัดเจน

```css
.flash.error   { background: rgba(248,81,73,.15); color: var(--red); }
.flash.success { background: rgba(63,185,80,.15); color: var(--green); }
```
- Flash messages: ใช้สีพื้นหลังโปร่งใส 15% เพื่อให้เห็นแต่ไม่ฉูดฉาด

```css
.btn { display: inline-block; padding: .55rem 1.1rem; border-radius: 6px;
       font-size: .9rem; font-weight: 600; cursor: pointer; border: none;
       font-family: inherit; transition: opacity .15s; }
.btn:hover { opacity: .85; }
.btn-primary   { background: var(--accent); color: #0d1117; }
.btn-secondary { background: var(--border); color: var(--text); }
```
- Button components: Primary (blue) และ Secondary (grey)
- `transition: opacity .15s` = hover effect เบลอปุ่มเบาๆ ใน 0.15 วินาที

### Body Content

```html
<header>
  <h1>Homework Checker</h1>
  <p>... ตรวจการบ้านด้วย Tesseract / TrOCR / corr2</p>
</header>
```
- Header ส่วนบนทุกหน้า

```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
    <div class="flash {{ cat }}">{{ msg }}</div>
  {% endfor %}
{% endwith %}
```
- `get_flashed_messages(with_categories=true)` = ดึง flash messages พร้อมประเภท (`error`/`success`)
- วน loop แสดงเป็น `<div class="flash error">` หรือ `<div class="flash success">`

```html
{% block content %}{% endblock %}
```
- **Placeholder** ที่หน้าลูกต้อง fill ด้วย content ของตัวเอง

---

# 📤 [index.html](file:///d:/Workspace/Project/DIP-Project-HomeworkChecker-OCR/corr2/templates/index.html) — หน้าอัปโหลด

```html
{% extends "base.html" %}
```
- สืบทอด layout จาก base.html → ได้ header, CSS, flash messages ทั้งหมดมาโดยอัตโนมัติ

```html
{% block content %}
<div class="card">
```
- ทุกอย่างข้างในจะแทนที่ `{% block content %}` ใน base.html

```html
<form action="{{ url_for('check') }}" method="post" enctype="multipart/form-data">
```
- `url_for('check')` = สร้าง URL `/check` แบบ dynamic (ถ้าเปลี่ยน route name ก็ update อัตโนมัติ)
- `method="post"` = ส่งข้อมูลแบบ POST
- `enctype="multipart/form-data"` = **จำเป็นมาก** เมื่อ form มีการ upload ไฟล์ ถ้าไม่ใส่ไฟล์จะไม่ถูกส่งไป

```html
<input type="file" name="file" accept=".png,.jpg,.jpeg,.bmp" required>
```
- `name="file"` = ต้องตรงกับ `request.files.get("file")` ใน app.py
- `accept=...` = บอก browser ว่าให้กรอง file explorer ให้แสดงเฉพาะ image
- `required` = HTML validation ห้ามส่ง form ถ้ายังไม่เลือกไฟล์

```html
<select name="engine" required>
    <option value="corr2">Correlation 2D (Default)</option>
    <option value="teserract">Tesseract OCR</option>
    <option value="trocr">TrOCR (AI)</option>
</select>
```
- `name="engine"` = ต้องตรงกับ `request.form.get("engine")` ใน app.py
- `value` ของแต่ละ option คือค่าที่จะส่งไป (ไม่ใช่ข้อความที่แสดง)

```html
<textarea name="answers_raw" placeholder="เช่น:&#10;7&#10;4" rows="6" required>
```
- `&#10;` = HTML entity ของ newline (`\n`) ใช้ใน attribute placeholder
- `rows="6"` = ความสูงเริ่มต้น 6 บรรทัด

---

# 📊 [result.html](file:///d:/Workspace/Project/DIP-Project-HomeworkChecker-OCR/TrOCR/templates/result.html) — หน้าแสดงผล

### CSS เพิ่มเติม

```css
.score-box .pct { font-size: 3rem; font-weight: 700; color: var(--accent) }
```
- แสดงเปอร์เซ็นต์ขนาดใหญ่ เป็น highlight ของหน้า

```css
.roi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
```
- CSS Grid แบบ Auto-fill: จัดการ์ดกล่องคำตอบเป็น column อัตโนมัติ
- แต่ละการ์ดกว้างอย่างน้อย 300px ถ้าพอที่จะวาง 2 column ก็วาง มิฉะนั้น 1 column

```css
.char-imgs img { image-rendering: pixelated; }
```
- ภาพ Template 24×42px ที่ขยายขึ้น → แสดงเป็น pixel art ชัดๆ ไม่ blur

### ส่วน Header ผลการตรวจ

```html
<h2>ผลการตรวจ ({{ engine }})</h2>
```
- `{{ engine }}` = แสดงชื่อ Engine ที่ใช้ ส่งมาจาก [app.py](file:///d:/Workspace/Project/DIP-Project-HomeworkChecker-OCR/corr2/app.py) ผ่าน `render_template`

### ตารางผลคะแนน

```html
{% if result.success %}
<div class="score-box">
    <div class="pct">{{ result.score }}%</div>
    <div class="lbl">ถูก {{ result.correct }} / {{ result.total }} ข้อ</div>
</div>
```
- แสดงเฉพาะกรณีสำเร็จ ถ้า `success=False` → ข้ามไปแสดง error

```html
{% for r in result.results %}
<tr>
    <td>{{ r.id }}</td>
    <td><strong>{{ r.got or "—" }}</strong></td>  <!-- ถ้าว่าง แสดง em dash -->
    <td>{{ r.expected }}</td>
    <td>
        {% if r.correct %}<span class="ok">✓ ถูก</span>
        {% else %}<span class="err">✗ ผิด</span>{% endif %}
    </td>
</tr>
{% endfor %}
```
- วน loop แสดงทีละข้อ
- `r.got or "—"` = ถ้า got เป็น string ว่าง → แสดง `—` แทน

### Pipeline Debug Section

```html
{% if steps %}
{% for step in steps %}
    {% if step.rois is defined %}
```
- แสดง section นี้เฉพาะเมื่อมี `steps` ถูกส่งมาจาก app.py
- `step.rois is defined` = ตรวจว่า step นี้เป็นประเภท ROI (กล่องคำตอบ) หรือเป็นภาพ step ธรรมดา

```html
<!-- ROI Card -->
<img src="data:image/png;base64,{{ roi.b64_color }}">
```
- Data URL: embed ภาพ PNG โดยตรงใน HTML โดยไม่ต้องมี URL จริง
- `roi.b64_color` = ภาพ ROI สีจริง encode เป็น base64 string

```html
{% for ch in roi.chars %}
<!-- สำหรับ corr2 เท่านั้น -->
<div class="char-label">{{ ch.label }}</div>
<div class="char-score">score: {{ ch.score }}</div>
{% for d,s in ch.top3 %}
  '{{ d }}': {{ s }}<br>
{% endfor %}
```
- แสดง template matching details ของแต่ละ character
- `ch.top3` = list ของ tuple [(ตัวเลข, คะแนน)](file:///d:/Workspace/Project/DIP-Project-HomeworkChecker-OCR/combined/app.py#16-17) 3 อันดับแรก
- สำหรับ Tesseract และ TrOCR: `roi.chars` จะเป็น `[]` เปล่า → ส่วนนี้จะไม่แสดง

```html
{% else %}
<!-- Image Step -->
<img class="step-img" src="data:image/png;base64,{{ step.b64 }}" alt="{{ step.title }}">
{% endif %}
```
- ถ้าไม่มี `rois` → แสดงเป็นภาพ step ปกติ (Original, Grayscale, Threshold ฯลฯ)
