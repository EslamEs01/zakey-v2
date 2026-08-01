import { announce, egyptianMobileIsValid, emailIsValid, setBusy } from "../utilities/dom.js";

const TAB_IDS = ["orders", "wishlist", "addresses", "payment", "settings"];
const PROTOTYPE_DELAY = 450;
const KEY_STEPS = { ArrowUp: -1, ArrowDown: 1, ArrowLeft: 1, ArrowRight: -1 };

const SETTINGS_RULES = [
  {
    id: "account-settings-name",
    message: "اكتب اسمًا معروضًا من حرفين على الأقل.",
    test: (value) => value.trim().length >= 2,
  },
  {
    id: "account-settings-phone",
    message: "اكتب رقم موبايل مصري صحيح يبدأ بـ 010 أو 011 أو 012 أو 015.",
    test: (value) => egyptianMobileIsValid(value),
  },
  {
    id: "account-settings-email",
    message: "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com",
    test: (value) => emailIsValid(value),
  },
];

function resolveTab(value) {
  return TAB_IDS.includes(value) ? value : TAB_IDS[0];
}

function renderStatus(container, tone, message) {
  if (!container) return;
  container.textContent = "";
  const note = document.createElement("p");
  note.className = tone ? `status-message status-message--${tone}` : "status-message";
  note.textContent = message;
  container.append(note);
}

function showError(input, error, message) {
  if (!input || !error) return;
  input.setAttribute("aria-invalid", "true");
  error.textContent = message;
  error.hidden = false;
}

function clearError(input, error) {
  if (!input || !error) return;
  input.removeAttribute("aria-invalid");
  error.textContent = "";
  error.hidden = true;
}

function persistAccountState(store, changes) {
  store?.setAccountState(changes);
}

function setupTabs(page, store) {
  const list = page.querySelector("[data-account-tabs]");
  const host = page.querySelector("[data-account-panels]");
  if (!list || !host) return;

  const tabs = [...list.querySelectorAll("[data-account-tab-id]")].filter((tab) =>
    document.getElementById(tab.dataset.accountPanel),
  );
  if (tabs.length < 2) return;

  list.setAttribute("role", "tablist");
  list.setAttribute("aria-orientation", "vertical");
  tabs.forEach((tab) => {
    const panel = document.getElementById(tab.dataset.accountPanel);
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-controls", panel.id);
    tab.removeAttribute("aria-current");
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("tabindex", "-1");
    panel.setAttribute("aria-labelledby", tab.id);
  });

  const select = (id, options = {}) => {
    const selected = tabs.find((tab) => tab.dataset.accountTabId === id);
    if (!selected) return;
    tabs.forEach((tab) => {
      const panel = document.getElementById(tab.dataset.accountPanel);
      const active = tab === selected;
      tab.setAttribute("aria-selected", String(active));
      tab.setAttribute("tabindex", active ? "0" : "-1");
      tab.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
    page.dataset.accountTab = id;
    persistAccountState(store, { tab: id });
    if (options.updateUrl && window.history?.replaceState) {
      const url = new URL(window.location.href);
      url.searchParams.set("state", "signed-in");
      url.searchParams.set("tab", id);
      window.history.replaceState(null, "", `${url.pathname}${url.search}`);
    }
    if (options.announce) announce(`تم فتح قسم ${selected.textContent.trim()}`);
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", (event) => {
      event.preventDefault();
      select(tab.dataset.accountTabId, { updateUrl: true, announce: true });
      tab.focus();
    });
    tab.addEventListener("keydown", (event) => {
      let target = null;
      if (event.key === "Home") target = tabs[0];
      else if (event.key === "End") target = tabs[tabs.length - 1];
      else if (KEY_STEPS[event.key] !== undefined) {
        target = tabs[(index + KEY_STEPS[event.key] + tabs.length) % tabs.length];
      }
      if (!target) return;
      event.preventDefault();
      target.focus();
      select(target.dataset.accountTabId, { updateUrl: true, announce: true });
    });
  });

  select(resolveTab(page.dataset.accountTab));
}

function setupWishlistPanel(store, products) {
  const empty = document.querySelector("[data-account-wishlist-empty]");
  const list = document.querySelector("[data-account-wishlist-list]");
  const items = document.querySelector("[data-account-wishlist-items]");
  const summary = document.querySelector("[data-account-wishlist-summary]");
  if (!empty || !list || !items || !summary || !store) return;

  const render = () => {
    const saved = store.snapshot().wishlist.productIds;
    items.textContent = "";
    saved.forEach((id) => {
      const product = products.find((entry) => entry.id === id);
      const item = document.createElement("li");
      item.textContent = product ? product.name : id;
      items.append(item);
    });
    summary.textContent = `عدد المنتجات المحفوظة في هذا المتصفح: ${saved.length}`;
    empty.hidden = saved.length > 0;
    list.hidden = saved.length === 0;
  };

  render();
  document.addEventListener("zakey:wishlist-change", render);
}

function setupUnavailableControls() {
  document.querySelectorAll("[data-account-unavailable]").forEach((button) => {
    button.addEventListener("click", () => {
      const status = button.closest(".account-panel")?.querySelector("[data-account-status]");
      const message = `${button.dataset.accountUnavailable} غير متاح في هذه الواجهة، لأنه يحتاج خدمة خلفية خارج نطاق النموذج.`;
      renderStatus(status, "", message);
      announce(message);
    });
  });
}

function setupSettingsForm() {
  const form = document.querySelector("[data-account-settings]");
  if (!form) return;

  const fields = SETTINGS_RULES.map((rule) => ({
    rule,
    input: form.querySelector(`#${rule.id}`),
    error: form.querySelector(`#${rule.id}-error`),
  })).filter((field) => field.input && field.error);
  if (!fields.length) return;

  const status = form.parentElement?.querySelector("[data-account-status]");
  const submit = form.querySelector("[data-account-settings-submit]");
  form.noValidate = true;

  fields.forEach((field) => {
    field.input.addEventListener("input", () => clearError(field.input, field.error));
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const invalid = fields.filter((field) => !field.rule.test(field.input.value));
    fields.forEach((field) => clearError(field.input, field.error));
    if (invalid.length) {
      invalid.forEach((field) => showError(field.input, field.error, field.rule.message));
      const message = `راجع ${invalid.length} من حقول الإعدادات قبل المتابعة.`;
      renderStatus(status, "error", message);
      announce(message);
      invalid[0].input.focus();
      return;
    }
    setBusy(submit, true, "جارٍ التحقق...");
    await new Promise((resolve) => window.setTimeout(resolve, PROTOTYPE_DELAY));
    setBusy(submit, false);
    const message = "اكتمل التحقق محليًا. لم تُحفظ أي بيانات ولم تُرسل إلى أي خدمة.";
    renderStatus(status, "success", message);
    announce(message);
  });

  form.addEventListener("reset", () => {
    window.setTimeout(() => {
      fields.forEach((field) => clearError(field.input, field.error));
      if (status) status.textContent = "";
    }, 0);
  });
}

function setupDemoForm() {
  const form = document.querySelector("[data-account-demo-form]");
  if (!form) return;
  const input = form.querySelector("#account-demo-email");
  const error = form.querySelector("#account-demo-error");
  if (!input || !error) return;

  form.noValidate = true;
  input.addEventListener("input", () => clearError(input, error));
  form.addEventListener("submit", (event) => {
    const value = input.value.trim();
    if (value === "" || emailIsValid(value)) {
      clearError(input, error);
      return;
    }
    event.preventDefault();
    const message = "اكتب بريدًا إلكترونيًا صحيحًا أو اترك الحقل فارغًا لفتح العرض.";
    showError(input, error, message);
    input.focus();
    announce(message);
  });
}

export function initialize(store, fixture) {
  const page = document.querySelector(".account-page");
  if (!page) return;

  const products = fixture?.products || store?.fixture?.products || [];
  persistAccountState(store, {
    mode: page.dataset.accountMode === "signed-in" ? "signed-in" : "signed-out",
    tab: resolveTab(page.dataset.accountTab),
  });

  setupTabs(page, store);
  setupWishlistPanel(store, products);
  setupUnavailableControls();
  setupSettingsForm();
  setupDemoForm();
}
