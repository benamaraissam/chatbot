# chatbot-react-library

Librairie React portable pour intégrer un chatbot flottant (SSE streaming, protocole v1 aligné avec `chatbot-python-library`).

## Stack

- Vite (library mode) + TypeScript
- Tailwind CSS (`cb-` prefix, scoped `.cb-root`)
- Zustand
- `fetch` + ReadableStream (SSE)
- react-markdown + remark-gfm
- shiki (lazy-loaded code highlight)
- framer-motion
- lucide-react

## UI features (modern chat patterns)

- **Streaming** — plain text + blinking cursor while tokens arrive; markdown renders after the turn completes (avoids layout flicker)
- **Thinking state** — animated indicator before the first token or tool
- **Tool calls inline** — cards under the assistant avatar, linked to the message; status icons (running / done / error / approval)
- **Streaming tool input** — shows `inputRaw` JSON as it arrives
- **Human-in-the-loop** — Approve / Deny when the backend emits `tool_approval_required` (+ optional `onToolApproval`)
- **Suggested prompts** — empty-state chips (`suggestions` prop)
- **Copy** — assistant messages
- **Accessibility** — `aria-live` region during streaming

## Install from npm (public)

Once published:

```bash
npm install chatbot-react
```

Peer dependencies (install in your app if missing):

```bash
npm install react react-dom
```

Import the bundle **and** styles:

```tsx
import { ChatbotProvider, FloatingChatbot } from "chatbot-react";
import "chatbot-react/styles.css";
```

## Install locally (another project on your machine)

Use this while developing the library or before publishing to npm.

### 1. Build the library

```bash
cd chatbot-react-library
npm install
npm run build
```

The `files` field in `package.json` only ships `dist/`, so **`npm run build` is required** before linking or packing.

### 2. Link into your app (good for active development)

In the library folder:

```bash
npm link
```

In your React app:

```bash
npm link chatbot-react
```

Your app must still import `chatbot-react/styles.css`. If you change library source, run `npm run build` again in `chatbot-react-library`.

To unlink:

```bash
# in your app
npm unlink chatbot-react
# in chatbot-react-library
npm unlink
```

### 3. Install from a local path (good for CI / monorepo-style)

In your app `package.json`:

```json
{
  "dependencies": {
    "chatbot-react": "file:../chatbot-react-library"
  }
}
```

Then:

```bash
cd ../chatbot-react-library && npm run build
cd ../your-app && npm install
```

### 4. Install from a tarball

```bash
cd chatbot-react-library
npm run build
npm pack
# creates chatbot-react-0.1.0.tgz

cd ../your-app
npm install ../chatbot-react-library/chatbot-react-0.1.0.tgz
```

## Publish to npm (public registry)

1. **Create an npm account** at [https://www.npmjs.com](https://www.npmjs.com) and log in:

   ```bash
   npm login
   ```

2. **Check the package name** — `package.json` uses `"name": "chatbot-react"`. If the name is taken, change it or use a scope (`@your-org/chatbot-react`) and set `"publishConfig": { "access": "public" }`.

3. **Build and verify** what will be published (only `dist/` is included):

   ```bash
   npm run build
   npm pack --dry-run
   ```

4. **Bump version** (semver), then publish:

   ```bash
   npm version patch   # or minor / major
   npm publish
   ```

   For a scoped package:

   ```bash
   npm publish --access public
   ```

5. **Consumers** install with:

   ```bash
   npm install chatbot-react
   ```

Optional: use [npm provenance](https://docs.npmjs.com/generating-provenance-statements) or GitHub Actions to publish on tag push.

## Development (this repo)

```bash
cd chatbot-react-library
npm install
npm run build
npm run dev   # demo at http://localhost:5173
```

## Usage

`ChatbotProvider` fournit la config, le store et l’appel API. **Votre application n’a pas besoin d’être à l’intérieur du provider** — seuls les composants UI du chat doivent l’être (ou un parent qui leur passe les props).

```tsx
function App() {
  return (
    <>
      <YourApp />

      <ChatbotProvider endpoint="/api/chat/chat">
        <FloatingChatbot />
      </ChatbotProvider>
    </>
  );
}
```

Import :

```tsx
import { ChatbotProvider, FloatingChatbot } from "chatbot-react";
import "chatbot-react/styles.css";
```

## Modes d’intégration

### 1. Flottant (défaut) — FAB + panneau

Bouton en bas à droite, fenêtre qui s’ouvre au clic. Idéal pour ajouter un assistant sur une app existante sans changer le layout.

```tsx
import { ChatbotProvider, FloatingChatbot } from "chatbot-react";

<ChatbotProvider
  endpoint="/api/chat/chat"
  hostLayout="overlay"   // défaut — ne prend pas de place dans le flux de la page
  title="Assistant"
  theme="system"
>
  <FloatingChatbot />
</ChatbotProvider>
```

Équivalent manuel : `FloatingButton` + `ChatWindow` (sans prop `embedded`).

Sur desktop, un bouton sur le bord du panneau permet de passer de 400px à 800px de large.

### 2. Intégré — colonne / sidebar / page dédiée

Chat toujours visible dans une zone de votre layout (pas de FAB, pas de backdrop).

```tsx
import { ChatbotProvider, ChatWindow } from "chatbot-react";

<ChatbotProvider
  endpoint="/api/chat/chat"
  hostLayout="block"   // le provider participe au flex/grid de la page
  title="Assistant"
>
  <aside className="h-screen w-96 shrink-0">
    <ChatWindow embedded />
  </aside>
</ChatbotProvider>
```

| | Flottant | Intégré (`embedded`) |
|---|----------|----------------------|
| Composant | `FloatingChatbot` ou `ChatWindow` | `ChatWindow embedded` |
| `hostLayout` | `overlay` (défaut) | `block` |
| Ouverture | FAB → `isOpen` | Toujours affiché |
| Bouton élargir le panneau | Oui (desktop) | Non |
| Pièces jointes | `attachments={{ enabled: true }}` | idem |

Exemple complet (page + chat côte à côte), comme la démo :

```tsx
function App() {
  const [theme, setTheme] = useState<ThemeMode>("system");

  return (
    <>
      <main className="flex-1">{/* votre contenu */}</main>

      <ChatbotProvider
        endpoint="/api/chat/chat"
        theme={theme}
        hostLayout="block"
        attachments={{ enabled: true }}
      >
        <aside className="h-screen w-[min(400px,42vw)] shrink-0 border-l">
          <ChatWindow embedded />
        </aside>
      </ChatbotProvider>
    </>
  );
}
```

Le conteneur parent est à votre charge. En mode `block`, le provider peut occuper une colonne flex **ou** un panneau `position: fixed` à droite pour ne pas décaler le reste de la page (comme dans la démo).

### Composants exportés (rappel)

| Composant | Rôle |
|-----------|------|
| `ChatbotProvider` | Config + store + SSE (obligatoire) |
| `FloatingChatbot` | FAB + fenêtre flottante |
| `ChatWindow` | Fenêtre seule (`embedded` pour sidebar) |
| `FloatingButton` | Bouton d’ouverture seul |
| `ChatHeader`, `MessageList`, `ChatInput`, … | UI modulaire / custom |

### Props `ChatbotProvider`

| Prop | Description |
|------|-------------|
| `endpoint` | URL POST SSE (ex. `/api/chat/chat`) |
| `headers` | Headers HTTP statiques |
| `getHeaders` | Headers async (auth bearer, etc.) |
| `model` | Modèle envoyé dans `ChatRequest.model` |
| `metadata` | Métadonnées libres |
| `theme` | `light` \| `dark` \| `system` — appliqué sur `.cb-root` via `data-cb-theme` |
| `primaryColor` | Couleur de marque (hex ou `rgb(...)`) — override `--cb-primary*` |
| `allowThemeToggle` | Bouton soleil/lune dans l’en-tête (défaut: `true` si `theme="system"`) |
| `title` | Titre dans l’en-tête du chat |
| `placeholder` | Placeholder du champ de saisie |
| `onToolApproval` | `(toolId, approved) => void` — appelé sur Approve/Deny |
| `suggestions` | Prompts suggérés dans l’état vide |
| `persist` | Historique localStorage (défaut: `true`) |
| `storageKey` | Clé localStorage |
| `hostLayout` | `overlay` (défaut, flottant) \| `block` (sidebar / page intégrée) |
| `attachments` | `{ enabled?, maxCount?, maxSizeBytes?, accept? }` — pièces jointes dans le composer (défaut: activé) |

### `ChatWindow`

| Prop | Description |
|------|-------------|
| `embedded` | `true` : panneau toujours visible, sans FAB ni bouton d’élargissement (à utiliser avec `hostLayout="block"`) |
| `collapsible` | Avec `embedded` : replier en rail latéral (défaut `true`). Même bouton latéral à chevrons que le mode flottant (`cb-panel-width-toggle`) pour replier / rouvrir. |

## Démo locale

Terminal 1 — backend Python :

```bash
cd ../chatbot-python-library
source .venv/bin/activate
python examples/02_fastapi_app.py
```

Terminal 2 — demo React :

```bash
npm run dev
# → http://localhost:5173 (proxy /api → :8000)
```

La démo propose un sélecteur **Integration → Display mode** (Floating / Sidebar) pour basculer entre les deux modes sans modifier le code.

## Structure

```
src/
├── components/   FloatingChatbot, ChatWindow, MessageList…
├── hooks/        useChatbot, useStreamingChat, useConversation
├── transport/    streamChat (SSE client)
├── core/         ChatbotProvider, Zustand store
├── types/        Protocole v1
└── styles/       globals.css, tokens.css
```

## Licence

MIT
