#!/usr/bin/env node
/**
 * super-fork MCP server (stdio transport).
 *
 * Wraps fork.py as a subprocess for each tool call, matching the
 * pattern used by qmd-knowledge's knowledge_mcp_server.cjs.
 *
 * Tools: fork, fork_list, fork_delete, fork_info, fork_rename, fork_tree
 */

const { execFile } = require("child_process");
const path = require("path");

// Resolve MCP SDK from known locations (same pattern as qmd-knowledge).
const sdkRoot = (() => {
  const candidates = [
    process.env.SUPER_FORK_SDK_ROOT,
    path.join(process.cwd(), "node_modules"),
    "/Users/ryo/.openclaw/vendor/node22-global/lib/node_modules/@tobilu/qmd/node_modules",
  ];
  for (const c of candidates) {
    if (!c) continue;
    try {
      require(path.join(c, "@modelcontextprotocol/sdk/dist/cjs/server/mcp.js"));
      return c;
    } catch {}
  }
  throw new Error(
    "Cannot find @modelcontextprotocol/sdk. Set SUPER_FORK_SDK_ROOT to a node_modules dir containing it."
  );
})();

const { McpServer } = require(path.join(sdkRoot, "@modelcontextprotocol/sdk/dist/cjs/server/mcp.js"));
const { StdioServerTransport } = require(path.join(sdkRoot, "@modelcontextprotocol/sdk/dist/cjs/server/stdio.js"));

let z;
try { z = require(path.join(sdkRoot, "zod/v4")); }
catch { try { z = require(path.join(sdkRoot, "zod")); } catch { z = null; } }

const FORK_PY = path.join(__dirname, "..", "skills", "super-fork", "scripts", "fork.py");

function runForkPy(args) {
  return new Promise((resolve, reject) => {
    execFile("python3", [FORK_PY, ...args], { timeout: 30000 }, (err, stdout, stderr) => {
      if (err && err.killed) {
        reject(new Error("fork.py timed out"));
      } else {
        resolve({ stdout: stdout || "", stderr: stderr || "", code: err ? err.code : 0 });
      }
    });
  });
}

async function callFork(args) {
  const result = await runForkPy(args);
  const output = (result.stdout + result.stderr).trim();
  return { content: [{ type: "text", text: output || "(no output)" }] };
}

async function main() {
  const server = new McpServer({ name: "super-fork", version: "0.3.0" });

  // --- fork ---
  const forkParams = z
    ? { source: z.string().optional().describe("Session UUID to fork (default: current session)"),
        name: z.string().optional().describe("Human-readable label ([s-fork] prefix added automatically)"),
        cwd: z.string().optional().describe("Target working directory for the fork") }
    : {};

  server.tool("fork", "Fork a Claude Code session (byte-level JSONL copy with new UUID)", forkParams, async (params) => {
    const args = [];
    if (params.name) { args.push("--name", params.name); }
    if (params.cwd) { args.push("--cwd", params.cwd); }
    if (params.source) { args.push(params.source); }
    return callFork(args);
  });

  // --- fork_list ---
  server.tool("fork_list", "List all labeled forks from the backup store", {}, async () => {
    return callFork(["--list"]);
  });

  // --- fork_delete ---
  const deleteParams = z
    ? { uuid: z.string().describe("UUID of the fork to delete") }
    : {};

  server.tool("fork_delete", "Delete a fork (JSONL + desktop metadata + label)", deleteParams, async (params) => {
    return callFork(["--delete", params.uuid]);
  });

  // --- fork_info ---
  const infoParams = z
    ? { uuid: z.string().describe("UUID of the session to inspect") }
    : {};

  server.tool("fork_info", "Show detailed info about a session (size, title, fork status, lineage)", infoParams, async (params) => {
    return callFork(["--info", params.uuid]);
  });

  // --- fork_rename ---
  const renameParams = z
    ? { uuid: z.string().describe("UUID of the fork to rename"),
        name: z.string().describe("New label ([s-fork] prefix added automatically)") }
    : {};

  server.tool("fork_rename", "Rename a fork's label in desktop sidebar and backup store", renameParams, async (params) => {
    return callFork(["--rename", params.uuid, params.name]);
  });

  // --- fork_tree ---
  server.tool("fork_tree", "Show fork lineage tree with trunk/branch/leaf roles", {}, async () => {
    return callFork(["--tree"]);
  });

  // --- fork_prune ---
  const pruneParams = z
    ? { level: z.enum(["leaf", "branch"]).describe("Prune level: 'leaf' (depth 2+) or 'branch' (depth 1+)"),
        dry_run: z.boolean().optional().describe("Preview only, don't actually delete") }
    : {};

  server.tool("fork_prune", "Prune forks by depth level (leaf or branch) into recoverable trash", pruneParams, async (params) => {
    const args = ["--prune", params.level];
    if (params.dry_run) { args.push("--dry-run"); }
    return callFork(args);
  });

  // --- fork_trash ---
  server.tool("fork_trash", "List contents of the super-fork trash (pruned sessions awaiting restore or permanent deletion)", {}, async () => {
    return callFork(["--trash"]);
  });

  // --- fork_restore ---
  const restoreParams = z
    ? { uuid: z.string().describe("UUID of the session to restore from trash") }
    : {};

  server.tool("fork_restore", "Restore a pruned session from trash back to its original location", restoreParams, async (params) => {
    return callFork(["--restore", params.uuid]);
  });

  // --- fork_mark_trunk ---
  const markTrunkParams = z
    ? { uuid: z.string().describe("UUID of the session to designate as trunk (depth 0)") }
    : {};

  server.tool("fork_mark_trunk", "Designate a session as trunk (upstream/main line) in the fork hierarchy", markTrunkParams, async (params) => {
    return callFork(["--mark-trunk", params.uuid]);
  });

  // --- fork_adopt ---
  const adoptParams = z
    ? { confirm: z.boolean().optional().describe("Actually register (default: dry-run preview only)") }
    : {};

  server.tool("fork_adopt", "Detect unregistered fork relationships and register them in the hierarchy", adoptParams, async (params) => {
    const args = ["--adopt"];
    if (params.confirm) { args.push("--confirm"); }
    return callFork(args);
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  process.stderr.write(`super-fork MCP server error: ${err.message}\n`);
  process.exit(1);
});
