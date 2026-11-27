// Annam AI helper server (Cloudflare Worker).
// Keeps the Gemini API key secret. The app calls:
//   POST /analyze  { image: "data:image/jpeg;base64,...", lang }  -> { items: [...] }
//   POST /chat     { question, context, lang }                    -> { answer }
// Setup: add a secret named GEMINI_API_KEY in the Worker's settings.

// Preferred models, tried in order. If Google retires one, the server finds
// another "flash" model automatically, so this file rarely needs changing.
const MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"];
let chosenModel = null;
const ALLOWED_ORIGINS = [
  "https://senthamizhselvanpa29-byte.github.io",
];
const LANG = { en: "English", ta: "Tamil", hi: "Hindi" };

function cors(origin) {
  const ok = ALLOWED_ORIGINS.includes(origin) || /^https:\/\/[a-z0-9-]+\.claude(usercontent)?\.(ai|com)$/.test(origin || "");
  return {
    "Access-Control-Allow-Origin": ok ? origin : ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}
const json = (data, status, origin) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", ...cors(origin) } });

const API = "https://generativelanguage.googleapis.com/v1beta";

async function findFlashModel(env) {
  const res = await fetch(`${API}/models?pageSize=200`, { headers: { "x-goog-api-key": env.GEMINI_API_KEY } });
  if (!res.ok) return null;
  const { models = [] } = await res.json();
  const ok = models.filter(m => (m.supportedGenerationMethods || []).includes("generateContent") &&
    /flash/.test(m.name) && !/lite|image|tts|audio|live|exp|preview|thinking/.test(m.name));
  ok.sort((a, b) => b.name.localeCompare(a.name, undefined, { numeric: true }));
  return ok[0] ? ok[0].name.replace(/^models\//, "") : null;
}

async function callModel(env, model, parts, jsonOut, maxTokens) {
  return fetch(`${API}/models/${model}:generateContent`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
    body: JSON.stringify({
      contents: [{ role: "user", parts }],
      generationConfig: {
        temperature: 0.3,
        maxOutputTokens: maxTokens,
        ...(jsonOut ? { responseMimeType: "application/json" } : {}),
      },
    }),
  });
}

async function gemini(env, parts, { jsonOut = false, maxTokens = 2048 } = {}) {
  const tried = [];
  const candidates = chosenModel ? [chosenModel] : [...MODELS];
  for (let i = 0; i < candidates.length + 1; i++) {
    let model = candidates[i];
    if (!model) { model = await findFlashModel(env); if (!model || tried.includes(model)) break; }
    tried.push(model);
    const res = await callModel(env, model, parts, jsonOut, maxTokens);
    if (res.status === 404) { if (chosenModel) { chosenModel = null; candidates.push(...MODELS); } continue; }
    if (!res.ok) {
      let msg = ""; try { msg = (await res.json()).error?.message || ""; } catch {}
      throw new Error(`AI service error ${res.status} ${msg}`.trim());
    }
    chosenModel = model;
    const data = await res.json();
    return (data.candidates?.[0]?.content?.parts || []).filter(p => !p.thought).map(p => p.text || "").join("").trim();
  }
  throw new Error("No Gemini model available for this key (tried " + tried.join(", ") + ")");
}

const ANALYZE_PROMPT = (lang) => `You are a nutrition assistant for an Indian calorie tracking app.
Look at this meal photo. List every distinct food or drink you can see.
For each item estimate the portion actually on the plate and its nutrition for that portion.
Prefer Indian dish names (e.g. idli, sambar, dosa, chapati, dal, biryani) when they fit.
If the photo is not food, return {"items": []}.
Reply ONLY with JSON in this shape:
{"items":[{"name":"English name","local":"name in ${LANG[lang] || "English"}","portion":"e.g. 2 pieces / 1 bowl","kcal":0,"protein":0,"carbs":0,"fat":0,"fibre":0}]}
Numbers are grams except kcal. Round to whole numbers.`;

const CHAT_PROMPT = (lang, context, question) => `You are "Annam Helper", a friendly nutrition coach inside a calorie tracking app used mostly in India.
Answer in ${LANG[lang] || "English"}, in simple words, in at most 120 words. Use short lines or a short list.
Suggest Indian foods where useful. Use the user's data below when it helps.
You are not a doctor: for illness, pregnancy, diabetes medicines or very low calorie goals, advise seeing a doctor.
If the question is not about food, health, fitness or this app, politely say you can only help with those.

User data (JSON): ${JSON.stringify(context).slice(0, 3000)}

Question: ${String(question).slice(0, 500)}`;

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(origin) });
    if (request.method !== "POST") return json({ ok: true, service: "annam-ai", version: 2 }, 200, origin);
    if (!env.GEMINI_API_KEY) return json({ error: "GEMINI_API_KEY is not set" }, 500, origin);
    const path = new URL(request.url).pathname;
    let body;
    try { body = await request.json(); } catch { return json({ error: "Bad request" }, 400, origin); }
    try {
      if (path === "/analyze") {
        const m = /^data:(image\/(?:jpeg|png|webp));base64,(.+)$/.exec(body.image || "");
        if (!m || m[2].length > 1_500_000) return json({ error: "Send a JPEG/PNG photo under 1 MB" }, 400, origin);
        const text = await gemini(env, [
          { inline_data: { mime_type: m[1], data: m[2] } },
          { text: ANALYZE_PROMPT(body.lang) },
        ], { jsonOut: true, maxTokens: 2048 });
        let items = [];
        try { items = JSON.parse(text).items || []; } catch {}
        items = items.slice(0, 12).map(i => ({
          name: String(i.name || "Food").slice(0, 60), local: String(i.local || i.name || "").slice(0, 60),
          portion: String(i.portion || "1 serving").slice(0, 40),
          kcal: Math.max(0, Math.round(+i.kcal || 0)), protein: Math.max(0, Math.round(+i.protein || 0)),
          carbs: Math.max(0, Math.round(+i.carbs || 0)), fat: Math.max(0, Math.round(+i.fat || 0)),
          fibre: Math.max(0, Math.round(+i.fibre || 0)),
        }));
        return json({ items }, 200, origin);
      }
      if (path === "/chat") {
        if (!body.question) return json({ error: "Ask a question" }, 400, origin);
        const answer = await gemini(env, [{ text: CHAT_PROMPT(body.lang, body.context || {}, body.question) }]);
        return json({ answer }, 200, origin);
      }
      return json({ error: "Not found" }, 404, origin);
    } catch (e) {
      return json({ error: String(e.message || e) }, 502, origin);
    }
  },
};
