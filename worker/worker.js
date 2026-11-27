// Annam AI helper server (Cloudflare Worker).
// Keeps the Gemini API key secret. The app calls:
//   POST /analyze  { image: "data:image/jpeg;base64,...", lang }  -> { items: [...] }
//   POST /chat     { question, context, lang }                    -> { answer }
// Setup: add a secret named GEMINI_API_KEY in the Worker's settings.

// Preferred models, tried in order. If Google retires one, the server finds
// another "flash" model automatically, so this file rarely needs changing.
const MODELS = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"];
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

async function listFlashModels(env) {
  const res = await fetch(`${API}/models?pageSize=200`, { headers: { "x-goog-api-key": env.GEMINI_API_KEY } });
  if (!res.ok) return [];
  const { models = [] } = await res.json();
  const ok = models.filter(m => (m.supportedGenerationMethods || []).includes("generateContent") &&
    /flash/.test(m.name) && !/image|tts|audio|live|exp|preview|thinking/.test(m.name));
  // newest first, full "flash" before "flash-lite"
  ok.sort((a, b) => (/lite/.test(a.name) - /lite/.test(b.name)) || b.name.localeCompare(a.name, undefined, { numeric: true }));
  return ok.map(m => m.name.replace(/^models\//, ""));
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

// Tries models in order. A missing model (404) or a busy one (429/5xx) moves on
// to the next; other errors (bad key, bad request) stop with Google's message.
async function gemini(env, parts, { jsonOut = false, maxTokens = 2048 } = {}) {
  const queue = [...new Set([chosenModel, ...MODELS].filter(Boolean))];
  const tried = new Set();
  let listed = false, busy = false, lastMsg = "";
  while (true) {
    let model = queue.shift();
    if (!model && !listed) { listed = true; queue.push(...(await listFlashModels(env)).filter(m => !tried.has(m))); model = queue.shift(); }
    if (!model) break;
    if (tried.has(model)) continue;
    tried.add(model);
    const res = await callModel(env, model, parts, jsonOut, maxTokens);
    if (res.ok) {
      chosenModel = model;
      const data = await res.json();
      return (data.candidates?.[0]?.content?.parts || []).filter(p => !p.thought).map(p => p.text || "").join("").trim();
    }
    let msg = ""; try { msg = (await res.json()).error?.message || ""; } catch {}
    if (res.status === 404) continue;
    if (res.status === 429 || res.status >= 500) { busy = true; lastMsg = msg; if (model === chosenModel) chosenModel = null; continue; }
    throw new Error(`AI service error ${res.status} ${msg}`.trim());
  }
  throw new Error(busy ? `AI is busy right now, please try again in a minute. ${lastMsg}`.trim()
                       : "No Gemini model available for this key (tried " + [...tried].join(", ") + ")");
}

const ANALYZE_PROMPT = (lang) => `You are an expert Indian dietitian estimating a meal from ONE photo for a calorie app.
Work carefully:
1. Identify each separate food or drink. Prefer specific Indian dish names (e.g. "idli", "sambar", "coconut chutney", "chicken biryani", "phulka/chapati").
2. Judge portion size from plate/bowl/glass size, cutlery and hands. A typical steel katori holds ~150 g, a full dinner plate of rice ~250-300 g, one idli ~40 g, one chapati ~40 g, one dosa ~80-100 g.
3. For countable items (idli, dosa, chapati, poori, vada, egg, biscuit, piece of fruit) give the count you can see.
4. Judge visible oil/ghee: none, little, normal, lots (glossy surface, oil pools, fried look = lots).
5. Give your own nutrition per 100 g as a fallback, using IFCT/ICMR-NIN style values for Indian home cooking.
6. Be honest about confidence: "high" only if the dish and portion are clear; "low" if partly hidden, blurry or ambiguous.
If the photo is not food, return {"items":[]}.
Reply ONLY with JSON:
{"items":[{"name":"English dish name","local":"name in ${LANG[lang] || "English"}","search":["2-3 alternative or more general names, e.g. 'rice idli','idli'"],
"countable":true,"count":3,"grams":120,"cooked":true,"oil":"none|little|normal|lots","confidence":"high|medium|low",
"per100":{"kcal":0,"protein":0,"carbs":0,"fat":0,"fibre":0}}],
"note":"one short helpful tip in ${LANG[lang] || "English"} about hidden calories in this meal, or empty"}
"grams" is the TOTAL weight of that item on the plate. Numbers only, no units.`;

const CHAT_PROMPT = (lang, context, question, history, refs) => `You are "Annam Helper", a warm, expert nutrition coach (like a registered dietitian) inside an Indian calorie tracking app.
Rules:
- Answer in ${LANG[lang] || "English"}. Simple words. Max 150 words. Use short lines or a small list. Use numbers (kcal, grams) where useful.
- Personalise using the user's data: today's intake vs goal, what they ate, their aim (lose/keep/gain), the time of day.
- For food values, prefer the REFERENCE FOODS below (from the Indian Nutrient Databank / app list) over your memory, and say portion sizes in Indian terms (katori, idli, chapati, glass).
- Suggest practical Indian swaps and meals (South and North Indian), budget-friendly.
- If the question is unclear or you need one key fact (e.g. portion, veg/non-veg), ask ONE short follow-up question instead of guessing.
- You are not a doctor: for illness, pregnancy, diabetes/BP medicines, eating disorders or very low calorie goals, advise seeing a doctor.
- Only help with food, nutrition, fitness, health habits and this app.

USER DATA: ${JSON.stringify(context).slice(0, 3500)}
REFERENCE FOODS: ${JSON.stringify(refs || []).slice(0, 1500)}
CONVERSATION SO FAR: ${JSON.stringify(history || []).slice(0, 3000)}

User: ${String(question).slice(0, 600)}`;

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(origin) });
    if (request.method !== "POST") return json({ ok: true, service: "annam-ai", version: 4 }, 200, origin);
    if (!env.GEMINI_API_KEY) return json({ error: "GEMINI_API_KEY is not set" }, 500, origin);
    const path = new URL(request.url).pathname;
    let body;
    try { body = await request.json(); } catch { return json({ error: "Bad request" }, 400, origin); }
    try {
      if (path === "/analyze") {
        const m = /^data:(image\/(?:jpeg|png|webp));base64,(.+)$/.exec(body.image || "");
        if (!m || m[2].length > 2_500_000) return json({ error: "Send a JPEG/PNG photo under 2 MB" }, 400, origin);
        const text = await gemini(env, [
          { inline_data: { mime_type: m[1], data: m[2] } },
          { text: ANALYZE_PROMPT(body.lang) },
        ], { jsonOut: true, maxTokens: 2048 });
        let items = [], note = "";
        try { const j = JSON.parse(text); items = j.items || []; note = String(j.note || "").slice(0, 200); } catch {}
        const num = (v, max) => Math.max(0, Math.min(max, Math.round(+v || 0)));
        items = items.slice(0, 12).map(i => ({
          name: String(i.name || "Food").slice(0, 60), local: String(i.local || i.name || "").slice(0, 60),
          search: (Array.isArray(i.search) ? i.search : []).slice(0, 3).map(x => String(x).slice(0, 40)),
          countable: !!i.countable, count: i.countable ? num(i.count, 30) || 1 : null,
          grams: num(i.grams, 2000) || 100, cooked: i.cooked !== false,
          oil: ["none", "little", "normal", "lots"].includes(i.oil) ? i.oil : "normal",
          confidence: ["high", "medium", "low"].includes(i.confidence) ? i.confidence : "medium",
          per100: { kcal: num(i.per100?.kcal, 900), protein: num(i.per100?.protein, 100), carbs: num(i.per100?.carbs, 100),
                    fat: num(i.per100?.fat, 100), fibre: num(i.per100?.fibre, 60) },
        }));
        return json({ items, note }, 200, origin);
      }
      if (path === "/chat") {
        if (!body.question) return json({ error: "Ask a question" }, 400, origin);
        const answer = await gemini(env, [{ text: CHAT_PROMPT(body.lang, body.context || {}, body.question, body.history, body.reference_foods) }]);
        return json({ answer }, 200, origin);
      }
      return json({ error: "Not found" }, 404, origin);
    } catch (e) {
      return json({ error: String(e.message || e) }, 502, origin);
    }
  },
};
