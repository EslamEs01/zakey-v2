import { readFile } from "node:fs/promises";
import path from "node:path";

export const FEATURE_ROOT = path.join(
  process.cwd(),
  "specs/003-zakey-frontend-reference-build",
);
export const MATRIX_PATH = path.join(FEATURE_ROOT, "contracts/qa-matrix.json");
export const RENDERED_HTML_ROOT = path.join(FEATURE_ROOT, "qa/rendered-html");
export const SCREENSHOT_ROOT = path.join(FEATURE_ROOT, "qa/implementation-screenshots");

export async function loadQaMatrix() {
  const encodedMatrix = await readFile(MATRIX_PATH, "utf8");
  return JSON.parse(encodedMatrix);
}

export function qaCells(matrix) {
  return matrix.states.flatMap((state) =>
    matrix.widths.map((width) => ({
      routeId: state.routeId,
      stateId: state.id,
      width,
    })),
  );
}

export function artifactName(pattern, cell) {
  return pattern
    .replace("{routeId}", cell.routeId)
    .replace("{stateId}", cell.stateId)
    .replace("{width}", String(cell.width));
}
