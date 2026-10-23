#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import process from "node:process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WEB_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const ROOT = path.dirname(WEB_DIR);

const BACKEND_SERVICES = [
  { name: "fournisseur", label: "[fournisseur]", port: 8765, health: "/health" },
  { name: "portail", label: "[portail]", port: 8766, health: "/health" },
];

function killPort(port) {
  const res = spawnSync("lsof", ["-t", "-i", `tcp:${port}`], { encoding: "utf8" });
  const pids = (res.stdout || "")
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
  for (const pid of pids) {
    if (pid === String(process.pid)) continue;
    spawnSync("kill", ["-9", pid]);
  }
  return pids.length;
}

async function waitHealth(port, healthPath, timeoutMs = 60000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}${healthPath}`);
      if (res.ok) return true;
    } catch {
      /* pas encore prêt */
    }
    await delay(300);
  }
  return false;
}

function isDockerAvailable() {
  try {
    const res = spawnSync("docker", ["info"], { stdio: "pipe" });
    return res.status === 0;
  } catch {
    return false;
  }
}

// --- Docker availability ---
if (!isDockerAvailable()) {
  console.error("\n❌ Docker n'est pas disponible ou n'est pas lancé.");
  console.error("   Démarrez Docker Desktop puis relancez `pnpm dev`.\n");
  process.exit(1);
}

// --- Free ports from any stale local processes ---
for (const svc of BACKEND_SERVICES) {
  const killed = killPort(svc.port);
  if (killed) {
    console.log(`${svc.label} port ${svc.port} libéré (${killed} processus tué(s))`);
  }
}

// --- Build + start the Docker stack (fournisseur, portail, Grafana, Prometheus, Loki) ---
console.log("[docker] construction + démarrage de la stack …");
const compose = spawnSync("docker", ["compose", "up", "-d", "--build"], {
  cwd: ROOT,
  stdio: "inherit",
  env: process.env,
});
if (compose.status !== 0) {
  console.error(`\n❌ \`docker compose up\` a échoué (code ${compose.status}).\n`);
  process.exit(1);
}

// --- Wait for backend health checks ---
for (const svc of BACKEND_SERVICES) {
  console.log(`${svc.label} attente du health check sur :${svc.port} …`);
  const ok = await waitHealth(svc.port, svc.health);
  if (!ok) {
    console.error(`\n❌ ${svc.label} ne répond pas sur :${svc.port} — arrêt.`);
    console.error("   Vérifiez les logs : `docker compose logs ${svc.name}`\n");
    process.exit(1);
  }
  console.log(`${svc.label} ✅ prêt sur :${svc.port}`);
}

// --- Start Vite (HMR stays local, proxies /api + /metrics → :8766) ---
console.log("[web] démarrage sur :5173 …");
const vite = spawn(
  process.execPath,
  [path.join(WEB_DIR, "node_modules", "vite", "bin", "vite.js")],
  {
    cwd: WEB_DIR,
    env: process.env,
    stdio: ["ignore", "inherit", "inherit"],
  },
);

function shutdown(code) {
  try {
    vite.kill("SIGTERM");
  } catch {
    /* déjà mort */
  }
  console.log("\n— conteneurs Docker toujours actifs (Grafana : http://localhost:3000) —");
  console.log("  arrêt complet : `docker compose down`\n");
  process.exit(code);
}

process.on("SIGINT", () => shutdown(130));
process.on("SIGTERM", () => shutdown(143));

await delay(1000);
console.log("\n✅ DÉTOUR prêt — http://localhost:5173  (Ctrl+C arrête Vite, Docker reste up)\n");
