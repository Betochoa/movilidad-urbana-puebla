# build-day

## Usar Claude Code con API key (sin suscripción)

1. Crea una key en https://console.anthropic.com/settings/keys (requiere crédito en la cuenta de API).
2. Pega la key en `.env` → `ANTHROPIC_API_KEY=sk-ant-...`
3. Si ya tenías sesión con tu suscripción, ejecuta `/logout` dentro de Claude Code.
4. Abre `claude` desde esta carpeta. `.claude/settings.json` usa `.claude/get-api-key.sh` para leer la key de `.env`.
5. Verifica con `/status` que diga que usa API key y no suscripción.

`.env` está en `.gitignore`; nunca lo subas al repo.
