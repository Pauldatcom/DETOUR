#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import process from "node:process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WEB_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const ROOT = path.dirname(WEB_DIR);

const SERVICES = [
  {
    name: "fournisseur",
    label: "[fournisseur]",
    cmd: "python3",
    args: [path.join(ROOT, "server", "app.py"), "--demo"],
    port: 8765,
    health: "/health",
  },
  {
    name: "portail",
    label: "[portail]",
    cmd: "python3",
    args: [path.join(ROOT, "conseiller", "app.py"), "--port", "8766"],
    port: 8766,
    health: "/health",
  },
  {
    name: "web",
    label: "[web]",
    cmd: process.execPath,
    args: [path.join(WEB_DIR, "node_modules", "vite", "bin", "vite.js")],
    port: 5173,
    health: null,
    cwd: WEB_DIR,
  },
];

function killPort(port) {
  const res = spawnSync("lsof", ["-t", "-i", `tcp:${port}`], { encoding: "utf8" });
  const pids = (res.stdout || "").split("\n").map((s) => s.trim()).filter(Boolean);
  for (const pid of pids) {
    if (pid === String(process.pid)) continue;
    spawnSync("kill", ["-9", pid]);
  }
  return pids.length;
}

async function waitHealth(port, healthPath, timeoutMs = 10000) {
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

const children = new Map();

function start(service) {
  const child = spawn(service.cmd, service.args, {
    cwd: service.cwd ?? ROOT,
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
  });
  children.set(service.name, child);
  const pipe = (stream, isError) => {
    let buffer = "";
    stream.on("data", (chunk) => {
      buffer += chunk.toString();
      let idx;
      while ((idx = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 1);
        if (line.trim()) console.log(`${service.label} ${line}`);
      }
    });
    stream.on("error", () => {});
    if (isError) stream.on("data", () => {});
  };
  pipe(child.stdout);
  pipe(child.stderr);
  child.on("exit", (code) => {
    if (children.get(service.name) === child) {
      children.delete(service.name);
      console.log(`${service.label} arrêté (code ${code ?? "?"})`);
    }
  });
}

function shutdown(code) {
  for (const child of children.values()) {
    try {
      child.kill("SIGTERM");
    } catch {
      /* déjà mort */
    }
  }
  process.exit(code);
}

process.on("SIGINT", () => shutdown(130));
process.on("SIGTERM", () => shutdown(143));

for (const service of SERVICES.slice(0, 2)) {
  const killed = killPort(service.port);
  if (killed) {
    console.log(`${service.label} port ${service.port} libéré (${killed} processus tué(s))`);
  }
}

for (const service of SERVICES.slice(0, 2)) {
  console.log(`${service.label} démarrage sur :${service.port} …`);
  start(service);
  const ok = await waitHealth(service.port, service.health);
  if (!ok) {
    console.error(`${service.label} ne répond pas sur :${service.port} — arrêt.`);
    shutdown(1);
  }
}

console.log("[web] démarrage sur :5173 …");
start(SERVICES[2]);

await delay(1000);
console.log("\n✅ DÉTOUR prêt — http://localhost:5173  (Ctrl+C pour tout arrêter)\n");
