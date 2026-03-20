window.ChatDock = window.ChatDock || (function createChatDock() {
  function createStyles(primaryColor) {
    if (document.getElementById("chatdock-widget-styles")) {
      return;
    }
    const style = document.createElement("style");
    style.id = "chatdock-widget-styles";
    style.textContent = `
      .chatdock-launcher {
        position: fixed;
        right: 24px;
        bottom: 24px;
        width: 56px;
        height: 56px;
        border: 0;
        border-radius: 18px;
        background: ${primaryColor};
        color: #fff;
        box-shadow: 0 20px 35px rgba(15, 23, 42, 0.22);
        cursor: pointer;
        z-index: 9998;
      }
      .chatdock-panel {
        position: fixed;
        right: 24px;
        bottom: 96px;
        width: min(360px, calc(100vw - 24px));
        max-height: calc(100vh - 120px);
        height: min(560px, calc(100vh - 120px));
        background: #f8fafc;
        border: 1px solid #d5dce8;
        border-radius: 20px;
        box-shadow: 0 30px 60px rgba(15, 23, 42, 0.24);
        overflow: hidden;
        display: none;
        flex-direction: column;
        z-index: 9998;
        font-family: Arial, sans-serif;
      }
      .chatdock-panel.is-open {
        display: flex;
      }
      .chatdock-header {
        padding: 16px 18px;
        background: #030824;
        color: #fff;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .chatdock-header-title {
        font-size: 15px;
        font-weight: 700;
      }
      .chatdock-header-subtitle {
        margin-top: 4px;
        font-size: 12px;
        color: rgba(255,255,255,0.72);
      }
      .chatdock-close {
        border: 0;
        background: transparent;
        color: #fff;
        font-size: 20px;
        cursor: pointer;
      }
      .chatdock-messages {
        flex: 1;
        overflow: auto;
        padding: 16px;
        background: #eef3f8;
        scrollbar-width: none;
        -ms-overflow-style: none;
      }
      .chatdock-messages::-webkit-scrollbar {
        width: 0;
        height: 0;
      }
      .chatdock-message {
        margin-bottom: 12px;
        display: flex;
      }
      .chatdock-message.user {
        justify-content: flex-end;
      }
      .chatdock-bubble {
        max-width: 82%;
        padding: 10px 12px;
        border-radius: 14px;
        font-size: 13px;
        line-height: 1.45;
        white-space: pre-wrap;
      }
      .chatdock-message.assistant .chatdock-bubble {
        background: #ffffff;
        color: #10203d;
        border: 1px solid #d7dfeb;
      }
      .chatdock-message.user .chatdock-bubble {
        background: ${primaryColor};
        color: #fff;
      }
      .chatdock-bubble h1,
      .chatdock-bubble h2,
      .chatdock-bubble h3 {
        margin: 0 0 8px;
        line-height: 1.3;
        color: inherit;
      }
      .chatdock-bubble h1 { font-size: 16px; }
      .chatdock-bubble h2 { font-size: 15px; }
      .chatdock-bubble h3 { font-size: 14px; }
      .chatdock-bubble p {
        margin: 0 0 8px;
      }
      .chatdock-bubble ul,
      .chatdock-bubble ol {
        margin: 0 0 8px;
        padding-left: 18px;
      }
      .chatdock-bubble li {
        margin: 0 0 4px;
      }
      .chatdock-footer {
        padding: 12px;
        border-top: 1px solid #d6deea;
        background: #f8fafc;
      }
      .chatdock-form {
        display: flex;
        gap: 8px;
      }
      .chatdock-input {
        flex: 1;
        border: 1px solid #cfd8e4;
        border-radius: 12px;
        height: 42px;
        padding: 0 12px;
        font-size: 13px;
      }
      .chatdock-send {
        border: 0;
        border-radius: 12px;
        min-width: 88px;
        background: #030824;
        color: #fff;
        font-weight: 700;
        cursor: pointer;
      }
      .chatdock-note {
        margin-top: 8px;
        font-size: 11px;
        color: #5a6f90;
      }
    `;
    document.head.appendChild(style);
  }

  function appendMessage(container, role, text) {
    const row = document.createElement("div");
    row.className = "chatdock-message " + role;
    const bubble = document.createElement("div");
    bubble.className = "chatdock-bubble";
    if (role === "assistant") {
      bubble.innerHTML = renderMarkdown(text);
    } else {
      bubble.textContent = text;
    }
    row.appendChild(bubble);
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
  }

  function createAssistantMessage(container) {
    const row = document.createElement("div");
    row.className = "chatdock-message assistant";
    const bubble = document.createElement("div");
    bubble.className = "chatdock-bubble";
    row.appendChild(bubble);
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return bubble;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderInline(text) {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  }

  function renderMarkdown(markdown) {
    const lines = String(markdown || "").replace(/\r/g, "").split("\n");
    const html = [];
    let inList = false;
    let listType = "";
    const plainSectionHeadings = new Set(["title", "key points", "details", "summary"]);

    function closeList() {
      if (inList) {
        html.push(listType === "ol" ? "</ol>" : "</ul>");
        inList = false;
        listType = "";
      }
    }

    for (let i = 0; i < lines.length; i += 1) {
      const raw = lines[i];
      const line = raw.trim();

      if (!line) {
        closeList();
        continue;
      }

      if (line.startsWith("### ")) {
        closeList();
        html.push("<h3>" + renderInline(line.slice(4)) + "</h3>");
        continue;
      }
      if (line.startsWith("## ")) {
        closeList();
        html.push("<h2>" + renderInline(line.slice(3)) + "</h2>");
        continue;
      }
      if (line.startsWith("# ")) {
        closeList();
        html.push("<h1>" + renderInline(line.slice(2)) + "</h1>");
        continue;
      }

      if (plainSectionHeadings.has(line.toLowerCase())) {
        closeList();
        html.push("<h3>" + renderInline(line) + "</h3>");
        continue;
      }

      const ordered = line.match(/^\d+\.\s+(.*)$/);
      if (ordered) {
        if (!inList || listType !== "ol") {
          closeList();
          html.push("<ol>");
          inList = true;
          listType = "ol";
        }
        html.push("<li>" + renderInline(ordered[1]) + "</li>");
        continue;
      }

      const bullet = line.match(/^[-*]\s+(.*)$/);
      if (bullet) {
        if (!inList || listType !== "ul") {
          closeList();
          html.push("<ul>");
          inList = true;
          listType = "ul";
        }
        html.push("<li>" + renderInline(bullet[1]) + "</li>");
        continue;
      }

      closeList();
      html.push("<p>" + renderInline(line) + "</p>");
    }

    closeList();
    return html.join("");
  }

  async function typeAssistantMessage(container, fullText) {
    const bubble = createAssistantMessage(container);
    const parts = String(fullText || "").match(/\s+|[^\s]+/g) || [String(fullText || "")];
    let current = "";
    for (let i = 0; i < parts.length; i += 1) {
      current += parts[i];
      bubble.innerHTML = renderMarkdown(current);
      container.scrollTop = container.scrollHeight;
      await new Promise(function wait(resolve) {
        window.setTimeout(resolve, 18);
      });
    }
  }

  function init(config) {
    const apiUrl = (config && config.apiUrl) || window.location.origin;
    const botId = config && config.botId;
    const token = config && config.token;
    const title = (config && config.title) || "ChatDock";
    const greeting = (config && config.greeting) || "Hello! Ask a question about this bot.";
    const primaryColor = (config && config.primaryColor) || "#2459ea";

    if (!botId || !token) {
      throw new Error("ChatDock widget requires botId and token.");
    }

    createStyles(primaryColor);

    const launcher = document.createElement("button");
    launcher.className = "chatdock-launcher";
    launcher.innerHTML = "&#9993;";

    const panel = document.createElement("div");
    panel.className = "chatdock-panel";

    const header = document.createElement("div");
    header.className = "chatdock-header";
    header.innerHTML = `
      <div>
        <div class="chatdock-header-title">${title}</div>
        <div class="chatdock-header-subtitle">Powered by ChatDock</div>
      </div>
    `;

    const close = document.createElement("button");
    close.className = "chatdock-close";
    close.textContent = "×";
    close.onclick = function closePanel() {
      panel.classList.remove("is-open");
    };
    header.appendChild(close);

    const messages = document.createElement("div");
    messages.className = "chatdock-messages";
    appendMessage(messages, "assistant", greeting);

    const footer = document.createElement("div");
    footer.className = "chatdock-footer";
    footer.innerHTML = `
      <form class="chatdock-form">
        <input class="chatdock-input" type="text" placeholder="Ask your question..." />
        <button class="chatdock-send" type="submit">Send</button>
      </form>
      <div class="chatdock-note">This widget uses your configured ChatDock backend.</div>
    `;

    const form = footer.querySelector(".chatdock-form");
    const input = footer.querySelector(".chatdock-input");
    let conversationId = null;

    form.addEventListener("submit", async function submitQuestion(event) {
      event.preventDefault();
      const question = input.value.trim();
      if (!question) {
        return;
      }
      appendMessage(messages, "user", question);
      input.value = "";

      try {
        const response = await fetch(apiUrl.replace(/\/$/, "") + "/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
          },
          body: JSON.stringify({
            bot_id: botId,
            message: question,
            conversation_id: conversationId || undefined,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error((payload && payload.detail) || "Widget request failed");
        }
        conversationId = payload.conversation_id || conversationId;
        await typeAssistantMessage(messages, payload.answer || "No response received.");
      } catch (error) {
        await typeAssistantMessage(messages, error instanceof Error ? error.message : "Request failed.");
      }
    });

    launcher.onclick = function openPanel() {
      panel.classList.add("is-open");
    };

    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(footer);

    document.body.appendChild(launcher);
    document.body.appendChild(panel);
  }

  return { init: init };
})();
