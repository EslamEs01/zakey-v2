import { access, copyFile, cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";

const PROJECT_ROOT = process.cwd();
const FONT_OUTPUT = path.join(PROJECT_ROOT, "static/dist/assets/fonts");
const ICON_OUTPUT = path.join(PROJECT_ROOT, "static/dist/assets/icons");
const AUTHORED_ASSETS = path.join(PROJECT_ROOT, "static/src/assets");
const AUTHORED_OUTPUT = path.join(PROJECT_ROOT, "static/dist/assets");

const FONT_FILES = [
  ...[400, 500, 600, 700, 800].map(
    (weight) => `@fontsource/cairo/files/cairo-arabic-${weight}-normal.woff2`,
  ),
  ...[400, 500, 600, 700].map(
    (weight) => `@fontsource/poppins/files/poppins-latin-${weight}-normal.woff2`,
  ),
];

const ICON_NAMES = [
  "alert-circle",
  "arrow-left",
  "arrow-right",
  "badge-check",
  "banknote",
  "check",
  "chevron-down",
  "chevron-left",
  "chevron-right",
  "circle-help",
  "clock-3",
  "credit-card",
  "download",
  "eye",
  "filter",
  "fingerprint",
  "heart",
  "house",
  "info",
  "key-round",
  "lock-keyhole",
  "mail",
  "map-pin",
  "menu",
  "minus",
  "package",
  "phone",
  "plus",
  "refresh-cw",
  "search",
  "share-2",
  "shield-check",
  "shopping-bag",
  "shopping-cart",
  "sliders-horizontal",
  "sparkles",
  "star",
  "trash-2",
  "truck",
  "user-round",
  "wallet-cards",
  "x",
];

async function copyDependencyFile(relativeSource, outputDirectory) {
  const source = path.join(PROJECT_ROOT, "node_modules", relativeSource);
  await access(source);
  await copyFile(source, path.join(outputDirectory, path.basename(source)));
}

async function copyFonts() {
  await mkdir(FONT_OUTPUT, { recursive: true });
  for (const relativeSource of FONT_FILES) {
    await copyDependencyFile(relativeSource, FONT_OUTPUT);
  }
}

async function copyIcons() {
  await mkdir(ICON_OUTPUT, { recursive: true });
  for (const iconName of ICON_NAMES) {
    await copyDependencyFile(`lucide-static/icons/${iconName}.svg`, ICON_OUTPUT);
  }
  await copyFile(
    path.join(PROJECT_ROOT, "static/src/assets/icons/sprite.svg"),
    path.join(ICON_OUTPUT, "sprite.svg"),
  );
}

async function rebuildLocalAssets() {
  await rm(FONT_OUTPUT, { recursive: true, force: true });
  await rm(ICON_OUTPUT, { recursive: true, force: true });
  for (const directory of ["images", "documents"]) {
    await rm(path.join(AUTHORED_OUTPUT, directory), { recursive: true, force: true });
  }
  await Promise.all([copyFonts(), copyIcons()]);
  await mkdir(path.join(PROJECT_ROOT, "static/dist/js"), { recursive: true });
  await cp(
    path.join(PROJECT_ROOT, "static/src/js"),
    path.join(PROJECT_ROOT, "static/dist/js"),
    { recursive: true, force: true },
  );
  for (const directory of ["images", "documents"]) {
    await cp(path.join(AUTHORED_ASSETS, directory), path.join(AUTHORED_OUTPUT, directory), {
      recursive: true,
      force: true,
    });
  }
  console.log(`Copied ${FONT_FILES.length} fonts and ${ICON_NAMES.length} icons.`);
}

await rebuildLocalAssets();
