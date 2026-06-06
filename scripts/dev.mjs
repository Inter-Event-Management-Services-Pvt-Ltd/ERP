import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";
const dryRun = process.argv.includes("--dry-run");

const npmCommand = "npm";
const uvCommand = "uv";

const services = [
  {
    name: "api",
    cwd: path.join(rootDir, "apps", "api"),
    command: uvCommand,
    args: ["run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
    envFile: path.join(rootDir, "apps", "api", ".env"),
    url: "http://localhost:8000/health",
  },
  {
    name: "web",
    cwd: path.join(rootDir, "apps", "web"),
    command: npmCommand,
    args: ["run", "dev"],
    envFile: path.join(rootDir, "apps", "web", ".env.local"),
    url: "http://localhost:3000",
  },
];

if (dryRun) {
  for (const service of services) {
    console.log(
      `[${service.name}] ${service.command} ${service.args.join(" ")} ` +
        `(cwd: ${path.relative(rootDir, service.cwd)})`,
    );
  }
  process.exit(0);
}

for (const service of services) {
  if (!existsSync(service.envFile)) {
    console.warn(
      `[${service.name}] warning: ${path.relative(rootDir, service.envFile)} is missing`,
    );
  }
}

console.log("[dev] starting API and web dev servers");
console.log("[api] " + services[0].url);
console.log("[web] " + services[1].url);

let shuttingDown = false;
const children = [];

for (const service of services) {
  children.push(startService(service));
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

function startService(service) {
  let child;
  try {
    child = spawnService(service);
  } catch (error) {
    console.error(`[${service.name}] failed to start: ${error.message}`);
    shutdown("START_ERROR", 1);
    throw error;
  }

  child.on("error", (error) => {
    console.error(`[${service.name}] failed to start: ${error.message}`);
    shutdown("START_ERROR", 1);
  });

  child.on("exit", (code, signal) => {
    if (shuttingDown) return;
    const reason = signal ? `signal ${signal}` : `code ${code}`;
    console.error(`[${service.name}] exited with ${reason}`);
    shutdown(`${service.name.toUpperCase()}_EXIT`, code ?? 1);
  });

  pipeWithPrefix(child.stdout, service.name);
  pipeWithPrefix(child.stderr, service.name);

  return child;
}

function spawnService(service) {
  if (isWindows) {
    return spawn("cmd.exe", ["/d", "/s", "/c", quoteWindowsCommand(service)], {
      cwd: service.cwd,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
  }

  return spawn(service.command, service.args, {
    cwd: service.cwd,
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
  });
}

function quoteWindowsCommand(service) {
  const parts = [service.command, ...service.args].map((part) => {
    if (!/[ \t"]/u.test(part)) return part;
    return `"${part.replaceAll('"', '\\"')}"`;
  });
  return parts.join(" ");
}

function pipeWithPrefix(stream, name) {
  const lines = readline.createInterface({ input: stream });
  lines.on("line", (line) => {
    console.log(`[${name}] ${line}`);
  });
}

function shutdown(reason, exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(`[dev] stopping services (${reason})`);

  const stops = children.map(stopProcess);
  Promise.allSettled(stops).finally(() => {
    process.exit(exitCode);
  });
}

function stopProcess(child) {
  return new Promise((resolve) => {
    if (child.exitCode !== null || child.killed) {
      resolve();
      return;
    }

    child.once("exit", () => resolve());

    if (isWindows) {
      spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], {
        stdio: "ignore",
        windowsHide: true,
      }).once("exit", () => resolve());
      return;
    }

    child.kill("SIGTERM");
    setTimeout(() => {
      if (child.exitCode === null) child.kill("SIGKILL");
      resolve();
    }, 5000).unref();
  });
}
