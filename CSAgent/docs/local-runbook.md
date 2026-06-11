# Local Runbook

Use these commands to start, stop, and check the local CSAgent app.

## Start Backend

```powershell
cd C:\Users\uday0\Documents\GenAIAcademy\Agentic-AI\CSAgent\backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

## Start Frontend

```powershell
cd C:\Users\uday0\Documents\GenAIAcademy\Agentic-AI\CSAgent\frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Customer UI:

```text
http://127.0.0.1:5173/
```

Eval/developer evidence mode:

```text
http://127.0.0.1:5173/?_m=e
```

Internal support-ticket console:

```text
http://127.0.0.1:5173/?_m=s#/support/tickets
```

## Stop Foreground Servers

In each terminal where a server is running:

```powershell
Ctrl + C
```

## Stop Background Servers

Find the process ID by port:

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

Stop the matching process:

```powershell
Stop-Process -Id <PID>
```

## Quick Validation

Backend support-agent validation:

```powershell
cd C:\Users\uday0\Documents\GenAIAcademy\Agentic-AI\CSAgent\backend
uv run python ..\rag_pipeline\validate_support_agent.py
```

Ticket workflow validation:

```powershell
cd C:\Users\uday0\Documents\GenAIAcademy\Agentic-AI\CSAgent\backend
uv run python ..\rag_pipeline\validate_ticket_workflow.py
```

Frontend production build:

```powershell
cd C:\Users\uday0\Documents\GenAIAcademy\Agentic-AI\CSAgent\frontend
npm run build
```
