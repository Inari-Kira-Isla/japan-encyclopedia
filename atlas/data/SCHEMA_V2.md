# 資料 v2（網站用，詳盡＋核實）
每個都道府縣一個檔 data/v2/<prefecture_id>.json：
{
 "id","name_zh","name_ja","region",
 "overview": {"intro_zh": 150-220字總介紹, "capital_zh","area_km2"(約),"population_approx","flower_zh","bird_zh","tree_zh"(不確定留空),"climate_zh":60字內,"access_zh":主要門戶交通60字內,"specialties_zh":[3-6項特產],"best_season_zh":""},
 "items": { architecture, food, culture, history, mascot, scenery, spot, experience, costume 各一項 },
 "areas": [ {"id","name_zh","name_ja","intro_zh":80-120字,"items":{"spot","food","scenery"}} ]   // 沿用 data/areas_*.json 的地區，可替換不準確者，保持 4–5 個
}
每個 item：
 {"title_zh","title_ja","summary_zh"(≤50字),"body_zh"(180–280字：是什麼、歷史／來由、特色、現況，重事實),
  "facts":[{"label":"所在地|起源|時節|特色|門票|…","value":""} 3–5 條],
  "best_season_zh":"","tips_zh":"旅遊或體驗小貼士 40–80字","tags":["3–5 個中文標籤"],
  "sources":["真實 URL 1–2 個（官方觀光或維基）"],"confidence":"high|medium|low","prompt_en":"出圖提示詞"}
規則：
- 先讀 data/part_*.json 與 data/areas_*.json 找到你負責縣份的初稿，修正錯誤、補足詳盡內容。事實有疑問就用 WebSearch/WebFetch 核實（官方觀光網、維基）；核實不到的寫 confidence=low 並用保守說法，唔好編造數字或年份。
- mascot：body_zh 可介紹該縣真實吉祥物（名稱、設計來源），prompt_en 仍要求「原創、受當地象徵啟發、唔複製任何商標吉祥物」。
- 商標地標（如迪士尼）：title 用上位概念（如「浦安」），prompt 用通用描述，body 可提及但不依賴商標畫面。
- history：場景或史蹟，不畫可辨識歷史人物。costume：無名模特兒。
- prompt_en 要貼合最終 title／內容；寫具體（地點、物件、季節、時間、構圖），不含文字／招牌字要求；統一尾巴由出圖腳本加，唔使寫風格詞。
- 繁體中文。完成後 python3 驗證 JSON 載入、9 類齊全、每地區 3 類齊全、各欄位非空，回報一行（縣數、地區數、low confidence 數）。
