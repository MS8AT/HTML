import pyodbc
from pathlib import Path

# === Настройки БД ===
SERVER = '192.168.88.20'
DATABASE = 'MS8AT'
USERNAME = 'sa'
PASSWORD = '!01Sloter01!'

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    "TrustServerCertificate=yes;"
)

def classify_case(row):
    """Классификация корпусов по форм-фактору"""
    product_group = str(row.get("product_group", "")).strip().upper()
    
    if "RACK" in product_group or "SERVER" in product_group or "INDUSTRIAL" in product_group:
        return "rack"
    if "MINI" in product_group or "ITX" in product_group:
        return "mini"
    if "MATX" in product_group or "MICROATX" in product_group:
        return "mATX"
    if "ATX" in product_group:
        return "ATX"
    
    # Резервная классификация
    hay = " ".join(str(row.get(k) or "") for k in ("type", "note", "ModelNo", "material")).lower()
    if any(k in hay for k in ("industrial", "server", "rack")):
        return "rack"
    if any(k in hay for k in ("mini", "minitx", "itx")):
        return "mini"
    if any(k in hay for k in ("microatx", "matx")):
        return "mATX"
    if "atx" in hay:
        return "ATX"
    return "ATX"

def get_cases():
    """Получает данные о корпусах из БД"""
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ModelNo, type, color, material, product_group,
                main_photo, front_photo, inside_photo, glass_photo,
                product_size, NW, GW, mb_form_factor, powersupply,
                cpu_cooler_height, gpu_max_length, io_ports
            FROM dbo.Cases
            ORDER BY ModelNo
        """)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

def get_image_url(model_no: str, photo_field: str | None) -> str:
    """Формирует URL к изображению"""
    if not photo_field or not photo_field.strip():
        return "placeholder.png"
    
    # Очищаем имя файла от путей
    filename = photo_field.strip().split('/')[-1].split('\\')[-1]
    safe_model = model_no.strip()
    
    # Формируем путь: /images/cases/case {ModelNo}/{filename}
    return f"../images/cases/case {safe_model}/{filename}"

def generate_html(cases_data):
    """Генерирует HTML-код для страницы корпусов"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cases — MS8AT Global</title>

  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
  
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      font-family: 'Roboto', sans-serif;
      background: #0a0a0f;
      color: #ffffff;
    }

    a { color: inherit; text-decoration: none; }

    /* ================= HEADER ================= */
    header {
      padding: 25px 30px 35px;
      text-align: center;
    }

    .top-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 25px;
      gap: 16px;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 220px;
    }

    .logo img {
      height: 42px;
      width: auto;
      display: block;
      filter: drop-shadow(0 0 14px #00ffe0);
    }

    .logo span {
      font-family: 'Orbitron', sans-serif;
      color: #00ffe0;
      font-size: 1.1rem;
      letter-spacing: 1px;
      text-shadow: 0 0 10px rgba(0,255,224,.6);
    }

    .top-buttons {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: flex-end;
      min-width: 220px;
    }

    .dealer-btn {
      padding: 8px 18px;
      border: 2px solid #00ffe0;
      border-radius: 30px;
      color: #00ffe0;
      font-weight: bold;
      transition: 0.3s;
      background: transparent;
      cursor: pointer;
      white-space: nowrap;
    }

    .dealer-btn:hover {
      background: #00ffe0;
      color: #0a0a0f;
      box-shadow: 0 0 18px #00ffe0;
    }

    .nav-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
      margin-bottom: 30px;
    }

    .nav-buttons a {
      padding: 8px 16px;
      border: 2px solid #00b3cc;
      border-radius: 30px;
      color: #00b3cc;
      font-size: 0.9rem;
      transition: 0.3s;
      background: rgba(0,179,204,0.08);
    }

    .nav-buttons a:hover {
      background: #00b3cc;
      color: #0a0a0f;
      box-shadow: 0 0 12px rgba(0,179,204,0.6);
    }

    header h1 {
      font-family: 'Orbitron', sans-serif;
      font-size: 2.6rem;
      color: #00ffe0;
      text-shadow: 0 0 10px #00ffe0;
    }

    /* ================= MAIN ================= */
    main {
      flex: 1;
      padding: 40px 20px;
      text-align: center;
    }

    .search-box {
      max-width: 500px;
      margin: 0 auto 30px;
    }

    .search-box input {
      width: 100%;
      padding: 12px;
      border-radius: 10px;
      border: 2px solid #00ffe0;
      background: rgba(0,0,0,0.4);
      color: #00ffe0;
      font-size: 1rem;
      outline: none;
      box-shadow: 0 0 10px rgba(0,255,224,0.35);
    }

    .filter-buttons {
      display: flex;
      gap: 12px;
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: 35px;
    }

    .filter-buttons button {
      padding: 8px 18px;
      border: 2px solid #00ffe0;
      background: transparent;
      color: #00ffe0;
      border-radius: 10px;
      cursor: pointer;
      transition: 0.3s;
    }

    .filter-buttons button.active,
    .filter-buttons button:hover {
      background: #00ffe0;
      color: #0a0a0f;
    }

    .cases-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 25px;
      max-width: 1200px;
      margin: 0 auto;
    }

    .case-card {
      background: rgba(0,0,0,0.6);
      border: 2px solid #00ffe0;
      border-radius: 15px;
      padding: 20px;
      box-shadow: 0 0 12px #00ffe0;
      cursor: pointer;
      transition: 0.3s;
      text-align: left;
    }

    .case-card:hover { transform: translateY(-6px); }

    .case-card img {
      width: 100%;
      max-height: 220px;
      object-fit: contain;
      border-radius: 10px;
      margin-bottom: 15px;
      background: rgba(0,0,0,0.25);
    }

    .case-card h3 {
      font-size: 1.1rem;
      text-shadow: 0 0 6px #00ffe0;
      margin-bottom: 6px;
    }

    .case-card p {
      opacity: 0.9;
      font-size: 0.95rem;
      line-height: 1.4;
    }

    /* ================= MODAL ================= */
    .modal {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.8);
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }

    .modal-content {
      background: #111125;
      padding: 30px;
      border-radius: 15px;
      max-width: 700px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
      position: relative;
      border: 2px solid rgba(0,255,224,0.45);
      box-shadow: 0 0 18px rgba(0,255,224,0.25);
      text-align: left;
    }

    .modal-content h3 {
      color: #00ffe0;
      margin-bottom: 15px;
      text-shadow: 0 0 8px rgba(0,255,224,0.5);
    }

    .modal-content img {
      max-width: 100%;
      margin-bottom: 15px;
      border-radius: 10px;
      background: rgba(0,0,0,0.25);
    }

    .modal-close {
      position: absolute;
      top: 10px;
      right: 18px;
      font-size: 26px;
      cursor: pointer;
      color: #b9b9b9;
    }

    .modal-content ul { padding-left: 18px; }
    .modal-content li { margin: 6px 0; opacity: 0.92; }

    /* ================= FOOTER ================= */
    footer {
      text-align: center;
      padding: 18px;
      font-size: 0.85rem;
      color: #777;
      border-top: 1px solid rgba(0,255,224,0.25);
    }

    @media(max-width: 720px){
      .top-bar{ flex-wrap: wrap; justify-content: center; }
      .top-buttons{ justify-content: center; }
      .logo{ justify-content: center; }
    }
  </style>

</head>

<body>

<header>
  <div class="top-bar">
    <div class="logo">
      <img src="../images/logo.png" alt="MS8AT Global">
      <span>MS8AT GLOBAL</span>
    </div>

    <div class="top-buttons">
      <!-- RU version -->
      <a href="../../ru/cases/cases.html" class="dealer-btn">RU</a>

      <!-- Home EN -->
      <a href="../index.html" class="dealer-btn">Home</a>

      <!-- Dealers EN -->
      <a href="../dealer/dealer.html" class="dealer-btn">Dealers</a>
    </div>
  </div>

  <div class="nav-buttons">
    <a href="./cases.html">Cases</a>
    <a href="../cooler/cooler.html">Coolers</a>
    <a href="../cpu/cpu.html">Processors</a>
    <a href="../mb/mb.html">Motherboards</a>
    <a href="../minipc/minipc.html">Mini-PC</a>
    <a href="../monitor/monitor.html">Monitors</a>
    <a href="../printer/printer.html">Printers</a>
    <a href="../soft/soft.html">Software</a>
    <a href="../svga/svga.html">Graphics Cards</a>

  </div>

  <h1>Cases</h1>
</header>

<main>
  <div class="search-box">
    <input type="text" id="searchInput" placeholder="Search by model or form factor...">
  </div>

  <div class="filter-buttons">
    <button class="active" data-filter="all">All</button>
    <button data-filter="mini">Mini-ITX</button>
    <button data-filter="mATX">mATX</button>
    <button data-filter="ATX">ATX</button>
    <button data-filter="rack">Rack / Server</button>
  </div>

  <div class="cases-grid" id="casesContainer">
"""

    # Генерация карточек корпусов
    for case in cases_data:
        model_no = case['ModelNo']
        category = case['category']
        image_url = get_image_url(model_no, case.get('main_photo'))
        
        # Формирование описания
        description_parts = []
        if case.get('color'):
            description_parts.append(f"Color: {case['color']}")
        if case.get('material'):
            description_parts.append(f"Material: {case['material']}")
        description = ", ".join(description_parts)
        
        html += f"""
    <div class="case-card" data-category="{category}">
      <img src="{image_url}" alt="Case {model_no}">
      <h3>Case {model_no}</h3>
      <p>Case, {description}</p>
    </div>
"""

    html += """
  </div>
</main>

<!-- MODAL -->
<div class="modal" id="modal">
  <div class="modal-content">
    <span class="modal-close" id="modalClose">&times;</span>
    <h3 id="modalTitle"></h3>
    <img id="modalImage" src="" alt="">
    <ul id="modalSpecs"></ul>
  </div>
</div>

<footer>
  © 2026 MS8AT Global
</footer>

  <script>
    let casesData = []; // Используется только для поиска, т.к. карточки уже на странице
    const DATA_SOURCE = './cases.json'; // Не используется, т.к. данные встроены в HTML

    // Важно: в JSON удобно хранить image как "../images/cases/filename.png"
    const FALLBACK_DATA = [];

    // Асинхронная загрузка не нужна, так как данные встроены

    function renderCasesFromDOM(filter) {
        const cards = document.querySelectorAll('.case-card');
        cards.forEach(card => {
            if (filter === 'all' || card.dataset.category === filter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    function openModal(item) {
        document.getElementById('modalTitle').textContent = item.model || '';
        document.getElementById('modalImage').src = item.image || '';
        const ul = document.getElementById('modalSpecs');
        ul.innerHTML = '';
        (item.specs || []).forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            ul.appendChild(li);
        });
        document.getElementById('modal').style.display = 'flex';
    }

    document.getElementById('modalClose').onclick = () =>
        document.getElementById('modal').style.display = 'none';

    window.onclick = e => {
        if (e.target === document.getElementById('modal')) {
            document.getElementById('modal').style.display = 'none';
        }
    };

    document.querySelectorAll('.filter-buttons button').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.filter-buttons button')
                .forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const f = btn.dataset.filter;
            renderCasesFromDOM(f);
        };
    });

    document.getElementById('searchInput').oninput = e => {
        const q = e.target.value.toLowerCase().trim();
        const cards = document.querySelectorAll('.case-card');
        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            if (!q || text.includes(q)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    };

    // Инициализация после загрузки DOM
    document.addEventListener('DOMContentLoaded', function() {
        renderCasesFromDOM('all');
    });

  </script>

</body>
</html>

<!-- === FIXED TELEGRAM BUTTON === -->
<a href="https://t.me/ms8at_global"
   target="_blank"
   title="MS8AT Global — Telegram"
   style="
     position: fixed;
     right: 22px;
     bottom: 22px;
     width: 58px;
     height: 58px;
     border-radius: 50%;
     background: #00ffe0;
     display: flex;
     align-items: center;
     justify-content: center;
     box-shadow: 0 0 18px rgba(0,255,224,0.8);
     z-index: 9999;
     transition: transform 0.25s, box-shadow 0.25s;
   "
   onmouseover="this.style.transform='scale(1.12)'; this.style.boxShadow='0 0 30px rgba(0,255,224,1)'"
   onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 0 18px rgba(0,255,224,0.8)'"
>
  <svg width="28" height="28" viewBox="0 0 240 240" fill="#0a0a0f" xmlns="http://www.w3.org/2000/svg">
    <path d="M120 0C53.7 0 0 53.7 0 120s53.7 120 120 120 120-53.7 120-120S186.3 0 120 0zm58.3 82.1-19.9 93.8c-1.5 6.7-5.5 8.3-11.2 5.2l-31-22.9-14.9 14.3c-1.6 1.6-3 3-6.1 3l2.2-31.7 57.7-52.1c2.5-2.2-.5-3.4-3.9-1.2l-71.3 44.9-30.7-9.6c-6.7-2.1-6.8-6.7 1.4-9.9l119.9-46.2c5.6-2 10.5 1.3 8.8 9.4z"/>
  </svg>
</a>
<!-- === /FIXED TELEGRAM BUTTON === -->
"""
    return html

if __name__ == "__main__":
    print("📊 Загружаем данные о корпусах из БД...")
    cases = get_cases()
    
    processed_cases = []
    for case in cases:
        model_no = str(case.get("ModelNo", "")).strip()
        if not model_no:
            continue
            
        category = classify_case(case)
        processed_cases.append({
            **case,
            "ModelNo": model_no,
            "category": category
        })
    
    print(f"✅ Обработано {len(processed_cases)} корпусов")
    
    print("🎨 Генерируем HTML...")
    html_content = generate_html(processed_cases)
    
    # Сохраняем HTML в текущую папку
    html_path = Path("cases.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"📄 Файл сохранен: {html_path.absolute()}")
    print("✅ Готово!")
