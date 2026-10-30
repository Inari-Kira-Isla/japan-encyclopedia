# 景點專輯（每縣 8 個，每個獨立一張圖）
檔案：data/v2_spot/<prefecture_id>.json
{ "id":"kyoto", "spots":[ 8 項 ] }
每項：{"title_zh","title_ja","category":"神社寺院|城郭史蹟|自然絕景|溫泉|庭園公園|街區古鎮|主題設施|海島海岸|山岳高原 其中之一",
 "area_zh":"所屬市町／地區","summary_zh"(≤40字),"body_zh"(120–200字：特色、歷史或成因、看點),
 "facts":[{"label":"所在地|開創／成因|看點|門票|交通|…","value":""} 3條],
 "best_season_zh":"","tips_zh":"40–80字","tags":[3–4個],"sources":["真實URL 1–2個"],"confidence":"high|medium|low",
 "prompt_en":"單一景點出圖提示詞：取景角度、季節、時間、光線、前景中景背景；唔要文字／招牌，唔要可辨識人物"}
規則：8 個覆蓋不同 category（至少 5 種），全部係該縣真正知名景點，彼此不重複，並盡量分佈在縣內不同地區；用 WebSearch/WebFetch 核實（官方觀光網、維基），核實不到寫 confidence=low，唔好編造。商標主題設施（如迪士尼）用通用描述，不依賴商標畫面。繁體中文。完成後 python3 驗證：8 項、欄位齊全、title 不重複，回報一行。
