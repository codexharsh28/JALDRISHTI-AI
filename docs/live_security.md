# Live Operational Security & Secret Separation
## JALDRISHTI AI (SIH26071)

---

## 1. Zero Credential Exposure Policy

1. **Client-Side Build Sanitization:** No backend API keys (`IMD_API_KEY`, `MOSDAC_API_KEY`, `NASA_EARTHDATA_TOKEN`, `CWC_WRIS_TOKEN`) are exposed to client JavaScript or bundled in Vite production assets.
2. **Public Token Limitation:** Frontend environment variables are strictly limited to public client map tokens (`VITE_MAP_API_KEY`).
3. **Redacted Audit Logs:** `IngestionRunRecord` stores payload checksums and status codes; raw access tokens or auth headers are never logged or cached.
