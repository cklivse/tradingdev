# 2026-10-24 第五輪：釘死 KD 輸入與 fixture（WIP，依要求中途停止）

## 狀態

- **WIP 分支：** `feat/stats-pinned-fixtures` 從 `feat/stats-py314`（`610e612`）分出，有一個 WIP commit `49de1b7`，已 push 到 origin。沒有開 PR。
- **WIP 而非 stash：** AGENTS.md 明文禁止 stash；commit 之後工作樹是乾淨的。
- **PR #38 未受影響：** `feat/stats-py314`、`origin/feat/stats-py314` 和 PR #38 的 head 都仍是 `610e612`，沒有追加任何 commit。
- **背景程序：** 沒有殘留的 pytest、optimization worker 或 keepalive。
- **沒有跑：** check-full 和獨立審查。

## 已完成（在 49de1b7 裡）

- **demo 的輸入釘死（任務 1）：**
  - `latest_cache()` 已移除。預設讀 `KD_SOURCE`（`cd03bf19459b48af.pkl`），並核對 `KD_SOURCE_SHA256`（`b9493b6b…6febd0`）。檔案不存在或雜湊不符就直接停止，不會改挑別的檔案。
  - 要用別份回測，必須明確傳 `--kd-pickle PATH`。
  - `kd_inference.md` 現在記錄 `Source SHA-256`。重新產生後，唯一的差異就是新增這一行。
- **validate_run：** 改成必須明確指定路徑，原本是挑字典序最後一個檔案。另外拆出 `validate(pr)` 給測試用，每次執行都會清空結果。
- **fixture（任務 2）：** 放在 `tests/domain/statistics/fixtures/kd_btcusdt_1h_2024/`。
  - `equity.parquet`：11,405 bytes，8,761 根小時權益與 UTC 時間戳。
  - `trades.parquet`：26,232 bytes，412 筆交易，欄位是 size_quote、entry_price、exit_price、net_pnl、fee、exit_notional、status。
  - `run.json`：1,918 bytes，來源、設定，以及引擎的 33 個指標。
  - 另有 `README.md` 和 `extract.py`。資料合計 39,555 bytes。
  - 格式選 Parquet zstd：時間戳用 delta 編碼、權益用 dictionary 編碼，round trip 逐位元精確。未調參數的 Parquet 約 86 KB；csv.gz 雖然只有 29 KB，但浮點數要小心格式化才能精確 round trip。
- **兩份來源：**
  - 原始序列來自 `cd03bf`。
  - 只有目前引擎才有的欄位（fee、exit_notional、status、metrics）來自 `cli_5ed5…pkl`。兩份 pickle 的權益曲線逐位元相同，時間戳與 4 個交易欄位也完全一致，`extract.py` 寫檔前會先檢查這些。
  - 只用 `cd03bf` 做不到任務 4：它的 trade 沒有 `exit_notional`，也沒記錄 fee；metrics 用的是舊慣例。
- **測試（任務 3、4）：** 統計測試加 validate_run 測試共 336 passed。
  - 三個數字以 rel 1e-9 和 PR 的全精度值比對，並檢查它們在 `kd_inference.md` 的顯示形式。
  - 日報酬筆數固定為 366。
  - validate_run：24 項全 PASS、exit 0；V3 對非負值判 PASS、對負值判 FAIL；成本占比 86%，不是 173%；CLI 沒給路徑時 exit 2。

## 還差什麼才算完整

1. **check-fast 還有兩個 strict mypy 錯誤：**
   - `extract.py` 匯入的 `pyarrow.parquet` 沒有型別 stub。
   - `test_statistics_kd_fixture.py` 有一個標成 `-> float` 的 helper 回傳 Any。
2. **獨立審查**，並套用修正。
3. **check-full**：審查修正都套用之後，開 keepalive 跑一次。
4. **WIP commit 的處理：** 在新的完整 commit 中修正，或改寫掉這個 WIP commit。這個分支已經 push 過，改寫歷史要先問使用者。

## 也存進 session-notes 的東西

- `tools/`：MCP stdio client（`mcp_call.py`、`read_scopes.py`），以及數字驗證腳本 `verify.py`。
- `evidence/2026-10-24-trial-scope/`：真實搜尋的 prepare 參數、submit 回應、15 個 trial scope 的原始 JSON（gzip）。
