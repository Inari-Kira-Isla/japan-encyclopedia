# 日本地方文化圖鑑（atlas）

以四十七都道府縣為經、九類文化為緯的日本地方文化資料站。本目錄收錄**資料與靜態網站**，
**不含圖片**（見下文「圖片」）。純前端、無需後端；`site/index.html` 以 hash 路由運作。

## 內容規模

- 47 個都道府縣，每縣包含：
  - **9 類核心項目**：建築（architecture）、美食（food）、文化（culture）、歷史（history）、
    吉祥物（mascot）、風景（scenery）、景點（spot）、體驗（experience）、服飾（costume）
  - **8 項美食**（food_1…food_8）與 **8 項景點**（spot_1…spot_8）
  - **重點地區**（每縣約 4–5 個，每區含景點／美食／風景三項）
- 合計 1,751 個項目（對應 1,751 張圖片）。

## 目錄結構

```
atlas/
├── data/                 資料來源（JSON）
│   ├── v2/<縣id>.json        概覽、9 類核心項目、重點地區
│   ├── v2_food/<縣id>.json   8 項美食
│   ├── v2_spot/<縣id>.json   8 項景點
│   └── SCHEMA*.md            各資料格式說明
├── site/                 靜態網站（可直接以 file:// 或任一靜態主機開啟）
│   ├── index.html
│   ├── config.js             圖片基底網址設定（JP_IMG_BASE）
│   └── data/index.js, p_<縣id>.js   由 build_site.py 產生的前端資料
├── build_site.py         資料＋原始圖片 → site/data 與縮圖
└── README.md
```

每個項目含：`title_zh/ja`、`summary_zh`、`body_zh`、`facts`、`tips_zh`、`tags`、`sources`（來源 URL）、
`confidence`（可信度 high／medium／low）、`prompt_en`（出圖提示詞）。

## 圖片：不放入本 repo

圖片共 1,751 張，大圖＋縮圖體積約 404MB，不適合放進本 repo，因此**由外部圖床提供**，
網站透過 `site/config.js` 的 `JP_IMG_BASE` 指向圖床。

資料內存的是**相對路徑**，網站會在前面接上 `JP_IMG_BASE`：

| 用途 | 路徑規則 |
|---|---|
| 縮圖（列表、卡片） | `img/t/<縣id>/<類>.webp`，如 `img/t/kyoto/scenery.webp` |
| 大圖（詳情、封面） | `img/<縣id>/<類>.webp`（把 `img/t/` 換成 `img/`） |
| 美食／景點 | `img/<縣id>/food_N.webp`、`img/<縣id>/spot_N.webp`（N=1…8） |
| 重點地區 | `img/areas/<地區id>/<spot｜food｜scenery>.webp` |

### 如何設定

1. 把圖片依上述規則上傳到圖床（保持 `img/…` 與 `img/t/…` 的目錄結構）。
2. 編輯 `site/config.js`：

   ```js
   window.JP_IMG_BASE = "https://你的圖床/路徑/";   // 結尾必須有 /
   ```

3. 預設為空字串，此時圖片走相對路徑（即把 `img/` 放在 `site/` 旁邊即可顯示）；
   若找不到圖片，網站會顯示「圖片待生成」佔位。

### 重建（需要原始圖片）

```bash
python3 build_site.py --images /path/to/原始圖片目錄
```

原始圖片結構為 `<縣id>/<類>.webp`、`<縣id>/food_N.webp`、`<縣id>/spot_N.webp`、
`areas/<地區id>/<類>.webp`。腳本會產生 `site/data/*.js`，並輸出大圖（長邊 1280px）與縮圖（480px）
到 `site/img/`（已被 `.gitignore` 排除）。**沒有圖片時請勿重跑**，否則所有項目會被當成無圖。

## 誠實聲明與已知缺陷

- 資料由 **AI 整理**，並盡量以維基百科、官方觀光網等公開來源核實，但**仍可能有誤**，請勿視為權威資料。
- 可信度分佈：high 818、medium 664、**low 230**（核實不到者以保守說法書寫），另有 39 項未標註可信度。
  使用或引用「低」可信度項目前請自行查證。
- **來源薄弱**：約 1,488 個項目只附 0–1 個來源，不少僅有維基單一來源，未經交叉驗證。
- **圖片為 AI 生成示意，並非實景照片**，不可當作真實景觀、建築、人物或商品的紀錄。
  網站上每張圖皆標示「AI 生成示意」。
- **吉祥物（mascot）為原創角色，非官方吉祥物**，與各地真實吉祥物及其商標無關。
- 商標地標以上位概念描述；歷史人物、服飾模特兒皆不描繪可辨識真人。
- 未做多語言校對；日文名稱與細節可能有誤。
