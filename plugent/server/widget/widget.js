/**
 * Plugent Chat Widget - Vanilla JavaScript
 * No dependencies, no frameworks
 */
(function() {
  'use strict';

  // Configuration from data attributes
  const config = {
    position: document.currentScript?.dataset.position || 'bottom-right',
    theme: document.currentScript?.dataset.theme || 'light',
    primaryColor: document.currentScript?.dataset.primaryColor || '#4F46E5',
    title: document.currentScript?.dataset.title || 'Chat',
    greeting: document.currentScript?.dataset.greeting || 'Hello! How can I help you?',
    agentAvatar: document.currentScript?.dataset.agentAvatar || null,
    apiUrl: document.currentScript?.dataset.apiUrl || '/chat',
  };

  // State
  let isOpen = false;
  let sessionId = 'widget_' + Math.random().toString(36).substr(2, 9);

  // Create widget DOM
  function createWidget() {
    // Container
    const container = document.createElement('div');
    container.id = 'plugent-widget-container';
    container.style.cssText = `
      position: fixed;
      ${config.position}: 20px;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
    `;

    // Chat panel
    const panel = document.createElement('div');
    panel.id = 'plugent-chat-panel';
    panel.style.cssText = `
      display: none;
      position: absolute;
      ${config.position.includes('bottom') ? 'bottom: 70px' : 'top: 70px'};
      ${config.position.includes('right') ? 'right: 0' : 'left: 0'};
      width: 350px;
      height: 450px;
      background: ${config.theme === 'dark' ? '#1f2937' : '#ffffff'};
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.15);
      flex-direction: column;
      overflow: hidden;
    `;
    panel.className = 'plugent-panel';

    // Header
    const header = document.createElement('div');
    header.style.cssText = `
      padding: 16px;
      background: ${config.primaryColor};
      color: white;
      display: flex;
      align-items: center;
      gap: 12px;
    `;

    if (config.agentAvatar) {
      const avatar = document.createElement('img');
      avatar.src = config.agentAvatar;
      avatar.style.cssText = 'width: 32px; height: 32px; border-radius: 50%;';
      header.appendChild(avatar);
    } else {
      const avatarPlaceholder = document.createElement('div');
      avatarPlaceholder.style.cssText = `
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
      `;
      avatarPlaceholder.textContent = '🤖';
      header.appendChild(avatarPlaceholder);
    }

    const title = document.createElement('div');
    title.style.cssText = 'font-weight: 600; flex: 1;';
    title.textContent = config.title;
    header.appendChild(title);

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = `
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 18px;
      padding: 4px;
    `;
    closeBtn.onclick = toggleChat;
    header.appendChild(closeBtn);

    panel.appendChild(header);

    // Messages area
    const messages = document.createElement('div');
    messages.id = 'plugent-messages';
    messages.style.cssText = `
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: ${config.theme === 'dark' ? '#111827' : '#f9fafb'};
    `;
    panel.appendChild(messages);

    // Typing indicator (hidden by default)
    const typing = document.createElement('div');
    typing.id = 'plugent-typing';
    typing.style.cssText = `
      display: none;
      padding: 8px 12px;
      background: ${config.theme === 'dark' ? '#374151' : '#e5e7eb'};
      border-radius: 12px;
      border-bottom-left-radius: 4px;
      color: ${config.theme === 'dark' ? '#d1d5db' : '#6b7280'};
      font-size: 13px;
    `;
    typing.textContent = 'Thinking...';
    messages.appendChild(typing);

    // Input area
    const inputArea = document.createElement('div');
    inputArea.style.cssText = `
      padding: 12px;
      border-top: 1px solid ${config.theme === 'dark' ? '#374151' : '#e5e7eb'};
      display: flex;
      gap: 8px;
      background: ${config.theme === 'dark' ? '#1f2937' : '#ffffff'};
    `;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Type a message...';
    input.id = 'plugent-input';
    input.style.cssText = `
      flex: 1;
      padding: 10px 14px;
      border: 1px solid ${config.theme === 'dark' ? '#374151' : '#d1d5db'};
      border-radius: 20px;
      outline: none;
      font-size: 14px;
      background: ${config.theme === 'dark' ? '#111827' : '#ffffff'};
      color: ${config.theme === 'dark' ? '#d1d5db' : '#1f2937'};
    `;
    input.onkeypress = function(e) {
      if (e.key === 'Enter') sendMessage();
    };
    inputArea.appendChild(input);

    const sendBtn = document.createElement('button');
    sendBtn.innerHTML = '➤';
    sendBtn.style.cssText = `
      background: ${config.primaryColor};
      border: none;
      color: white;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 16px;
    `;
    sendBtn.onclick = sendMessage;
    inputArea.appendChild(sendBtn);

    panel.appendChild(inputArea);

    container.appendChild(panel);

    // Toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'plugent-toggle';
    toggleBtn.innerHTML = '💬';
    toggleBtn.style.cssText = `
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: ${config.primaryColor};
      border: none;
      color: white;
      font-size: 24px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
      transition: transform 0.2s;
    `;
    toggleBtn.onclick = toggleChat;
    container.appendChild(toggleBtn);

    document.body.appendChild(container);

    // Show greeting
    setTimeout(() => {
      addMessage(config.greeting, 'agent');
    }, 500);
  }

  function toggleChat() {
    isOpen = !isOpen;
    const panel = document.querySelector('.plugent-panel');
    const btn = document.getElementById('plugent-toggle');

    if (isOpen) {
      panel.style.display = 'flex';
      btn.style.transform = 'rotate(90deg)';
      document.getElementById('plugent-input').focus();
    } else {
      panel.style.display = 'none';
      btn.style.transform = 'rotate(0deg)';
    }
  }

  function addMessage(text, role) {
    const messages = document.getElementById('plugent-messages');
    const msg = document.createElement('div');
    msg.style.cssText = `
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 12px;
      line-height: 1.5;
      word-wrap: break-word;
    `;

    if (role === 'user') {
      msg.style.cssText += `
        align-self: flex-end;
        background: ${config.primaryColor};
        color: white;
        border-bottom-right-radius: 4px;
      `;
    } else {
      msg.style.cssText += `
        align-self: flex-start;
        background: ${config.theme === 'dark' ? '#374151' : '#e5e7eb'};
        color: ${config.theme === 'dark' ? '#d1d5db' : '#1f2937'};
        border-bottom-left-radius: 4px;
      `;
    }

    msg.innerHTML = parseMarkdown(text);
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  function parseMarkdown(text) {
    if (!text) return '';
    // Escape HTML
    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // Bold: **text** or *text*
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<strong>$1</strong>');
    // Line breaks
    text = text.replace(/\n/g, '<br>');
    return text;
  }

  function showTyping(show) {
    const typing = document.getElementById('plugent-typing');
    typing.style.display = show ? 'block' : 'none';
    if (show) {
      const messages = document.getElementById('plugent-messages');
      messages.scrollTop = messages.scrollHeight;
    }
  }

  async function sendMessage() {
    const input = document.getElementById('plugent-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';
    showTyping(true);

    try {
      const response = await fetch(config.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId }),
      });

      if (!response.ok) throw new Error('API error');

      const data = await response.json();
      showTyping(false);
      addMessage(data.reply || 'No response', 'agent');
    } catch (err) {
      showTyping(false);
      addMessage('Error: Could not connect to server', 'agent');
    }
  }

  // Initialize when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();