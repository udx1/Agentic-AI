# Frontend

Stack: React with Vite.

## Setup

Install dependencies:

```powershell
npm install
```

Run the local UI:

```powershell
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Build for production:

```powershell
npm run build
```

## Current Scope

- Product listing page
- Product detail view
- Product cards
- Basic responsive layout
- Department navigation
- Search
- Sorting
- Local cart panel with quantity controls

The UI loads product and category data from the FastAPI backend.

Default API base URL:

```text
http://127.0.0.1:8000
```

Override it with:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```
