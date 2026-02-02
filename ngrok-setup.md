## Guida completa: ngrok con frontend + backend su una sola porta (Windows)

Questa guida spiega come esporre in pubblico il progetto **da locale**, unendo
frontend e backend dietro **un unico URL** tramite un proxy locale.

## Prerequisiti
- Account ngrok attivo con token di autenticazione.
- Node.js + pnpm installati.
- Python installato (per il backend).

## Step 1) Installa ngrok
1. Vai su `https://dashboard.ngrok.com/get-started/setup/windows`
2. Scarica il binario per Windows.
3. Estrai `ngrok.exe` e spostalo in una cartella stabile, es. `C:\Tools\ngrok`.

## Step 2) Verifica ngrok dal terminale
Apri PowerShell e prova:
```powershell
ngrok version
```
Se non funziona:
- chiudi e riapri PowerShell (serve per ricaricare il `PATH`), oppure
- usa il comando con percorso completo:
```powershell
C:\Tools\ngrok\ngrok.exe version
```

## Step 3) Configura il token di ngrok
Nel terminale esegui:
```powershell
C:\Tools\ngrok\ngrok.exe config add-authtoken <IL_TUO_TOKEN>
```
Non condividere mai il token in chat o ticket pubblici. Se lo hai esposto, revocalo e rigeneralo.

## Step 4) Avvia il backend (porta 8000)
Questo e` l’equivalente del tuo start su Render:
```powershell
cd backend
pip install -r electronics_server_python/requirements.txt
uvicorn electronics_server_python.main:app --host 0.0.0.0 --port 8000
```
Lascia questo terminale aperto.

## Step 5) Avvia il frontend (porta 5173)
In un nuovo terminale:
```powershell
cd frontend
pnpm install
pnpm build
pnpm serve
```
Lascia questo terminale aperto.

## Step 6) Installa un proxy locale (Caddy)
Serve un proxy per unire frontend e backend dietro un’unica porta.

1. Installa Caddy (puoi scaricare il binario da `https://caddyserver.com/download`).
2. Crea un file chiamato `Caddyfile` in una cartella a tua scelta, con questo contenuto:
   ```txt
   :8080 {
     reverse_proxy /sse* localhost:8000
     reverse_proxy /api/* localhost:8000
     reverse_proxy localhost:4444
   }
   ```
   Questo instrada:
   - `/api/*` -> backend (8000)
   - tutto il resto -> frontend (4444)

## Step 7) Avvia il proxy (porta 8080)
Apri un nuovo terminale **nella cartella dove hai il `Caddyfile`** ed esegui:
```powershell
C:\Tools\caddy\caddy.exe run --config C:\Tools\caddy\Caddyfile
```

oppure

```powershell
cd ..
cd ..
cd tools 
cd caddy
.\caddy run 
```

Ora il tuo sito locale e` su `http://localhost:8080`.

## Step 8) Esporre la porta 8080 con ngrok
In un quarto terminale:
```powershell
C:\Tools\ngrok\ngrok.exe http http://localhost:8080
```
oppure

```powershell
cd ..
cd ..
cd tools 
cd ngrok
.\ngrok http http://localhost:8080
```
Otterrai un URL pubblico del tipo:
`https://<qualcosa>.ngrok-free.app`

## Step 9) Verifica finale
- Apri l’URL ngrok nel browser.
- Il frontend deve caricarsi.
- Le chiamate al backend devono passare su `/api`.

## Troubleshooting (errori comuni)
**`ngrok` non riconosciuto**
- Usa sempre il percorso completo: `C:\Tools\ngrok\ngrok.exe ...`

**PowerShell non esegue comandi nella cartella corrente**
- Se sei nella cartella di ngrok, usa `.\ngrok ...`

**Il link ngrok cambia**
- Nel piano free l’URL cambia ad ogni riavvio.

**Come trovare il PID di Caddy (porta 2019)**
```powershell
netstat -ano | findstr :2019
```
Se vuoi chiudere Caddy, prendi il PID e fai:
```powershell
taskkill /PID <PID> /F
```

**Come verificare se un host/porta e` attivo**
```powershell
curl http://localhost:8000
curl http://localhost:4444
curl http://localhost:8080
```

## Comandi rapidi (riassunto)
```powershell
cd backend
pip install -r electronics_server_python/requirements.txt
uvicorn electronics_server_python.main:app --host 0.0.0.0 --port 8000
cd ..\frontend
pnpm install
pnpm build
pnpm serve
caddy run
C:\Tools\ngrok\ngrok.exe http http://localhost:8080
```

## 1) Vai nella cartella
```powershell
cd C:\Projects\electronics_demo
```
## Avvia tutto

```powershell
.\start-local-terminals.ps1
```

oppure

```powershell
.\start-local-terminals.ps1 -BackendBuild
```

oppure

```powershell
.\start-local-terminals.ps1 -FrontendBuild
```
oppure

```powershell
.\start-local-terminals.ps1 -BackendBuild -FrontendBuild
```
 # Se Caddy / ngrok non sono nel PATH

 Imposta i percorsi solo per questa sessione:
 ```powershell
$env:CADDY_PATH="C:\Tools\caddy\caddy.exe"
$env:NGROK_PATH="C:\Tools\ngrok\ngrok.exe"
$env:motherduck_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImhyQHhlZWwudGVjaCIsIm1kUmVnaW9uIjoiYXdzLXVzLWVhc3QtMSIsInNlc3Npb24iOiJoci54ZWVsLnRlY2giLCJwYXQiOiJnSUVKOUVPcHA4RnExOUx1NktKZUhwYk44Zk9aN0N1WV9VR0Y4djgteDFRIiwidXNlcklkIjoiODA3MDM5ZDMtMzA3Ny00ZGY1LWEyZTMtMTk4ZGYzMTMzMTNkIiwiaXNzIjoibWRfcGF0IiwicmVhZE9ubHkiOmZhbHNlLCJ0b2tlblR5cGUiOiJyZWFkX3dyaXRlIiwiaWF0IjoxNzY3NjEzMTUwfQ.Y4_OIRpyrcSelw3_XH0mVip71Ram7czigIrzK7pa9tQ"
```


## Kill globale 
```powershell
taskkill /IM node.exe /F
taskkill /IM python.exe /F
taskkill /IM uvicorn.exe /F
taskkill /IM caddy.exe /F
taskkill /IM ngrok.exe /F
```

oppure

```powershell
.\stop-local-terminals.ps1
```
Eseguilo da **PowerShell** nella root del progetto.

```powershell
uvicorn main:app --app-dir pizzaz_server_python --host 0.0.0.0 --port 8000 --reload
```

## Per far partire il backend

```powershell
python main.py
```