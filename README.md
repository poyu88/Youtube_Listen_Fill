# YouTube 聽打練習

透過 YouTube 影片進行英文聽力與拼寫（挖空）練習的 Web 應用。

## 技術栈

- 後端：FastAPI + yt-dlp（`uv`）
- 前端：React + Vite + TypeScript

## 啟動

### 後端

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

瀏覽器開啟 http://localhost:5173 。前端會透過 Vite proxy 轉發 `/api` 至後端。

## 使用說明

1. 在首頁貼上有英文字幕的 YouTube URL 並匯入
2. 點進影片進入練習頁
3. 使用分段列表或左右箭頭切換句子，調整速度與循環／單次模式
4. 在填空區聽打；可使用 Hint／Check Answer／Show Translation（翻譯為預留）
