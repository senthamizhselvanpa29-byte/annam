// Annam AI helper server (Cloudflare Worker).
// Keeps the Gemini API key secret. The app calls:
//   POST /analyze  { image: "data:image/jpeg;base64,...", lang }  -> { items: [...] }
//   POST /chat     { question, context, lang }                    -> { answer }
// Setup: add a secret named GEMINI_API_KEY in the Worker's settings.

const MODEL = "gemini-2.5-flash";
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

async function gemini(env, parts, { jsonOut = false, maxTokens = 800 } = {}) {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
      body: JSON.stringify({
        contents: [{ role: "user", parts }],
        generationConfig: {
          temperature: 0.3,
          maxOutputTokens: maxTokens,
          thinkingConfig: { thinkingBudget: 0 },
          ...(jsonOut ? { responseMimeType: "application/json" } : {}),
        },
      }),
    }
  );
  if (!res.ok) throw new Error("AI service error " + res.status);
  const data = await res.json();
  return (data.candidates?.[0]?.content?.parts || []).map(p => p.text || "").join("").trim();
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
    if (request.method !== "POST") return json({ ok: true, service: "annam-ai" }, 200, origin);
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
        ], { jsonOut: true, maxTokens: 1000 });
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
