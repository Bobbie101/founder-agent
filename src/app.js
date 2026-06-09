// ── State ──
let isWaiting = false;
let pendingLookupName = null;

// ── DOM refs ──
const messagesEl   = document.getElementById('messages');
const inputEl      = document.getElementById('userInput');
const sendBtn      = document.getElementById('sendBtn');
const typingEl     = document.getElementById('typingIndicator');
const scoreNumEl   = document.getElementById('scoreNumber');
const ringFillEl   = document.getElementById('ringFill');
const sessionBadge = document.getElementById('sessionBadge');

// ── Inject SVG gradient ──
const svgNS = 'http://www.w3.org/2000/svg';
const defs = document.createElementNS(svgNS, 'defs');
const grad = document.createElementNS(svgNS, 'linearGradient');
grad.setAttribute('id', 'ringGrad');
grad.setAttribute('x1', '0%'); grad.setAttribute('y1', '0%');
grad.setAttribute('x2', '100%'); grad.setAttribute('y2', '0%');
const s1 = document.createElementNS(svgNS, 'stop');
s1.setAttribute('offset', '0%'); s1.setAttribute('stop-color', '#5B4FF5');
const s2 = document.createElementNS(svgNS, 'stop');
s2.setAttribute('offset', '100%'); s2.setAttribute('stop-color', '#00A88E');
grad.appendChild(s1); grad.appendChild(s2);
defs.appendChild(grad);
document.querySelector('.score-ring').prepend(defs);

// ── Auto-resize textarea ──
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
});

// ── Enter to send ──
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ── Send message ──
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || isWaiting) return;

  addMessage(text, 'user');
  inputEl.value = '';
  inputEl.style.height = 'auto';
  setWaiting(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();

    if (data.error) {
      addMessage('Something went wrong: ' + data.error, 'agent');
    } else {
      addMessage(data.response, 'agent');
      if (data.session_id) {
        sessionBadge.textContent = 'Session: ' + data.session_id;
      }
      detectScoreInResponse(data.response);
    }
  } catch (err) {
    addMessage('Connection error. Please try again.', 'agent');
  }

  setWaiting(false);
}

// ── Add message to UI ──
function addMessage(text, role) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role === 'user' ? 'user-message' : 'agent-message'}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'user' ? 'You' : 'FA';

  const body = document.createElement('div');
  body.className = 'message-body';
  body.innerHTML = formatMessage(text);

  wrap.appendChild(avatar);
  wrap.appendChild(body);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ── Format agent markdown-ish text ──
function formatMessage(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hul])(.+)$/gm, (m) => m.startsWith('<') ? m : `<p>${m}</p>`)
    .replace(/<p><\/p>/g, '');
}

// ── Typing indicator ──
function setWaiting(state) {
  isWaiting = state;
  sendBtn.disabled = state;
  typingEl.classList.toggle('visible', state);
  if (state) messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ── Update score ring ──
function updateScore(score) {
  const circumference = 314.16;
  const offset = circumference - (score / 100) * circumference;
  ringFillEl.style.strokeDashoffset = offset;
  const current = parseInt(scoreNumEl.textContent);
  const step = score > current ? 1 : -1;
  let val = current;
  const timer = setInterval(() => {
    val += step;
    scoreNumEl.textContent = val;
    if (val === score) clearInterval(timer);
  }, 20);
}

// ── Update milestones ──
function updateMilestones(milestones) {
  Object.entries(milestones).forEach(([key, val]) => {
    const el = document.querySelector(`.milestone[data-key="${key}"]`);
    if (el) {
      el.classList.toggle('complete', val.completed);
    }
  });
}

// ── Detect score in agent response ──
function detectScoreInResponse(text) {
  const match = text.match(/(\d+)\s*\/\s*100/);
  if (match) {
    const score = parseInt(match[1]);
    if (score >= 0 && score <= 100) updateScore(score);
  }
}

// ── Lookup returning founder ──
async function lookupFounder() {
  const name = document.getElementById('founderLookup').value.trim();
  if (!name) return;

  try {
    const res = await fetch(`/api/check/${encodeURIComponent(name)}`);
    const data = await res.json();

    if (data.exists) {
      // Show PIN keypad
      pendingLookupName = name;
      showPinModal(name);
    } else {
      addMessage(`No profile found for "${name}". Start a new session to create one.`, 'agent');
    }
  } catch (err) {
    addMessage('Could not check profile. Try again.', 'agent');
  }
}

// ── PIN Modal ──
function showPinModal(name) {
  // Remove existing modal if any
  const existing = document.getElementById('pinModal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'pinModal';
  modal.className = 'pin-modal-overlay';
  modal.innerHTML = `
    <div class="pin-modal">
      <p class="pin-greeting">Welcome back, <strong>${name}</strong></p>
      <p class="pin-subtitle">Enter your PIN to resume</p>
      <div class="pin-dots" id="pinDots">
        <span></span><span></span><span></span><span></span>
      </div>
      <div class="pin-error" id="pinError"></div>
      <div class="pin-keypad">
        ${[1,2,3,4,5,6,7,8,9,'',0,'⌫'].map(k => `
          <button class="pin-key ${k === '' ? 'pin-key-empty' : ''}" 
            onclick="pinPress('${k}')"
            ${k === '' ? 'disabled' : ''}>
            ${k}
          </button>
        `).join('')}
      </div>
      <button class="pin-cancel" onclick="closePinModal()">Cancel</button>
    </div>
  `;

  document.body.appendChild(modal);
  setTimeout(() => modal.classList.add('visible'), 10);
}

let pinBuffer = '';

function pinPress(key) {
  if (key === '⌫') {
    pinBuffer = pinBuffer.slice(0, -1);
  } else if (pinBuffer.length < 4 && key !== '') {
    pinBuffer += key;
  }

  // Update dots
  const dots = document.querySelectorAll('#pinDots span');
  dots.forEach((dot, i) => {
    dot.classList.toggle('filled', i < pinBuffer.length);
  });

  // Auto-submit when 4 digits entered
  if (pinBuffer.length === 4) {
    setTimeout(() => submitPin(), 200);
  }
}

async function submitPin() {
  const name = pendingLookupName;
  const pin = pinBuffer;
  pinBuffer = '';

  try {
    const res = await fetch('/api/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, pin })
    });

    const data = await res.json();

    if (data.success) {
      closePinModal();
      updateMilestones(data.milestones || {});
      if (data.investor_score !== undefined) updateScore(data.investor_score);
      sessionBadge.textContent = 'Resumed: ' + name;
      addMessage(data.message, 'agent');
    } else {
      // Wrong PIN — shake and reset dots
      const dots = document.getElementById('pinDots');
      dots.classList.add('shake');
      document.getElementById('pinError').textContent = 'Incorrect PIN. Try again.';
      setTimeout(() => {
        dots.classList.remove('shake');
        document.querySelectorAll('#pinDots span').forEach(d => d.classList.remove('filled'));
        document.getElementById('pinError').textContent = '';
      }, 600);
    }
  } catch (err) {
    document.getElementById('pinError').textContent = 'Connection error. Try again.';
  }
}

function closePinModal() {
  const modal = document.getElementById('pinModal');
  if (modal) {
    modal.classList.remove('visible');
    setTimeout(() => modal.remove(), 300);
  }
  pinBuffer = '';
  pendingLookupName = null;
}

// Close on overlay click
document.addEventListener('click', (e) => {
  if (e.target.id === 'pinModal') closePinModal();
});