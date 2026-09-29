# Junba AI Transcriber v2.3

Windows 10/11 繁體中文 GUI：離線 `faster-whisper` + Google Gemini 3.5 Transcribe + M4A 切割/合併 + TXT/SRT/VTT/Word。

## v2.3 修正重點

- **修正 Google Gemini 中文檔名上傳錯誤**：v2.2 會把中文/日文檔名直接交給 SDK multipart 上傳，在部分 Windows HTTP 路徑會出現 `UnicodeEncodeError: 'ascii' codec can't encode...`。v2.3 保留原始檔名與輸出檔名，但上傳時自動建立 ASCII 安全暫存別名，完成後刪除。
- 設定頁保留「前往取得 API Key」，並把原本只查 `/models` 的測試升級成 **「完整測試 API Key（含音訊上傳）」**：程式會自動建立約 0.5 秒測試 WAV，上傳 Google，並呼叫 `gemini-3.5-transcribe`，可更早發現 API / Files API / 模型存取問題。
- **切割優先**：只要切割分鐘數大於 0，程式會先完成切割，再載入 Whisper 或上傳 Gemini，不會一邊辨識才臨時切。
- 新增「只切割音檔」與「開啟切割資料夾」。切割結果保存到 `輸出位置\切割音檔\...`，可直接拿給其他辨識軟體使用。
- 切割結果有 manifest；來源檔、大小、修改時間與切割分鐘未變時會直接重用，不會再次切割。
- 加入音檔後主動詢問：不切割 / 2 / 5 / 10 / 15 / 30 / 60 / 自訂分鐘。
- 修正進度顯示：先顯示切割進度，再顯示模型載入 / 上傳 / 轉錄 / 匯出；整體進度不再只在整段完成後跳動。
- Google Gemini 模式使用 `gemini-3.5-transcribe`。啟用 speaker diarization 或 word timestamps 時，若音檔過長會自動限制為最多 30 分鐘一段；未啟用這兩項時最多 60 分鐘一段。
- 混合模式：Whisper 本機轉錄，再把「文字」交給 Gemini 整理；音訊不上傳。

## 關於「切割會不會更快」

切割主要解決：

1. 避免單檔過大 / 時長上限。
2. 某一段失敗時只重跑那一段。
3. 可以先切好，再拿去其他辨識軟體使用。
4. 降低長檔一次失敗造成全部重來的風險。

對 **離線 Whisper**，切割本身不保證總推論時間一定縮短，因為同樣的音訊仍要運算；但通常會讓長檔工作更穩定、容易續跑。線上 Gemini 若未來加入多段平行請求，才會進一步利用切割提升總吞吐量。

## GitHub Actions 驗證

`.github/workflows/build-windows-v2.3.yml` 會在 `windows-latest`：

1. 安裝 Python 3.11 x64 與 requirements。
2. `compileall` + 套件 import smoke test。
3. 跑 pytest：FFmpeg、Unicode 中文檔名切割、切割快取重用、Gemini ASCII 上傳別名測試。
4. 建立 Single EXE。
5. 在 Windows runner 實際執行 Single EXE `--self-test`。
6. 建立 Portable EXE。
7. 在 Windows runner 實際執行 Portable EXE `--self-test`。
8. 只有自我檢查通過才上傳 Artifact。

> GitHub CI 無法替使用者持有 Gemini API Key，因此「實際連 Google」由程式設定頁的「完整測試 API Key（含音訊上傳）」完成。

## 使用方式

1. 加入或拖曳音檔。
2. 加入後選擇切割分鐘數；若只想先切檔，按「只切割音檔」。
3. 選擇離線 Whisper / Google Gemini / 混合模式。
4. Google 模式先到「設定」儲存 API Key，再按「完整測試 API Key（含音訊上傳）」。
5. 按開始。若設定切割，程式先完成切割，再開始辨識。
6. 觀察「目前階段 %」「整體進度 %」與執行紀錄。

## 完全離線 large-v3

`large-v3` 不內嵌在 EXE。第一次可讓 faster-whisper 下載，或先執行 `download_large_v3.bat`，之後在 GUI 指定 `models\large-v3`。指定本機模型後即可斷網轉錄。

## 隱私

- 離線 Whisper：音訊不離開電腦。
- 混合模式：音訊不離開電腦，只把 Whisper 產生的文字送至 Gemini。
- Google Gemini：音訊會上傳 Google API；v2.3 上傳完成後會盡力刪除該次 Files API 暫存檔。
