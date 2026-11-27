# Annam AI helper server

A tiny Cloudflare Worker that keeps the Google Gemini API key secret and lets the app:

- `POST /analyze`: recognise foods in a meal photo and estimate calories, protein, carbs, fat and fibre
- `POST /chat`: answer nutrition questions using the user's own log, in English, Tamil or Hindi

## Set up (Cloudflare dashboard, free plan)

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Start with Hello World** → name it `annam-ai` → **Deploy**.
2. **Edit code** → replace everything with the contents of `worker.js` → **Deploy**.
3. **Settings** → **Variables and Secrets** → **Add** → Type **Secret**, Name `GEMINI_API_KEY`, Value = your key from https://aistudio.google.com/apikey → **Deploy**.
4. Put the Worker URL (`https://annam-ai.<your-subdomain>.workers.dev`) in `AI_URL` at the top of the script in `index.html`.

Never put the API key in this repository.
