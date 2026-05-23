#!/Users/ryo/.local/nodejs/bin/node

const { execFile } = require("node:child_process");
const path = require("node:path");
const { promisify } = require("node:util");

const execFileAsync = promisify(execFile);
const pluginRoot = path.resolve(__dirname, "..");
const scriptsRoot = path.join(pluginRoot, "scripts");

const sdkRoot =
  process.env.QMD_KNOWLEDGE_SDK_ROOT ||
  "/Users/ryo/.openclaw/vendor/node22-global/lib/node_modules/@tobilu/qmd/node_modules";

const { McpServer } = require(path.join(
  sdkRoot,
  "@modelcontextprotocol/sdk/dist/cjs/server/mcp.js"
));
const { StdioServerTransport } = require(path.join(
  sdkRoot,
  "@modelcontextprotocol/sdk/dist/cjs/server/stdio.js"
));
const z = require(path.join(sdkRoot, "zod/v4"));

const queryWrapper = path.join(scriptsRoot, "knowledge_query");
const searchWrapper = path.join(scriptsRoot, "knowledge_search");
const getWrapper = path.join(scriptsRoot, "knowledge_get");

const server = new McpServer({
  name: "qmd-knowledge",
  version: "0.1.0",
});

function buildToolError(error) {
  const stderr = error.stderr ? String(error.stderr).trim() : "";
  const stdout = error.stdout ? String(error.stdout).trim() : "";
  const message = stderr || stdout || error.message || "Unknown error.";
  return {
    isError: true,
    content: [{ type: "text", text: message }],
  };
}

async function runWrapper(wrapperPath, args) {
  const result = await execFileAsync(wrapperPath, args, {
    cwd: pluginRoot,
    maxBuffer: 1024 * 1024,
  });
  return JSON.parse(result.stdout);
}

// --- query: balanced hybrid search (default) ---
server.registerTool(
  "query",
  {
    title: "QMD Query",
    description:
      "Hybrid search over knowledge/reports/agents-docs/diary using balanced lex+vec strategy with LLM reranking. Best for general retrieval.",
    inputSchema: {
      query: z.string().min(1).describe("Natural-language search query."),
      maxResults: z.number().int().min(1).max(20).default(5).describe("Max hits."),
      pathFilter: z.string().optional().describe("Substring filter on path, e.g. knowledge/openclaw/."),
      collection: z.string().optional().describe("Limit to a single collection: knowledge, agents-docs, reports, eris-diary."),
      minScore: z.number().min(0).max(1).optional().describe("Minimum score threshold."),
    },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  async ({ query, maxResults = 5, pathFilter, collection, minScore }) => {
    try {
      const args = [query, "--max-results", String(maxResults), "--strategy", "balanced", "--candidate-limit", "15"];
      if (pathFilter) args.push("--path-filter", pathFilter);
      if (collection) args.push("--collection", collection);
      if (minScore !== undefined) args.push("--min-score", String(minScore));
      const payload = await runWrapper(queryWrapper, args);
      return {
        content: [{ type: "text", text: `Found ${payload.meta.resultCount} hit(s) for "${payload.query}".` }],
        structuredContent: payload,
      };
    } catch (error) {
      return buildToolError(error);
    }
  }
);

// --- vsearch: semantic vector search ---
server.registerTool(
  "vsearch",
  {
    title: "QMD VSearch",
    description:
      "Semantic vector search only. Faster than query, good when you need lightweight similarity matching.",
    inputSchema: {
      query: z.string().min(1).describe("Natural-language semantic search query."),
      maxResults: z.number().int().min(1).max(20).default(5).describe("Max hits."),
      pathFilter: z.string().optional().describe("Substring filter on path."),
      collection: z.string().optional().describe("Limit to a single collection."),
      minScore: z.number().min(0).max(1).optional().describe("Minimum score threshold."),
    },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  async ({ query, maxResults = 5, pathFilter, collection, minScore }) => {
    try {
      const args = [query, "--max-results", String(maxResults)];
      if (pathFilter) args.push("--path-filter", pathFilter);
      if (collection) args.push("--collection", collection);
      if (minScore !== undefined) args.push("--min-score", String(minScore));
      const payload = await runWrapper(searchWrapper, args);
      return {
        content: [{ type: "text", text: `Found ${payload.meta.resultCount} hit(s) for "${payload.query}".` }],
        structuredContent: payload,
      };
    } catch (error) {
      return buildToolError(error);
    }
  }
);

// --- get: read a note slice ---
server.registerTool(
  "get",
  {
    title: "QMD Get",
    description:
      "Read a specific slice of a document by absolute path or qmd:// URI. Use after query/vsearch to read the best hit.",
    inputSchema: {
      path: z.string().min(1).describe("Absolute path or qmd:// URI from search results."),
      line: z.number().int().min(1).default(1).describe("1-based start line."),
      lines: z.number().int().min(1).max(200).default(40).describe("Number of lines to read."),
    },
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  async ({ path: notePath, line = 1, lines = 40 }) => {
    try {
      const args = [notePath, "--line", String(line), "--lines", String(lines)];
      const payload = await runWrapper(getWrapper, args);
      return {
        content: [{ type: "text", text: `Read lines ${payload.startLine}-${payload.endLine} from ${payload.path}.` }],
        structuredContent: payload,
      };
    } catch (error) {
      return buildToolError(error);
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("qmd-knowledge MCP server running on stdio (Claude Code)");
}

main().catch((error) => {
  console.error("qmd-knowledge MCP server failed:", error);
  process.exit(1);
});
