import { readdir } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";

const PROJECT_ROOT = process.cwd();
const SEARCH_DIRECTORIES = [
  "scripts",
  "static/src/js",
  "tests/e2e",
  "tests/accessibility",
  "tests/helpers",
];

async function javaScriptFiles(directory) {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }

  const nestedFiles = await Promise.all(
    entries.map((entry) => filesForEntry(directory, entry)),
  );
  return nestedFiles.flat();
}

async function filesForEntry(directory, entry) {
  const entryPath = path.join(directory, entry.name);
  if (entry.isDirectory()) return javaScriptFiles(entryPath);
  return entry.isFile() && entry.name.endsWith(".js") ? [entryPath] : [];
}

function syntaxFailure(filePath) {
  const check = spawnSync(process.execPath, ["--check", filePath], {
    cwd: PROJECT_ROOT,
    encoding: "utf8",
  });
  if (check.status === 0) return null;
  return `${filePath}\n${check.stderr || check.stdout}`;
}

async function checkNativeJavaScript() {
  const discovered = await Promise.all(
    SEARCH_DIRECTORIES.map((directory) => javaScriptFiles(directory)),
  );
  const files = ["playwright.config.js", ...discovered.flat()].sort();
  const failures = files.map(syntaxFailure).filter(Boolean);
  if (failures.length) throw new Error(failures.join("\n"));
  console.log(`JavaScript syntax check passed for ${files.length} files.`);
}

await checkNativeJavaScript();
