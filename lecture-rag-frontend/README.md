# Lecture Assistant Frontend (React)

Simple chat UI for the lecture assistant. Sends prompts and conversation history to the FastAPI backend and renders responses.

## Project structure

```
lecture-rag-frontend/
├─ src/
│  ├─ App.js        # Chat UI
│  ├─ api.js        # Backend client
│  ├─ config.js     # Base URL + timeouts
│  └─ styles...
├─ public/
├─ package.json
└─ README.md
```

## Prerequisites

- Node.js 18+ and npm
- Running backend (default expected at `http://localhost:8000`)

## Quick start

```bash
npm install
npm start
```
The app runs at http://localhost:3000.

To point at a different backend, edit `src/config.js`:
```js
const CONFIG = {
  API_BASE_URL: "https://your-cloud-run-url",
  TIMEOUT_MS: 15000,
};
export default CONFIG;
```

## Build and deploy

```bash
npm run build
```
Outputs a production build to `build/`. Host it on any static site host (Cloud Storage + CDN, Netlify, Vercel, etc.). Ensure `API_BASE_URL` is reachable from the client.

## Testing

```bash
npm test
```
Runs React Testing Library tests in watch mode.
