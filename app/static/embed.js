/* Embeddable lead-capture widget.
 * Usage: <script src="https://YOUR-HOST/embed.js" data-widget="wgt_xxx" async></script>
 * Everything renders inside a Shadow DOM so the host page's CSS cannot break it,
 * and user-visible text is only ever set with textContent (no HTML injection). */
(function () {
  "use strict";
  var script = document.currentScript;
  if (!script) return;
  var widgetId = script.getAttribute("data-widget");
  if (!widgetId) { console.error("[widget] missing data-widget attribute"); return; }

  var api = new URL(script.src).origin + "/public/widgets/" + encodeURIComponent(widgetId);
  var loadedAt = Date.now();
  var LABELS = { name: "Your name", email: "Email", phone: "Phone", message: "Message" };

  function h(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  }

  fetch(api + "/config")
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(render)
    .catch(function (e) { console.warn("[widget] not loaded:", e.message); });

  function render(cfg) {
    var host = h("div");
    var root = host.attachShadow({ mode: "open" });
    var style = h("style", {}, [
      ":host{all:initial;font-family:system-ui,sans-serif}",
      ".btn{position:fixed;right:20px;bottom:20px;z-index:2147483647;background:var(--c);color:#fff;border:0;border-radius:999px;padding:12px 20px;font-size:15px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.2)}",
      ".panel{position:fixed;right:20px;bottom:76px;z-index:2147483647;width:320px;max-width:calc(100vw - 40px);background:#fff;color:#111;border-radius:12px;padding:16px;box-shadow:0 8px 30px rgba(0,0,0,.25);display:none}",
      ".panel.open{display:block}",
      "h3{margin:0 0 12px;font-size:17px}",
      "label{display:block;font-size:13px;margin-bottom:10px}",
      "input,textarea{box-sizing:border-box;width:100%;margin-top:4px;padding:8px;border:1px solid #ccc;border-radius:6px;font:inherit}",
      ".hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}",
      ".send{width:100%;background:var(--c);color:#fff;border:0;border-radius:6px;padding:10px;font-size:15px;cursor:pointer}",
      ".send[disabled]{opacity:.6}",
      ".msg{font-size:13px;margin-top:8px;min-height:16px}"
    ].join("\n"));
    root.appendChild(style);
    host.style.setProperty("--c", cfg.theme_color);

    var btn = h("button", { "class": "btn", type: "button" }, cfg.button_text);
    var panel = h("div", { "class": "panel" });
    panel.appendChild(h("h3", {}, cfg.title));
    var form = h("form", { novalidate: "" });
    var inputs = {};

    cfg.fields.forEach(function (f) {
      var label = h("label", {}, LABELS[f] || f);
      var input = f === "message" ? h("textarea", { rows: "4", maxlength: "2000" }) : h("input", { type: f === "email" ? "email" : f === "phone" ? "tel" : "text", maxlength: "100" });
      if (f === "email") input.required = true;
      label.appendChild(input);
      form.appendChild(label);
      inputs[f] = input;
    });

    // honeypot: invisible to people, tempting to bots
    var hp = h("div", { "class": "hp", "aria-hidden": "true" });
    var hpInput = h("input", { type: "text", tabindex: "-1", autocomplete: "off" });
    hp.appendChild(hpInput);
    form.appendChild(hp);

    var send = h("button", { "class": "send", type: "submit" }, "Send");
    var msg = h("div", { "class": "msg" });
    form.appendChild(send);
    form.appendChild(msg);
    panel.appendChild(form);

    btn.addEventListener("click", function () { panel.classList.toggle("open"); });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var body = { website: hpInput.value, elapsed_ms: Date.now() - loadedAt };
      Object.keys(inputs).forEach(function (k) { body[k] = inputs[k].value; });
      send.disabled = true; msg.textContent = "Sending...";
      fetch(api + "/leads", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        .then(function (r) {
          if (r.status === 201) { form.reset(); msg.textContent = "Thanks! We'll be in touch."; return; }
          msg.textContent = r.status === 422 ? "Please check your details." :
                            r.status === 429 ? "Too many attempts. Try again soon." : "Something went wrong.";
        })
        .catch(function () { msg.textContent = "Network error. Please try again."; })
        .then(function () { send.disabled = false; });
    });

    root.appendChild(btn);
    root.appendChild(panel);
    document.body.appendChild(host);
  }
})();
