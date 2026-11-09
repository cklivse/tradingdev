# 第 33 輪（2026-11-09）：統計模組簡報草稿

草稿位置：本分支 `talks/statistics-module/`（`slides.md` 和 `theme.css`）。
`theme.css` 從 main `ad2fb75` 的 `docs/talks/tradingdev-introduction/theme.css` 原檔複製
（sha256 `7236184340bf…f8f9`，兩邊相同）。
沒有動 `docs/talks/tradingdev-introduction/` 的任何檔案，沒有開 PR、沒有留言，也沒有推到任何
stats 或 feat 分支。

> 註：session-notes 已經有一份 11-08 的 `2026-11-08-round33-repro-method/`（commit bb618d7）。
> 這次依指示也標第 33 輪，檔名用日期和主題區分。

## 結論

- 新 talk 共 30 頁，三部分的內容頁是 4：12：7（另有封面、閱讀路線、三個章首頁、結語與參考資料）。
- **`scripts/presentations.sh` 不能 build 或 check 這份新簡報**：`tooling/presentations.py` 的
  `DECK = "docs/talks/tradingdev-introduction"` 是寫死的，五個動作都只處理介紹簡報。
  所以我用同一套鎖定工具鏈的 `tooling/marp/build.mjs` 直接編譯，再呼叫 repo 自己的檢查函式
  （見「驗證」）。
- `setup` 成功。現有介紹簡報的 `check` 失敗：Mermaid 需要 Chrome，這台機器沒有。依指示沒有安裝。
  新簡報沒有 Mermaid，所以編譯不需要瀏覽器。
- 有兩處你的大綱和程式不一致，簡報照程式寫（見「需要你決定的地方」）。

## 任務 1 回報

### 1. slides.md 的分頁與 directive 語法

- 檔頭是 HTML 註解形式的 front-matter：

  ```markdown
  <!--
  marp: true
  theme: tradingdev
  size: 16:9
  paginate: true
  lang: zh-Hant
  title: …
  -->
  ```

- 分頁用單獨一行 `---`。
- 單頁 directive 加底線前綴，只作用在該頁：`<!-- _class: chapter -->`、`<!-- _header: "" -->`、
  `<!-- _footer: "來源：[…](…)" -->`。class 可以疊加，例如 `<!-- _class: compact diagram-wide -->`。
- 不加底線的 directive 從該頁起一直有效，例如章首頁的
  `<!-- header: "01　系統架構" -->` 搭配 `<!-- _header: "" -->`（章首頁本身不顯示頁首）。
- 其餘 HTML 註解是講者備註，介紹簡報用它放來源，例如
  `來源：https://github.com/Kuan-Lun/tradingdev/blob/9e502ce/ARCHITECTURE.md`。
- theme.css 實際定義的 class 有 `cover`、`chapter`、`compact`、`closing`、`references`、`diagram-wide`
  和 `case-*` 系列。README 提到 `statement`，但 main 的 theme.css 沒有它的樣式，所以新簡報沒有用它。

### 2. 介紹簡報「01 系統架構」已涵蓋的主題

這一節在附加的第二部分（main 的 slides.md 第二個「01」章），共 6 頁：

1. 章首頁：MCP 研究後端、不綁定 LLM 供應商、不真實下單
2. 系統模組與責任：MCP 工具／Application services／Domain／Adapters／Workspace
3. 外部訊號流程（Mermaid）：使用者、AI 代理、TradingDev
4. 內部訊號流程（Mermaid）：MCP、App、Plan、Worker、Store、Result
5. MCP 工具覆蓋研究流程：Strategy、Execution、Data 與 Jobs、Runs 與 Artifacts、ML
6. Application services 協調工作：StrategyService、ExecutionPlanService 等

後面的「04 現況與邊界」還有一頁講 `domain/statistics`。PR #209 也改了這一頁（見下）。

### 3. 引用的 ARCHITECTURE.md commit 和 main 的差距

- 「01 系統架構」一節只引用 **`9e502ce`**（2026-11-07）。整份簡報其他地方另有 `cd95d60`（README／ARCHITECTURE
  的頁尾）、`7e7a997`（頁尾）和 `35d709d`（README）。
- 現在的 main 是 upstream `ad2fb75`（PR #215 合併）。fork 的 main 還停在 `1ea5276`。
- `9e502ce..ad2fb75` 有 136 個 commit，其中 6 個改過 ARCHITECTURE.md（+31／−5）：0eb1370、cf66214、2893047、
  0b21e81、3be69ff、2312d6d。
- 差異內容：
  - 新增 `tooling/environment.py`、`tooling/llm_check.py` 兩列
  - CLI 改稱「直接回測 CLI」，並註明 `tradingdev-codex` 走 MCP 流程
  - 新增 `ArtifactService.read_download` 和 MCP `ArtifactDownloads` 的短效網址
  - 新增「可見對話紀錄」一節
- **四層的責任表沒有變**，所以介紹簡報那節的模組表仍然成立。
- 對照其他引用：`cd95d60..ad2fb75` 有 527 個 commit（+165／−18），`7e7a997..ad2fb75` 有 298 個（+136／−18）。

## 任務 2：setup 原文輸出

在 main `ad2fb75` 的 scratchpad worktree 執行（先跑過 `uv sync --locked --all-extras` 建立該 worktree 的 `.venv`）：

```text
$ scripts/presentations.sh setup
Locked presentation compiler installed.
exit=0
```

環境：`node` v24.21.0、`npm` 11.19.0；`google-chrome`、`chromium`、`chromium-browser` 都不在 PATH。

接著對現有介紹簡報跑 `scripts/check-presentations.sh`，失敗輸出如下（原文照抄，只把 scratchpad 路徑縮寫成 `<SP>`）：

```text
Presentation checks failed: Presentation compiler failed (1):
[  INFO ] Converting 1 markdown...
[  INFO ] ../claude-1000/<SP>/main-ad2fb75/docs/talks/tradingdev-introduction/slides.md => index.html.building-6360
file:///tmp/claude-1000/<SP>/main-ad2fb75/tooling/marp/render-diagrams.mjs:94
      throw new Error('Mermaid rendering requires Chrome. Install Chrome or set '
            ^

Error: Mermaid rendering requires Chrome. Install Chrome or set TRADINGDEV_PRESENTATION_BROWSER to a Chromium executable.
    at renderDiagrams (file:///tmp/claude-1000/<SP>/main-ad2fb75/tooling/marp/render-diagrams.mjs:94:13)
    at async file:///tmp/claude-1000/<SP>/main-ad2fb75/tooling/marp/build.mjs:29:22 {
  [cause]: Error: Could not find Google Chrome executable for channel 'stable' at:
   - /opt/google/chrome/chrome.
      at computeSystemExecutablePath (…/node_modules/@puppeteer/browsers/lib/esm/launch.js:50:11)
      at ChromeLauncher.executablePath (…/node_modules/puppeteer-core/lib/esm/puppeteer/node/ChromeLauncher.js:208:20)
      at ChromeLauncher.computeLaunchArguments (…/node_modules/puppeteer-core/lib/esm/puppeteer/node/ChromeLauncher.js:85:24)
      at async ChromeLauncher.launch (…/node_modules/puppeteer-core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
      at async renderDiagrams (file:///tmp/claude-1000/<SP>/main-ad2fb75/tooling/marp/render-diagrams.mjs:92:17)
      at async file:///tmp/claude-1000/<SP>/main-ad2fb75/tooling/marp/build.mjs:29:22
}

Node.js v24.21.0

Markdown formatting and local links passed (28 documents).
SRS structure and references passed (31 requirements).
exit=1
```

依指示沒有安裝 Chrome，也沒有設定 `TRADINGDEV_PRESENTATION_BROWSER`。`build.mjs` 只在 HTML 裡有
`language-mermaid` 區塊時才啟動瀏覽器，所以沒有 Mermaid 的新簡報可以編譯。

### `tooling/presentations.py` 的 `main()`：五個動作各做什麼

| 動作 | 行為 |
| --- | --- |
| `setup` | 確認有 Node／npm，在 `tooling/marp` 執行 `npm ci --ignore-scripts --no-audit --no-fund`，再核對安裝結果與 lock 相符 |
| `build` | 核對工具鏈，用 `build.mjs` 在臨時目錄編譯 `DECK` 的 slides.md／theme.css，執行 `check_html`，寫回 `DECK/index.html` |
| `watch` | 每 0.5 秒比對 slides.md、theme.css，有變更就 `build`；失敗時印出錯誤並繼續監看 |
| `check` | `check_environment("docs")`、工具鏈、Node、`check_documents`，再於臨時目錄建置整包並執行 `check_html` 與 `check_bundle` |
| `package` | 同 `check` 的前置檢查，建置整包後寫出資料夾和同名 ZIP；輸出必須在 `DECK` 之外 |

以上五個動作都綁在 `DECK` 常數上。另外 `build.mjs` 把 `--title`、`--description` 寫死成介紹簡報的值，
所以新簡報編譯出來的 `<title>` 是「TradingDev｜能學習策略開發經驗、自我演進的研究後端」，不是
front-matter 寫的「TradingDev｜統計模組」。

## 驗證（新簡報）

都在 main `ad2fb75` 的 worktree 執行，用的是同一套鎖定工具鏈與 repo 的檢查函式，沒有修改任何 repo 檔案：

| 檢查 | 結果 |
| --- | --- |
| `node tooling/marp/build.mjs slides.md theme.css index.html` | exit 0 |
| `tooling.presentation_html.check_html` | 通過，30 頁 |
| `tooling.presentation_bundle.check_bundle` | 通過 |
| `python -m pymarkdown -d MD013 scan slides.md`（同 `check_documents` 的參數） | exit 0 |
| `tooling.documentation.check_local_links` | 通過 |

**未驗證**：

- 瀏覽器視覺排版（文字溢出、表格密度）。沒有瀏覽器可用，也沒有安裝。
- 下列頁面內容較密，最可能溢出：「介紹簡報引用的架構版本之後的變化」、「怎麼選」、「介面上還缺的東西」、
  「為什麼需要 `_validation` 和 `_scaling`」、「三條不可混用的規則」。
- 沒有安排獨立 reviewer。依 AGENTS.md，簡報變更不強制模型審查。所有數字與行為都在撰寫時對照下列程式和文件逐條核對過。

## 引用版本

引用一律釘 commit，不指向分支：

- main：`Kuan-Lun/tradingdev` `ad2fb75`
- 統計程式（fork `cklivse/tradingdev`，各 PR 2026-11-09 的 head）：
  - `stats/1-foundation` `c8154a8`（#206）
  - `stats/2-breakeven` `fc62da5`（#207）
  - `stats/3-plateau` `dfb383d`（#208）
  - `stats/4-sharpe` `bede2d0`（#209）
  - `stats/5-comparison` `a216dc4`（尚未開 PR）
- Issue 和 PR 用編號連結；它們沒有 commit 可釘。

## 簡報大綱（30 頁）

| 頁 | 標題 | 部分 |
| --- | --- | --- |
| 1 | 統計模組（封面） | — |
| 2 | 閱讀路線 | — |
| 3 | 01　架構：統計模組的位置（章首頁） | 架構 |
| 4 | 四層分工 | 架構 |
| 5 | 為什麼統計模組只在 domain | 架構 |
| 6 | 和主線績效管線的界線 | 架構 |
| 7 | 介紹簡報引用的架構版本之後的變化 | 架構 |
| 8 | 02　統計模組（章首頁） | 統計 |
| 9 | 模組地圖 | 統計 |
| 10 | `periods`：權益曲線怎麼切成日和月 | 統計 |
| 11 | `performance`：從原始輸出重算一次績效 | 統計 |
| 12 | `breakeven`：成本吃掉多少，勝率還夠不夠 | 統計 |
| 13 | `sharpe`（一）：這個 Sharpe 有多不確定 | 統計 |
| 14 | `sharpe`（二）：是真的嗎？從 N 個裡挑最好的還算嗎？ | 統計 |
| 15 | `comparison`：A 真的比 B 好嗎 | 統計 |
| 16 | `plateau`：穩定高原還是運氣好的尖峰 | 統計 |
| 17 | `benchmark`：相對買進持有多了什麼 | 統計 |
| 18 | 為什麼需要 `_validation` 和 `_scaling` | 統計 |
| 19 | 怎麼選：從問題到方法 | 統計 |
| 20 | 三條不可混用的規則 | 統計 |
| 21 | 03　現況與邊界（章首頁） | 現況 |
| 22 | 拆分狀態 | 現況 |
| 23 | 為什麼拆 | 現況 |
| 24 | 介面上還缺的東西 | 現況 |
| 25 | #189：搜尋規模沒有跟著代表結果 | 現況 |
| 26 | #190：分不出訊號是誰算的 | 現況 |
| 27 | 修不掉的限制：配對紀錄不是 holdout | 現況 |
| 28 | 目前不能說的事 | 現況 |
| 29 | 統計模組的定位（結語） | — |
| 30 | 參考資料 | — |

內容頁比重是架構 4、統計 12、現況 7，約等於 2：5.2：3。

## 需要你決定的地方

1. **`performance` 沒有年化報酬和波動**。你的大綱寫「年化報酬、波動、Sharpe、最大回撤」，但
   `PerformanceSummary`（`bede2d0`）只有：
   - `total_pnl`、`total_return`
   - 日／月 P&L 的平均與樣本標準差（金額）
   - `sharpe_ratio`
   - `max_drawdown`（金額）、`max_drawdown_pct`
   - 交易統計

   第 11 頁照程式寫，並明說沒有這兩個欄位。
2. **`benchmark` 的「超額報酬」**。模組 docstring 把「excess return」保留給總報酬差（報告裡產品基準那一個），
   模組本身算的是 `active_return_annualised`（主動報酬）。第 17 頁用這個名稱，沒有寫「超額報酬」。
3. **PR #209 改了 Kuan-Lun 那份簡報**。`stats/4-sharpe` 上 Kuan-Lun 自己的 commit（bb13cc2、471cedc、db2bdda）
   把介紹簡報 04 章的「主線績效與 PR #38 擴充」改成「績效管線與獨立統計 API」。新簡報沒有碰它。
   兩份簡報合併後對統計模組的說法要一致，這點你可能要和 Kuan-Lun 對一下。
4. **工具鏈只認一份簡報**。要讓新 talk 進 repo 並用 `presentations.sh`／`check-presentations.sh` 檢查，
   需要改 `tooling/presentations.py`（`DECK`、`PRESENTATION_PATHS`）和 `build.mjs` 的寫死標題。
   這是開發工具變更，不在這次授權內，我沒有做。
5. **其他現況**（簡報第 22 頁已寫）：
   - #206–#209 已經不是 draft，Kuan-Lun 今天在四個分支上都推了型別和 docstring 修正。
   - PR 內文仍寫「verified at `main` c246355」。
   - 第 5 包的基底是 `b62ac97`，不含 #209 目前的 head。開 PR 前要先同步。
