import { readFile } from "node:fs/promises";
import path from "node:path";
import { FileSystemConfigLoader, HtmlValidate } from "html-validate";
import {
  RENDERED_HTML_ROOT,
  artifactName,
  loadQaMatrix,
  qaCells,
} from "./qa-matrix.js";

const htmlValidator = new HtmlValidate(new FileSystemConfigLoader());

function reportMessages(report, filename) {
  return report.results.flatMap((validationResult) =>
    validationResult.messages.map(
      (message) =>
        `${filename}:${message.line}:${message.column} ${message.ruleId} ${message.message}`,
    ),
  );
}

async function validateSnapshot(matrix, cell) {
  const pngName = artifactName(matrix.screenshotPattern, cell);
  const filename = pngName.replace(/\.png$/, ".html");
  const snapshotPath = path.join(RENDERED_HTML_ROOT, filename);
  let markup;
  try {
    markup = await readFile(snapshotPath, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return [`${filename}: rendered snapshot is missing`];
    throw error;
  }
  const report = await htmlValidator.validateString(markup, snapshotPath);
  return report.valid ? [] : reportMessages(report, filename);
}

async function validateRenderedMatrix() {
  const matrix = await loadQaMatrix();
  const cells = qaCells(matrix);
  const validationGroups = await Promise.all(
    cells.map((cell) => validateSnapshot(matrix, cell)),
  );
  const failures = validationGroups.flat();
  if (failures.length) throw new Error(failures.join("\n"));
  console.log(`Rendered HTML validation passed for ${cells.length} QA cells.`);
}

await validateRenderedMatrix();
