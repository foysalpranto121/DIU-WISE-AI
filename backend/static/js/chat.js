document.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  const chatSend = document.getElementById('chat-send');
  const chatLog = document.getElementById('chat-log');
  const anonCheck = document.getElementById('anonymous');
  const agentBadge = document.getElementById('current-agent-badge');
  const suggestionContainer = document.getElementById('suggested-questions');
  
  let chatHistory = [];
  const chatBubble = document.getElementById('chat-bubble');
  const chatWidget = document.getElementById('chat-widget');
  const chatClose = document.getElementById('chat-close');

  // Toggle Chat
  if (chatClose) {
    chatClose.addEventListener('click', () => {
      chatWidget.classList.remove('active');
      chatWidget.classList.add('minimized');
      chatBubble.style.display = 'flex';
    });
  }

  // Draggable Bubble
  if (chatBubble) {
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;

    let dragStartX, dragStartY;
    let hasMoved = false;
    const moveThreshold = 5; // pixels

    chatBubble.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);

    function openChat() {
      chatWidget.classList.remove('minimized');
      chatWidget.classList.add('active');
      chatBubble.style.display = 'none';
    }

    function dragStart(e) {
      e.stopPropagation();
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      hasMoved = false;
      initialX = e.clientX - xOffset;
      initialY = e.clientY - yOffset;
      
      // Ensure bubble is on top during drag
      chatBubble.style.zIndex = "10000";
      
      if (e.target === chatBubble || chatBubble.contains(e.target)) {
        isDragging = true;
      }
    }

    function drag(e) {
      if (isDragging) {
        e.stopPropagation();
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        if (Math.abs(dx) > moveThreshold || Math.abs(dy) > moveThreshold) {
          hasMoved = true;
        }

        e.preventDefault();
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;
        xOffset = currentX;
        yOffset = currentY;
        setTranslate(currentX, currentY, chatBubble);
      }
    }

    function setTranslate(xPos, yPos, el) {
      el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
    }

    function dragEnd(e) {
      if (isDragging) {
        e.stopPropagation();
        if (!hasMoved) {
          openChat();
        }
      }
      
      initialX = currentX;
      initialY = currentY;
      isDragging = false;
      chatBubble.style.zIndex = "9999";
    }
  }

  // Handle Suggested Questions Clicks
  if (suggestionContainer) {
    suggestionContainer.addEventListener('click', (e) => {
      if (e.target.classList.contains('suggestion-chip')) {
        chatInput.value = e.target.innerText;
        sendMessage();
      }
    });
  }

  // Handle Follow Up Question Clicks
  chatLog.addEventListener('click', (e) => {
    if (e.target.classList.contains('follow-up-btn')) {
      chatInput.value = e.target.innerText;
      sendMessage();
    }
  });

  const sendMessage = async () => {
    const message = chatInput.value.trim();
    if (!message) return;

    appendMessage(message, 'user-message');
    chatInput.value = '';

    const loadingId = appendLoading();

    // Gather Student Context from DOM (if available)
    const contextData = {
      attendance: document.getElementById('attendance') ? document.getElementById('attendance').value : '',
      delay: document.getElementById('delay') ? document.getElementById('delay').value : '',
      grades: document.getElementById('grades') ? document.getElementById('grades').value : ''
    };

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message, 
          anonymous: anonCheck ? anonCheck.checked : true,
          history: chatHistory,
          student_context: contextData
        })
      });

      const data = await res.json();
      removeLoading(loadingId);

      if (data.error) {
        appendMessage(data.error, 'ai-message error');
      } else {
        if (data.agent_name && agentBadge) {
          agentBadge.innerText = `Agent: ${data.agent_name}`;
        }

        renderStructuredMessage(data.structured_response);

        // Crisis Safety Net: if the assistant detected high distress, gently
        // surface a calming breathing exercise + emergency helplines.
        const riskLevel = data.structured_response && data.structured_response.risk_level;
        if ((data.crisis || data.urgency === 'high' || riskLevel === 'high') &&
            window.CrisisSafetyNet) {
          window.CrisisSafetyNet.trigger();
        }

        chatHistory.push({ user: message, ai: data.structured_response.summary });
      }
    } catch (err) {
      removeLoading(loadingId);
      appendMessage('Connection error. Please try again.', 'ai-message error');
    }
  };

  if (chatSend && chatInput) {
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  }

  function appendMessage(text, className) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${className}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerText = text;
    
    msgDiv.appendChild(contentDiv);
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function renderStructuredMessage(resp) {
    if (!resp) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai-message structured-msg';
    
    let html = `<div class="message-content">`;
    
    // Risk Badge
    if (resp.risk_level) {
      let color = 'var(--success)';
      if (resp.risk_level === 'medium') color = 'var(--warning)';
      if (resp.risk_level === 'high') color = 'var(--danger)';
      html += `<span class="risk-badge" style="background-color: ${color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; float: right;">${resp.risk_level.toUpperCase()} RISK</span>`;
    }

    // Summary
    html += `<strong>${resp.summary}</strong><br><br>`;

    // Advice Bullets
    if (resp.advice && resp.advice.length > 0) {
      html += `<ul style="margin: 0; padding-left: 20px;">`;
      resp.advice.forEach(adv => {
        html += `<li>${adv}</li>`;
      });
      html += `</ul>`;
    }

    // Action Required
    if (resp.action_required) {
      html += `<div style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.05); border-left: 3px solid var(--accent-primary); border-radius: 4px;">
                 <em>Action: ${resp.action_required}</em>
               </div>`;
    }

    html += `</div>`; // end message-content
    
    // Follow up questions
    if (resp.follow_up_questions && resp.follow_up_questions.length > 0) {
      html += `<div class="follow-up-container" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">`;
      resp.follow_up_questions.forEach(q => {
        html += `<button class="suggestion-chip follow-up-btn">${q}</button>`;
      });
      html += `</div>`;
    }

    msgDiv.innerHTML = html;
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function appendLoading() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai-message loading-msg';
    msgDiv.id = id;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<span class="typing-indicator"><span>.</span><span>.</span><span>.</span></span>';
    
    msgDiv.appendChild(contentDiv);
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
    
    return id;
  }

  function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }
});
