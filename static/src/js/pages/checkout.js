import {
  announce,
  egyptianMobileIsValid,
  emailIsValid,
  setBusy,
} from "../utilities/dom.js";

const STEPS = ["shipping", "payment", "review"];

function formatCurrency(amount, fixture) {
  const value = new Intl.NumberFormat(fixture.site.locale, { maximumFractionDigits: 0 }).format(amount);
  return `${value} ${fixture.site.currency.label}`;
}

function productMap(fixture) {
  return new Map(fixture.products.map((product) => [product.id, product]));
}

function visibleCart(store, fixture) {
  const products = productMap(fixture);
  const lines = store.snapshot().cart.items.filter((line) => products.has(line.productId));
  return { lines, products };
}

function calculateTotals(lines, products, store, fixture) {
  const subtotal = lines.reduce(
    (sum, line) => sum + products.get(line.productId).price * line.quantity,
    0,
  );
  const coupon = fixture.site.couponPrototype;
  const discount = store.snapshot().cart.coupon === coupon.acceptedCode
    ? Math.round(subtotal * coupon.discountRate)
    : 0;
  const total = subtotal - discount;
  const vat = Math.round((total * fixture.site.vatRate) / (1 + fixture.site.vatRate));
  return { subtotal, discount, total, vat };
}

function finishLabel(product, finishId) {
  return product.finishes.find((finish) => finish.id === finishId)?.label || "الخيار الافتراضي";
}

function summaryLine(line, product, fixture) {
  const template = document.querySelector("#checkout-line-template");
  const element = template.content.firstElementChild.cloneNode(true);
  const image = element.querySelector("[data-checkout-line-image]");
  image.src = product.images[0].path;
  image.alt = product.images[0].alt;
  element.querySelector("[data-checkout-line-name]").textContent = product.name;
  element.querySelector("[data-checkout-line-meta]").textContent = `الكمية: ${line.quantity} · ${finishLabel(product, line.finishId)}`;
  element.querySelector("[data-checkout-line-price]").textContent = formatCurrency(product.price * line.quantity, fixture);
  return element;
}

function shippingOption(fixture, optionId) {
  return fixture.shippingOptions.find((option) => option.id === optionId);
}

function renderTotals(root, totals, state, fixture) {
  root.querySelector("[data-checkout-subtotal]").textContent = formatCurrency(totals.subtotal, fixture);
  root.querySelector("[data-checkout-discount]").textContent = `− ${formatCurrency(totals.discount, fixture)}`;
  root.querySelector("[data-checkout-discount-row]").hidden = totals.discount === 0;
  root.querySelector("[data-checkout-vat]").textContent = formatCurrency(totals.vat, fixture);
  root.querySelector("[data-checkout-total]").textContent = formatCurrency(totals.total, fixture);
  const selected = shippingOption(fixture, state.shippingMethod);
  root.querySelector("[data-checkout-shipping]").textContent = selected?.label || "يُحدد حسب الاختيار";
  const threshold = fixture.site.freeShippingThreshold;
  const note = totals.subtotal >= threshold
    ? "السلة مؤهلة لخيار الشحن المجاني التجريبي."
    : `أضف ${formatCurrency(threshold - totals.subtotal, fixture)} لظهور خيار الشحن المجاني.`;
  root.querySelector("[data-checkout-shipping-note]").textContent = note;
}

function renderCart(root, store, state, fixture) {
  const { lines, products } = visibleCart(store, fixture);
  const empty = lines.length === 0;
  root.querySelector("[data-checkout-loading]").hidden = true;
  root.querySelector("[data-checkout-empty]").hidden = !empty;
  root.querySelector("[data-checkout-layout]").hidden = empty;
  root.querySelector(".checkout-stepper-wrap").hidden = empty;
  root.querySelector("[data-checkout-lines]").replaceChildren(
    ...lines.map((line) => summaryLine(line, products.get(line.productId), fixture)),
  );
  const totals = calculateTotals(lines, products, store, fixture);
  renderTotals(root, totals, state, fixture);
  root.setAttribute("aria-busy", "false");
  return totals;
}

function formValue(form, name) {
  return form.elements[name]?.value.trim() || "";
}

function shippingValues(form) {
  return {
    fullName: formValue(form, "fullName"),
    email: formValue(form, "email"),
    mobile: formValue(form, "mobile"),
    governorate: formValue(form, "governorate"),
    city: formValue(form, "city"),
    areaKey: formValue(form, "areaKey"),
    street: formValue(form, "street"),
    building: formValue(form, "building"),
    landmark: formValue(form, "landmark"),
    shippingMethod: form.querySelector("input[name='shippingMethod']:checked")?.value || "",
    installation: form.elements.installation.checked,
    acknowledgement: form.elements.acknowledgement.checked,
  };
}

function hasArabicLetter(value) {
  return /[\u0600-\u06ff]/u.test(value);
}

function normalizeArabicDigits(value) {
  return value
    .replace(/[٠-٩]/g, (digit) => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)))
    .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)));
}

function shippingErrors(values) {
  const errors = [];
  if (values.fullName.length < 2 || !hasArabicLetter(values.fullName)) errors.push(["fullName", "اكتب الاسم بالكامل بالعربية."]);
  if (!emailIsValid(values.email)) errors.push(["email", "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com."]);
  if (!egyptianMobileIsValid(normalizeArabicDigits(values.mobile))) errors.push(["mobile", "اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا."]);
  if (!values.governorate) errors.push(["governorate", "اختر المحافظة."]);
  if (values.city.length < 2) errors.push(["city", "اكتب اسم المدينة أو المركز."]);
  if (values.street.length < 4) errors.push(["street", "اكتب اسم الشارع والعنوان التفصيلي."]);
  if (!values.building) errors.push(["building", "اكتب رقم المبنى."]);
  if (!values.shippingMethod) errors.push(["shippingMethod", "اختر طريقة الشحن."]);
  if (!values.acknowledgement) errors.push(["acknowledgement", "أكد فهمك أن هذه واجهة تجريبية."]);
  return errors;
}

function fieldForError(form, name) {
  if (name === "shippingMethod") return form.querySelector("input[name='shippingMethod']:not([disabled])");
  return form.elements[name];
}

function clearErrors(form) {
  form.querySelectorAll("[aria-invalid='true']").forEach((field) => field.removeAttribute("aria-invalid"));
  form.querySelectorAll(".field-error").forEach((error) => { error.hidden = true; error.textContent = ""; });
  const summary = form.querySelector("[data-error-summary]");
  summary.hidden = true;
  summary.querySelector("[data-error-summary-list]").replaceChildren();
}

function showFieldError(form, name, message) {
  const field = fieldForError(form, name);
  if (name === "shippingMethod") {
    form.querySelectorAll("input[name='shippingMethod']:not([disabled])").forEach((input) => input.setAttribute("aria-invalid", "true"));
  } else {
    field?.setAttribute("aria-invalid", "true");
  }
  const errorKey = name === "fullName" ? "name" : name;
  const error = form.querySelector(`#checkout-${errorKey}-error`);
  error.textContent = message;
  error.hidden = false;
  return field;
}

function showShippingErrors(form, errors) {
  clearErrors(form);
  const summary = form.querySelector("[data-error-summary]");
  const list = summary.querySelector("[data-error-summary-list]");
  errors.forEach(([name, message]) => {
    const field = showFieldError(form, name, message);
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${field.id}`;
    link.textContent = message;
    item.append(link);
    list.append(item);
  });
  summary.hidden = false;
  summary.focus();
  announce(`يوجد ${errors.length} حقول تحتاج إلى مراجعة.`);
}

function updateAreaOptions(root, fixture, preferredArea = "") {
  const form = root.querySelector("[data-shipping-form]");
  const governorate = formValue(form, "governorate");
  const select = form.elements.areaKey;
  const areas = fixture.serviceEligibility.areas.filter((area) => area.governorateKey === governorate);
  const prompt = new Option("اختر المنطقة إن كانت مدرجة", "");
  select.replaceChildren(prompt, ...areas.map((area) => new Option(area.label, area.key)));
  select.value = areas.some((area) => area.key === preferredArea) ? preferredArea : "";
  select.disabled = areas.length === 0;
  root.querySelector("[data-area-field]").hidden = areas.length === 0;
}

function updateServiceEligibility(root, fixture, totals, state) {
  const form = root.querySelector("[data-shipping-form]");
  const values = shippingValues(form);
  const sameDayEligible = fixture.serviceEligibility.sameDayAreaKeys.includes(values.areaKey);
  const installationEligible = fixture.serviceEligibility.installationGovernorateKeys.includes(values.governorate);
  const freeMinimum = shippingOption(fixture, "shipping-free")?.eligibility.minimumSubtotal || 0;
  setChoiceEligibility(form, "shipping-same-day", sameDayEligible);
  setChoiceEligibility(form, "shipping-free", totals.subtotal >= freeMinimum);
  const installation = root.querySelector("[data-installation-fieldset]");
  installation.hidden = !installationEligible;
  installation.disabled = !installationEligible;
  if (!installationEligible) form.elements.installation.checked = false;
  state.shippingMethod = form.querySelector("input[name='shippingMethod']:checked")?.value || "";
  state.installation = form.elements.installation.checked;
}

function setChoiceEligibility(form, optionId, eligible) {
  const label = form.querySelector(`[data-shipping-option='${optionId}']`);
  if (!label) return;
  const input = label.querySelector("input");
  label.hidden = !eligible;
  input.disabled = !eligible;
  if (!eligible) input.checked = false;
}

function seedShippingForm(root, fixture, totals) {
  const form = root.querySelector("[data-shipping-form]");
  const account = fixture.prototypeAccounts.find((item) => item.mode === "signed-in");
  const address = account?.addresses[0];
  if (!account?.identity || !address) return;
  form.elements.fullName.value = account.identity.name;
  form.elements.email.value = account.identity.email;
  form.elements.mobile.value = account.identity.phone;
  form.elements.governorate.value = address.governorateKey;
  updateAreaOptions(root, fixture, address.areaKey);
  const area = fixture.serviceEligibility.areas.find((item) => item.key === address.areaKey);
  form.elements.city.value = area?.label || "";
  form.elements.street.value = address.street;
  form.elements.building.value = address.building;
  form.elements.acknowledgement.checked = true;
  const shippingId = totals.subtotal >= fixture.site.freeShippingThreshold ? "shipping-free" : "shipping-standard";
  form.querySelector(`input[value='${shippingId}']`).checked = true;
}

function setStepInUrl(step) {
  const url = new URL(window.location.href);
  if (step === "shipping") url.searchParams.delete("step");
  else url.searchParams.set("step", step);
  window.history.replaceState({}, "", url);
}

function renderStepper(root, state) {
  const activeIndex = STEPS.indexOf(state.step);
  root.querySelectorAll("[data-checkout-step-item]").forEach((item, index) => {
    const button = item.querySelector("button");
    const stepState = index < activeIndex ? "complete" : index === activeIndex ? "active" : "upcoming";
    item.dataset.state = stepState;
    button.disabled = index > activeIndex;
    if (index === activeIndex) button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  });
}

function goToStep(root, state, step, focus = true) {
  state.step = step;
  root.querySelectorAll("[data-checkout-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.checkoutPanel !== step;
  });
  renderStepper(root, state);
  setStepInUrl(step);
  if (step === "review") renderReview(root, state);
  if (focus) root.querySelector(`[data-checkout-panel='${step}'] h2`)?.focus();
  announce(`الخطوة الحالية: ${root.querySelector(`[data-checkout-step='${step}'] b`).textContent}`);
}

function definitionRows(container, rows) {
  container.replaceChildren(...rows.map(([term, value]) => {
    const row = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = term;
    dd.textContent = value || "—";
    row.append(dt, dd);
    return row;
  }));
}

function labelByKey(records, key, idField = "id") {
  return records.find((record) => record[idField] === key)?.label || "—";
}

function renderReview(root, state) {
  const fixture = state.fixture;
  const values = shippingValues(root.querySelector("[data-shipping-form]"));
  const governorate = labelByKey(fixture.governorates, values.governorate, "key");
  const area = labelByKey(fixture.serviceEligibility.areas, values.areaKey, "key");
  definitionRows(root.querySelector("[data-review-customer]"), [
    ["الاسم", values.fullName], ["البريد", values.email], ["الموبايل", values.mobile],
    ["العنوان", `${governorate}، ${area === "—" ? values.city : area}، ${values.street}، مبنى ${values.building}`],
  ]);
  definitionRows(root.querySelector("[data-review-delivery]"), [
    ["طريقة الشحن", labelByKey(fixture.shippingOptions, state.shippingMethod)],
    ["التركيب", state.installation ? "مطلوب للمعاينة التجريبية" : "غير مطلوب"],
  ]);
  definitionRows(root.querySelector("[data-review-payment]"), [
    ["الطريقة المختارة", labelByKey(fixture.paymentOptions, state.paymentMethod)],
    ["الحالة", "اختيار واجهة غير متصل بأي مزود"],
  ]);
}

function submitShipping(event, root, state) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = shippingValues(form);
  const errors = shippingErrors(values);
  if (errors.length) {
    showShippingErrors(form, errors);
    return;
  }
  clearErrors(form);
  Object.assign(state, values);
  updateServiceEligibility(root, state.fixture, state.totals, state);
  goToStep(root, state, "payment");
}

function submitPayment(event, root, state) {
  event.preventDefault();
  const form = event.currentTarget;
  const selected = form.querySelector("input[name='paymentMethod']:checked");
  const error = form.querySelector("[data-payment-error]");
  if (!selected) {
    error.textContent = "اختر طريقة دفع لمراجعة الواجهة.";
    error.hidden = false;
    form.querySelector("input[name='paymentMethod']")?.focus();
    announce(error.textContent);
    return;
  }
  error.hidden = true;
  state.paymentMethod = selected.value;
  goToStep(root, state, "review");
}

function addRecoveryLinks(container) {
  const actions = document.createElement("div");
  actions.className = "checkout-final-state__actions";
  const cart = document.createElement("a");
  cart.className = "btn btn--outline";
  cart.href = "/cart/";
  cart.textContent = "العودة إلى السلة";
  const shop = document.createElement("a");
  shop.className = "btn btn--primary";
  shop.href = "/shop/";
  shop.textContent = "متابعة التسوق";
  actions.append(cart, shop);
  container.append(actions);
}

function showUnavailable(root, moveFocus = true) {
  const state = root.querySelector("[data-final-state]");
  const heading = document.createElement("strong");
  heading.textContent = "إرسال الطلب غير متاح في هذا النموذج";
  const message = document.createElement("p");
  message.textContent = "لم يتم إنشاء طلب أو تحصيل مبلغ أو إرسال بيانات. يمكنك تعديل اختياراتك أو العودة إلى السلة بأمان.";
  state.className = "checkout-final-state status-message";
  state.replaceChildren(heading, message);
  addRecoveryLinks(state);
  state.hidden = false;
  if (moveFocus) state.focus();
  announce("إرسال الطلب غير متاح، ولم يتم إنشاء أي طلب أو معاملة.");
}

function showRecoverableError(root) {
  const state = root.querySelector("[data-final-state]");
  const heading = document.createElement("strong");
  heading.textContent = "تعذر تجهيز حالة الإرسال التجريبية";
  const message = document.createElement("p");
  message.textContent = "بياناتك ما زالت داخل هذه الصفحة فقط. يمكنك إعادة المحاولة من دون فقد اختياراتك.";
  const retry = document.createElement("button");
  retry.type = "button";
  retry.className = "btn btn--outline";
  retry.textContent = "إعادة المحاولة";
  retry.addEventListener("click", () => {
    state.hidden = true;
    root.querySelector("[data-checkout-final]").focus();
    announce("يمكنك إعادة معاينة حالة الإرسال الآن.");
  });
  state.className = "checkout-final-state status-message status-message--error";
  state.replaceChildren(heading, message, retry);
  state.hidden = false;
}

function initializeFinalState(root) {
  const button = root.querySelector("[data-checkout-final]");
  const qaState = root.dataset.qaState;
  if (qaState === "loading") setBusy(button, true, "جارٍ عرض الحالة…");
  if (qaState === "unavailable") showUnavailable(root, false);
  if (["error", "recoverable-error"].includes(qaState)) showRecoverableError(root);
  button.addEventListener("click", () => {
    setBusy(button, true, "جارٍ عرض الحالة…");
    window.setTimeout(() => {
      setBusy(button, false);
      showUnavailable(root);
    }, 450);
  });
}

function bindShippingInteractions(root, state) {
  const { fixture } = state;
  const form = root.querySelector("[data-shipping-form]");
  form.addEventListener("submit", (event) => submitShipping(event, root, state));
  form.elements.governorate.addEventListener("change", () => {
    updateAreaOptions(root, fixture);
    updateServiceEligibility(root, fixture, state.totals, state);
  });
  form.elements.areaKey.addEventListener("change", () => {
    const area = fixture.serviceEligibility.areas.find((item) => item.key === form.elements.areaKey.value);
    if (area && !form.elements.city.value.trim()) form.elements.city.value = area.label;
    updateServiceEligibility(root, fixture, state.totals, state);
  });
  form.addEventListener("change", () => {
    updateServiceEligibility(root, fixture, state.totals, state);
    renderTotals(root, state.totals, state, fixture);
  });
}

function bindStepControls(root, state) {
  root.querySelectorAll("[data-go-step]").forEach((button) => {
    button.addEventListener("click", () => goToStep(root, state, button.dataset.goStep));
  });
  root.querySelectorAll("[data-checkout-step]").forEach((button) => {
    button.addEventListener("click", () => goToStep(root, state, button.dataset.checkoutStep));
  });
}

export function initialize(store, fixture) {
  const root = document.querySelector("[data-checkout-root]");
  if (!root) return;
  const initialStep = STEPS.includes(root.dataset.initialStep) ? root.dataset.initialStep : "shipping";
  const state = { step: initialStep, shippingMethod: "", installation: false, paymentMethod: "", fixture };
  state.totals = renderCart(root, store, state, fixture);
  if (initialStep !== "shipping") seedShippingForm(root, fixture, state.totals);
  updateServiceEligibility(root, fixture, state.totals, state);
  Object.assign(state, shippingValues(root.querySelector("[data-shipping-form]")));
  if (initialStep === "review") {
    const payment = root.querySelector("input[name='paymentMethod']");
    payment.checked = true;
    state.paymentMethod = payment.value;
  }
  bindShippingInteractions(root, state);
  root.querySelector("[data-payment-form]").addEventListener("submit", (event) => submitPayment(event, root, state));
  bindStepControls(root, state);
  initializeFinalState(root);
  goToStep(root, state, initialStep, false);
  document.addEventListener("zakey:cart-change", () => {
    state.totals = renderCart(root, store, state, fixture);
    updateServiceEligibility(root, fixture, state.totals, state);
  });
}
