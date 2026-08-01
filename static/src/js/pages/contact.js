import { announce, egyptianMobileIsValid, emailIsValid, setBusy } from "../utilities/dom.js";

const MIN_MESSAGE_LENGTH = 20;
const PROTOTYPE_DELAY = 500;

const RULES = [
  {
    id: "contact-name",
    message: "اكتب اسمك كاملًا (حرفان على الأقل).",
    test: (value) => value.trim().length >= 2,
  },
  {
    id: "contact-phone",
    message: "اكتب رقم موبايل مصري صحيح يبدأ بـ 010 أو 011 أو 012 أو 015.",
    test: (value) => egyptianMobileIsValid(value),
  },
  {
    id: "contact-email",
    message: "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com",
    test: (value) => emailIsValid(value),
  },
  {
    id: "contact-subject",
    message: "اختر موضوع الرسالة من القائمة.",
    test: (value) => value.trim() !== "",
  },
  {
    id: "contact-message",
    message: `اكتب رسالتك في ${MIN_MESSAGE_LENGTH} حرفًا على الأقل.`,
    test: (value) => value.trim().length >= MIN_MESSAGE_LENGTH,
  },
];

function collectFields(form) {
  return RULES.map((rule) => ({
    rule,
    input: form.querySelector(`#${rule.id}`),
    error: form.querySelector(`#${rule.id}-error`),
  })).filter((field) => field.input && field.error);
}

function showError(field) {
  field.input.setAttribute("aria-invalid", "true");
  field.error.textContent = field.rule.message;
  field.error.hidden = false;
}

function clearError(field) {
  field.input.removeAttribute("aria-invalid");
  field.error.textContent = "";
  field.error.hidden = true;
}

function renderStatus(container, tone, message, retryLabel) {
  if (!container) return;
  container.textContent = "";
  const note = document.createElement("p");
  note.className = tone ? `status-message status-message--${tone}` : "status-message";
  note.textContent = message;
  if (retryLabel) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "btn btn--outline contact-status__retry";
    retry.dataset.contactRetry = "";
    retry.textContent = retryLabel;
    note.append(" ", retry);
  }
  container.append(note);
}

function clearStatus(container) {
  if (container) container.textContent = "";
}

function successMessage(fixture) {
  return fixture?.site?.contact?.form?.successMessage || "اكتمل التحقق محليًا، ولم تُرسل الرسالة.";
}

export function initialize(store, fixture) {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const fields = collectFields(form);
  if (!fields.length) return;

  const status = document.querySelector("[data-form-status='contact']");
  const submit = form.querySelector("[data-contact-submit]");

  // Linked Arabic messages replace native bubbles only once scripting is available.
  form.noValidate = true;

  fields.forEach((field) => {
    field.input.addEventListener("input", () => clearError(field));
    field.input.addEventListener("change", () => clearError(field));
  });

  const validate = () => fields.filter((field) => !field.rule.test(field.input.value));

  const reportInvalid = (invalid, moveFocus) => {
    fields.forEach(clearError);
    invalid.forEach(showError);
    const message = `راجع ${invalid.length} من حقول النموذج قبل المتابعة.`;
    renderStatus(status, "error", message);
    announce(message);
    if (moveFocus) invalid[0].input.focus();
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const invalid = validate();
    if (invalid.length) {
      reportInvalid(invalid, true);
      return;
    }
    fields.forEach(clearError);
    renderStatus(status, "", "جارٍ التحقق من الرسالة داخل الواجهة، ولن تُرسل إلى أي خدمة.");
    setBusy(submit, true, "جارٍ التحقق...");
    await new Promise((resolve) => window.setTimeout(resolve, PROTOTYPE_DELAY));
    setBusy(submit, false);
    const message = successMessage(fixture || store?.fixture);
    renderStatus(status, "success", message);
    announce(message);
  });

  form.addEventListener("reset", () => {
    window.setTimeout(() => {
      fields.forEach(clearError);
      clearStatus(status);
    }, 0);
  });

  status?.addEventListener("click", (event) => {
    if (!event.target.closest("[data-contact-retry]")) return;
    clearStatus(status);
    fields.forEach(clearError);
    fields[0].input.focus();
    announce("يمكنك تعديل الرسالة وإعادة المحاولة.");
  });

  if (document.body.dataset.state === "validation") {
    const invalid = validate();
    if (invalid.length) reportInvalid(invalid, false);
  } else if (document.body.dataset.state === "loading") {
    renderStatus(status, "", "جارٍ التحقق من الرسالة داخل الواجهة، ولن تُرسل إلى أي خدمة.");
    setBusy(submit, true, "جارٍ التحقق...");
  } else if (document.body.dataset.state === "unsent") {
    renderStatus(status, "success", successMessage(fixture || store?.fixture));
  } else if (["error", "recoverable-error"].includes(document.body.dataset.state)) {
    renderStatus(status, "error", "تعذّر إكمال التحقق المحلي. بقيت بيانات النموذج في الصفحة.", "إعادة المحاولة");
  }
}
