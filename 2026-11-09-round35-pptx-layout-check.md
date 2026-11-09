# 第 35 輪（2026-11-09）：PowerPoint 版排版檢查與修正

## 結論

- 已用 LibreOffice 把 30 頁全部轉成圖片，逐頁看過，找到的問題都修好了。修正版放在本分支 `talks/statistics-module/statistics-module.pptx`，會覆蓋第 34 輪的版本。
- 另附 LibreOffice 轉出的預覽：`talks/statistics-module/statistics-module-preview.pdf`。
- 第 34 輪那一版有一個明顯問題：列表裡只要某一項含粗體或程式碼，那一項的「•」就會消失。第 20 頁的 1、2、3 編號也不見了。這一版已修正。

## 找到並修正的問題

1. **項目符號消失**（第 5、10、12、13、14、16、17、20、23、25、26、28、30 頁）。原因是 pptxgenjs 會在同一段的每個格式片段前都寫一份段落設定（`<a:pPr>`）。後面幾份帶「不加符號」的設定，把第一份蓋掉了。這也不符合 PPTX 格式規範，PowerPoint 開檔時可能會要求修復。修法：產生檔案後，每段只保留第一份段落設定。修正後檢查第 12 頁，每段只剩一份。
2. **表格第一欄太窄**：第 4 頁的「Application」、第 18 頁的 `_validation` 被斷成兩行。表格欄寬改成至少容納最長的英文單字，並多留 12% 的空間。程式碼字寬的估算也從 0.55 改成 0.6 倍字級。
3. **項目符號顏色**：項目開頭是粗體時，• 會跟著變綠色。已統一設成內文色。

## 檢查方式與限制

- 在 codespace 安裝了 `libreoffice-impress`、`fonts-noto-cjk`、`fonts-liberation`、`poppler-utils`，用的是 apt 和 sudo。
- 字型對應寫在 `~/.config/fontconfig/fonts.conf`：微軟正黑體 → Noto Sans CJK TC，Consolas → Liberation Mono。中文字寬和 PowerPoint 相同。英文和程式碼在 PowerPoint 裡會稍窄一些，所以這份預覽偏保守：預覽放得下，PowerPoint 裡也放得下。
- 結構檢查（`validate.py`）通過。
- 仍沒有在真正的 PowerPoint 裡開過。
- 第 9、11、19、22 頁仍是縮小到 90–97.5% 的字級。
- 還有兩處小瑕疵沒有處理：第 14 頁表格第一欄的「（PSR）」右括號掉到下一行，第 27 頁表格有一行最後一個字「疊」單獨換行。用 PowerPoint 的 Consolas 開，這兩處應該會變窄而放得下。
