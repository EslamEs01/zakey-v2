import { stat } from "node:fs/promises";
import path from "node:path";
import {
  SCREENSHOT_ROOT,
  artifactName,
  loadQaMatrix,
  qaCells,
} from "./qa-matrix.js";

const REQUIRED_WIDTHS = [1440, 1024, 768, 390];
const REQUIRED_CHECKS = [
  "functional-assertion",
  "axe-critical-serious",
  "rendered-html",
  "console-pageerror",
  "assets-images-links",
  "horizontal-overflow",
  "screenshot",
];
const REQUIRED_DEFAULT_ROUTES = [
  "home",
  "shop",
  "collection",
  "search",
  "product",
  "cart",
  "checkout",
  "wishlist",
  "account",
  "about",
  "contact",
  "404",
  "5xx",
];
const EXPECTED_CELL_COUNT = 224;

function sameValues(actual, expected) {
  return (
    Array.isArray(actual) &&
    actual.length === expected.length &&
    expected.every((entry) => actual.includes(entry))
  );
}

function validateMatrixHeader(matrix) {
  if (matrix.schemaVersion !== 1) throw new Error("Unsupported QA matrix schema version.");
  if (!sameValues(matrix.widths, REQUIRED_WIDTHS)) throw new Error("QA widths are incomplete.");
  if (!sameValues(matrix.checksPerCell, REQUIRED_CHECKS)) {
    throw new Error("QA checks-per-cell are incomplete.");
  }
  if (matrix.screenshotPattern !== "{routeId}__{stateId}__{width}.png") {
    throw new Error("QA screenshot pattern changed unexpectedly.");
  }
}

function validateState(state) {
  const stringFields = [state.id, state.routeId, state.route, state.assert];
  if (stringFields.some((field) => !field)) throw new Error("QA state has a blank required field.");
  if (!state.route.startsWith("/")) throw new Error(`${state.id} has an invalid route.`);
  if (!state.setup?.kind) throw new Error(`${state.id} has no setup kind.`);
  if (Boolean(state.reference) === Boolean(state.referenceAbsentReason)) {
    throw new Error(`${state.id} must define reference evidence or an absence reason.`);
  }
}

function validateStates(states) {
  const stateIds = states.map((state) => state.id);
  if (new Set(stateIds).size !== stateIds.length) throw new Error("QA state IDs are not unique.");
  states.forEach(validateState);
  for (const routeId of REQUIRED_DEFAULT_ROUTES) {
    if (!states.some((state) => state.routeId === routeId && state.id.endsWith("default"))) {
      throw new Error(`${routeId} has no default QA state.`);
    }
  }
}

async function missingScreenshots(matrix, cells) {
  const missing = [];
  for (const cell of cells) {
    const filename = artifactName(matrix.screenshotPattern, cell);
    try {
      const screenshot = await stat(path.join(SCREENSHOT_ROOT, filename));
      if (screenshot.size === 0) missing.push(filename);
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
      missing.push(filename);
    }
  }
  return missing;
}

async function validateQaMatrix() {
  const matrix = await loadQaMatrix();
  validateMatrixHeader(matrix);
  validateStates(matrix.states);
  const cells = qaCells(matrix);
  if (cells.length !== EXPECTED_CELL_COUNT) {
    throw new Error(`Expected ${EXPECTED_CELL_COUNT} QA cells; received ${cells.length}.`);
  }
  if (process.argv.includes("--evidence")) {
    const missing = await missingScreenshots(matrix, cells);
    if (missing.length) throw new Error(`Missing screenshots:\n${missing.join("\n")}`);
  }
  console.log(`QA matrix is complete: ${matrix.states.length} states × ${matrix.widths.length} widths.`);
}

await validateQaMatrix();
