// AI Crawler Tracking — Vercel Edge Function
// Detects AI bot user-agents, logs to Supabase crawler_visits table
// Usage: <img src="/api/track?p=/path" width="1" height="1" alt="">

export const config = { runtime: "edge" };

const SITE_NAME = "japan-encyclopedia";

const SUPABASE_URL = "https://yitmabzsxfgbchhhjjef.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpdG1hYnpzeGZnYmNoaGhqamVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA3OTQ0NzQsImV4cCI6MjA1NjM3MDQ3NH0.pDq3Mn6GT0y_IB-frPxJTTy5YaxJhJg3aluUsjR_VE4";

// 1x1 transparent GIF
const PIXEL = new Uint8Array([
  71,73,70,56,57,97,1,0,1,0,128,0,0,255,255,255,0,0,0,33,249,4,0,0,0,0,0,44,0,0,0,0,1,0,1,0,0,2,2,68,1,0,59
]);

const AI_BOTS = [
  { ua: "GPTBot", name: "GPTBot", owner: "OpenAI" },
  { ua: "ChatGPT-User", name: "ChatGPT-User", owner: "OpenAI" },
  { ua: "OAI-SearchBot", name: "OAI-SearchBot", owner: "OpenAI" },
  { ua: "Google-Extended", name: "Google-Extended", owner: "Google" },
  { ua: "Googlebot", name: "Googlebot", owner: "Google" },
  { ua: "Bingbot", name: "Bingbot", owner: "Microsoft" },
  { ua: "anthropic-ai", name: "ClaudeBot", owner: "Anthropic" },
  { ua: "ClaudeBot", name: "ClaudeBot", owner: "Anthropic" },
  { ua: "Claude-Web", name: "Claude-Web", owner: "Anthropic" },
  { ua: "PerplexityBot", name: "PerplexityBot", owner: "Perplexity" },
  { ua: "cohere-ai", name: "Cohere", owner: "Cohere" },
  { ua: "Applebot", name: "Applebot", owner: "Apple" },
  { ua: "YouBot", name: "YouBot", owner: "You.com" },
  { ua: "Amazonbot", name: "Amazonbot", owner: "Amazon" },
  { ua: "meta-externalagent", name: "Meta-AI", owner: "Meta" },
  { ua: "FacebookBot", name: "FacebookBot", owner: "Meta" },
  { ua: "CCBot", name: "CCBot", owner: "Common Crawl" },
  { ua: "YandexBot", name: "YandexBot", owner: "Yandex" },
  { ua: "ia_archiver", name: "Alexa", owner: "Internet Archive" },
  { ua: "PetalBot", name: "PetalBot", owner: "Huawei" },
  { ua: "Bytespider", name: "Bytespider", owner: "ByteDance" },
  { ua: "Baiduspider", name: "Baiduspider", owner: "Baidu" },
  { ua: "Sogou", name: "Sogou", owner: "Sogou" },
  { ua: "360Spider", name: "360Spider", owner: "Qihoo 360" },
  { ua: "DeepSeekBot", name: "DeepSeekBot", owner: "DeepSeek" },
];

function detectBot(userAgent) {
  if (!userAgent) return null;
  for (const bot of AI_BOTS) {
    if (userAgent.includes(bot.ua)) return bot;
  }
  return null;
}

async function hashIP(ip) {
  const data = new TextEncoder().encode(ip + "cloudpipe-salt-2026");
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

export default async function handler(request) {
  const ua = request.headers.get("user-agent") || "";
  const bot = detectBot(ua);

  if (bot) {
    const url = new URL(request.url);
    const path = url.searchParams.get("p") || request.headers.get("referer") || "/";
    const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
    const ipHash = await hashIP(ip);
    const dateStr = new Date().toISOString().slice(0, 10);

    // Fire-and-forget to Supabase
    try {
      fetch(`${SUPABASE_URL}/rest/v1/crawler_visits`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: SUPABASE_KEY,
          Authorization: `Bearer ${SUPABASE_KEY}`,
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          bot_name: bot.name,
          bot_owner: bot.owner,
          path: path.slice(0, 500),
          referer: request.headers.get("referer")?.slice(0, 500) || null,
          ip_hash: ipHash,
          session_id: `${ipHash}-${bot.name}-${dateStr}`,
          ua_raw: ua.slice(0, 500),
          site: SITE_NAME,
          page_type: path === "/" ? "home" : path.includes("/articles/") ? "article" : "page",
        }),
      }).catch(() => {});
    } catch {}
  }

  return new Response(PIXEL, {
    headers: {
      "Content-Type": "image/gif",
      "Cache-Control": "no-store, no-cache, must-revalidate",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
