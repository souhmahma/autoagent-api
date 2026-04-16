# AutoAgent Frontend

Interface React pour l'API AutoAgent — design terminal dark avec Syne + JetBrains Mono.

## Stack

- **React 18** + React Router v6
- **Vite** (build ultra rapide)
- **CSS Modules** (zéro dépendance UI)
- **Axios** avec intercepteur JWT auto-refresh

## Lancer en développement

```bash
cd autoagent-frontend
cp .env.example .env
npm install
npm run dev
```

> L'API FastAPI doit tourner sur `http://localhost:8000`
> Le proxy Vite redirige `/api/*` → `http://localhost:8000/*`

## Build production

```bash
npm run build
# Les fichiers sont dans /dist
```

## Pages

| Route | Description | Auth |
|-------|-------------|------|
| `/login` | Login + Register | Public |
| `/` | Terminal agent (ReAct) | ✅ |
| `/sessions` | Historique sessions | ✅ |
| `/admin` | Panel admin | 👮 admin only |

## Structure

```
src/
├── context/
│   └── AuthContext.jsx     # Auth globale + JWT
├── services/
│   └── api.js              # Axios + intercepteurs
├── components/
│   ├── Layout.jsx           # Sidebar + nav
│   └── Layout.module.css
├── pages/
│   ├── Auth.jsx             # Login / Register
│   ├── Terminal.jsx         # Agent terminal
│   ├── Sessions.jsx         # Historique
│   └── Admin.jsx            # Panel admin
├── App.jsx                  # Routing
├── main.jsx
└── index.css                # Design system global
```
