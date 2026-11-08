# 第 28 輪：開 PR

日期：2026-11-08。依指示由我開 PR，全部開在 Kuan-Lun/tradingdev，base 是 `main`。沒有在 #189／#190 留言，沒有動任何分支的程式。

| PR | head | 狀態 | commit | 檔案 |
| --- | --- | --- | --- | --- |
| #205 | `cklivse:docs/readme-final-evaluation-data`（a68f1e4） | ready | 1 | `README.md` +5 |
| #206 | `cklivse:stats/1-foundation`（69ecbda） | ready | 1 | 5 |
| #207 | `cklivse:stats/2-breakeven`（5ea494d） | draft | 2（含 #206 的 69ecbda） | 7 |
| #208 | `cklivse:stats/3-plateau`（b1dac02） | draft | 4（含 69ecbda） | 8 |
| #209 | `cklivse:stats/4-sharpe`（ebac927） | draft | 2（含 69ecbda） | 11 |

開完後 GitHub 對五個 PR 都顯示 `MERGEABLE`。

## body 和指示不同的地方

- **第 1 包用的是 7ac57a2 的版本，不是 eeec723 報告附錄那份**。eeec723 那份的清單連結還指向分支，第 27 輪任務 1 才改成釘到 commit eeec723 的網址。兩者只差那個連結。
- **第 1 包刪掉了「The split was agreed on #38 (<AGREEMENT_URL>)」這一句**。開 PR 前發現連結沒填，問過後依你的選擇整句刪掉。
- **第 2–4 包沒有另外加 Depends on 那一行**。三份 body 原本就有「Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.」，我把 `#<P1>` 換成 #206，沒有再加一行，以免重複。

## 第 5 包

還沒開，等 #209 合併。body（`2026-11-07-round22-pr-bodies/pr5-comparison.md`）已經把 `#<P1>` 換成 #206、`#<P4>` 換成 #209，沒有其他佔位符。開之前，驗證段的 `main` SHA 要看當時的 `main` 重驗。
