# 日本視覺圖鑑 資料結構
每個都道府縣一個物件，放入 data/part_<N>.json（JSON 陣列）：
{
 "id": "hokkaido", "name_zh": "北海道", "name_ja": "北海道", "region": "北海道", "capital_zh": "札幌",
 "items": {
   "architecture": {"title_zh","title_ja","desc_zh"(≤50字),"prompt_en"},
   "food": ..., "culture": ..., "history": ..., "mascot": ..., "scenery": ..., "spot": ..., "experience": ..., "costume": ...
 }
}
九類：architecture 特色建築｜food 當地美食｜culture 文化（祭典／工藝／藝能）｜history 歷史（具體史蹟或事件場景，不畫真人肖像）｜mascot 吉祥物｜scenery 自然風景｜spot 代表景點｜experience 體驗活動｜costume 衣着裝扮（傳統或在地服飾）
規則：
- prompt_en 英文、具體（地點、物件、時間、光線、構圖），不含任何文字／招牌字／水印要求，不指名真人。
- mascot：data 內可寫真實吉祥物名稱（title_zh/desc_zh），但 prompt_en 要求「原創」可愛角色，取材該縣特產／象徵，明確「not replicating any existing trademarked mascot」。
- history：畫史蹟建築或場景重現，不畫可辨認的歷史人物肖像。
- costume：畫無名模特兒穿著傳統／在地服飾（非人物肖像）。
- 事實要穩：只寫有把握的知名項目；不確定寧選更廣為人知的。每縣 9 項彼此不重複（例如 spot 同 scenery 唔好同一個地方）。

## 縣內重點地區（area）
寫入 data/areas_<N>.json（JSON 陣列，每個地區一個物件）：
{ "id": "kyoto_arashiyama", "prefecture_id": "kyoto", "name_zh": "嵐山", "name_ja": "嵐山",
  "items": { "spot": {title_zh,title_ja,desc_zh,prompt_en}, "food": {...}, "scenery": {...} } }
每縣選 4 個彼此地理上分開、辨識度高的地區（市／町／著名區域／島嶼）；北海道、東京、沖繩可選 5 個。三類內容要屬該地區本身，唔好重複縣級已寫嘅同一項（縣級資料 data/part_N.json 可能仍在寫，唔需對照）。prompt_en 規則同上。
