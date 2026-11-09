# 第 34 輪（2026-11-09）：統計模組簡報轉成 PowerPoint

## 結論

- 統計模組簡報已轉成可編輯的 PowerPoint：本分支 `talks/statistics-module/statistics-module.pptx`，30 頁，和 `slides.md` 頁序相同。
- 這份 PPTX 不是截圖：文字、表格、連結都可以直接在 PowerPoint 裡改。配色和字級照 `theme.css`，講者備註、頁首、頁尾、頁碼也都保留。
- 有 4 頁內容較密，為了不超出頁面，整頁字級等比例縮小：第 9 頁 90%、第 11 頁 92.5%、第 19、22 頁 97.5%。
- **沒有做目視檢查**：這台 codespace 沒有 LibreOffice 和中文字型，沒辦法把投影片轉成圖片來看。超出頁面的檢查是轉換程式依字寬估算的，請在 PowerPoint 裡翻一遍。

## 做法

- 沒有用 Marp 的 `--pptx` 匯出：它需要 Chrome，而且每頁只輸出一張圖片，無法編輯。
- 改用 pptxgenjs 3.12.0（裝在 session 的 scratchpad，沒動 repo）。轉換程式 `tools/marp_to_pptx.js` 直接讀 `slides.md`。
- 版面換算：1280×720 px 對應 13.333×7.5 吋，1 px = 0.75 pt。例如內文 30 px 是 22.5 pt，compact 頁 27 px 是 20.25 pt。
- 字型：中文 Microsoft JhengHei，程式碼 Consolas。Mac 上沒有正黑體時，PowerPoint 會自動換成其他中文字型。
- 閱讀路線頁的章名連結改成跳到 PPTX 裡的第 3、8、21 頁；外部連結照舊指到 GitHub。
- 章節（PowerPoint 的「節」）：開場、01、02、03、結語。

## 驗證

- 用 pptx skill 的 `validate.py` 檢查結構：全部通過。
- 用 `slide_text.py` 抽出全部文字和 `slides.md` 逐頁核對：30 頁的內容和講者備註都在。
- 修正一個問題：列表項目中的粗體和程式碼片段原本被拆成獨立段落，原因是 pptxgenjs 遇到帶 bullet 設定的片段就會另起一段。已改成只在每項的第一個片段設 bullet。

## 沒有做的事

- 沒有改 `slides.md`、`theme.css`、`index.html`，也沒有動任何 code 分支。
- 沒有裝 LibreOffice 或 Chrome。
