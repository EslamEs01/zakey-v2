import { announce, egyptianMobileIsValid, emailIsValid } from "../utilities/dom.js";

/**
 * Contact form enhancement (T-1206/T-1607, FR-098, FR-136).
 *
 * The prototype's handler called `preventDefault()`, waited 350 ms and then
 * reported success while stating the message had not been sent anywhere. The
 * form now POSTs to a real endpoint that stores a `ContactMessage`.
 *
 * What is left is early feedback: catch obviously invalid fields before the
 * round trip, with the same Arabic messages the server uses. If everything
 * looks right the submit proceeds normally and the server validates again.
 */

const MIN_MESSAGE_LENGTH = 20;

const RULES = [
  { name: "name", test: (value) => value.trim().length >= 2, message: "اكتب الاسم بالكامل بالعربية." },
  { name: "email", test: emailIsValid, message: "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com." },
  {
    name: "phone",
    test: (value) => !value.trim() || egyptianMobileIsValid(value),
    message: "اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا.",
  },
  { name: "subject", test: (value) => Boolean(value), message: "اختر موضوعًا." },
  {
    name: "message",
    test: (value) => value.trim().length >= MIN_MESSAGE_LENGTH,
    message: `اكتب ${MIN_MESSAGE_LENGTH} حرفًا على الأقل.`,
  },
];

function errorNode(form, name) {
  return form.querySelector(`#contact-${name}-error`);
}

function clearError(form, name) {
  const input = form.elements[name];
  input?.removeAttribute("aria-invalid");
  const node = errorNode(form, name);
  if (node) node.hidden = true;
}

function showError(form, rule) {
  const input = form.elements[rule.name];
  input?.setAttribute("aria-invalid", "true");
  const node = errorNode(form, rule.name);
  if (node) {
    node.textContent = rule.message;
    node.hidden = false;
  }
}

export function initialize() {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  // Native bubbles are replaced by the linked Arabic messages only when
  // scripting is available; without it the browser's own validation applies.
  form.noValidate = true;

  RULES.forEach((rule) => {
    const input = form.elements[rule.name];
    if (!input) return;
    input.addEventListener("input", () => clearError(form, rule.name));
    input.addEventListener("change", () => clearError(form, rule.name));
  });

  form.addEventListener("submit", (event) => {
    const invalid = RULES.filter((rule) => {
      const input = form.elements[rule.name];
      return input && !rule.test(input.value);
    });
    if (!invalid.length) return; // let the browser submit

    event.preventDefault();
    RULES.forEach((rule) => clearError(form, rule.name));
    invalid.forEach((rule) => showError(form, rule));
    const message = `راجع ${invalid.length} من حقول النموذج قبل المتابعة.`;
    announce(message);
    form.elements[invalid[0].name].focus();
  });

  form.addEventListener("reset", () => {
    window.setTimeout(() => RULES.forEach((rule) => clearError(form, rule.name)), 0);
  });
}
