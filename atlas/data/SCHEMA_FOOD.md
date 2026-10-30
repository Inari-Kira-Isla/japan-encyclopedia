# 美食專輯（每縣 8 道，每道獨立一張圖）
檔案：data/v2_food/<prefecture_id>.json
{ "id":"kyoto", "foods":[ 8 項 ] }
每項：{"title_zh","title_ja","category":"鄉土料理|麵飯|海鮮|肉類|甜點和菓子|酒與飲品|特產食材|B級美食 其中之一",
 "summary_zh"(≤40字),"body_zh"(120–200字：是什麼、來由、做法特色、吃法),
 "facts":[{"label":"起源|主要食材|時節|吃法|…","value":""} 3條],
 "season_zh":"","where_zh":"在縣內哪個地區／哪類店最有代表性","tags":[3–4個],
 "sources":["真實 URL 1–2 個"],"confidence":"high|medium|low",
 "prompt_en":"單一菜式出圖提示詞：盛器、食材、擺盤、配襯、桌面／環境、光線；一道菜一張圖，唔要多道菜併盤，唔要文字／招牌"}
規則：8 道要覆蓋不同 category（至少 5 種），全部係該縣真正知名的在地美食／名產，彼此不重複；用 WebSearch/WebFetch 核實（官方觀光、農水省「農林水産省 うちの郷土料理」、維基），核實不到寫 confidence=low，唔好編造起源年份。繁體中文。完成後 python3 驗證：8 項、欄位齊全、title 不重複，回報一行。
