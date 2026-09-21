"""
jog/dashboard.py
================
Máy chủ Web Dashboard Realtime nhúng (Embedded Web Monitor).
Cung cấp giao diện đồ họa trực quan (Web UI) hiển thị radar bảo vệ,
luồng sự kiện kiểm toán thời gian thực (SSE) và bảng thử nghiệm prompt tương tác.
"""

import os
import sys
import json
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JevGuarAgent - Realtime Defense Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0a0d14;
            --bg-card: rgba(18, 24, 38, 0.75);
            --bg-card-hover: rgba(26, 35, 56, 0.85);
            --border-glow: rgba(0, 242, 254, 0.25);
            --border-line: rgba(255, 255, 255, 0.08);
            --cyan-neon: #00f2fe;
            --blue-neon: #4facfe;
            --green-neon: #00f5a0;
            --red-neon: #ff0055;
            --yellow-neon: #ffd200;
            --text-main: #f0f4f8;
            --text-muted: #8a99ad;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
        }

        body {
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(0, 242, 254, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(255, 0, 85, 0.06) 0%, transparent 40%),
                linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px;
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
            overflow-x: hidden;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* HEADER */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-line);
            margin-bottom: 28px;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .shield-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--cyan-neon), var(--blue-neon));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.4);
            animation: pulse-glow 3s infinite alternate;
        }

        @keyframes pulse-glow {
            0% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 242, 254, 0.3); }
            100% { transform: scale(1.04); box-shadow: 0 0 35px rgba(0, 242, 254, 0.6); }
        }

        .title-group h1 {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #ffffff, var(--cyan-neon));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .title-group p {
            font-size: 13px;
            color: var(--text-muted);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 245, 160, 0.1);
            border: 1px solid rgba(0, 245, 160, 0.3);
            padding: 8px 16px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
            color: var(--green-neon);
        }

        .radar-dot {
            width: 10px;
            height: 10px;
            background-color: var(--green-neon);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--green-neon);
            animation: blink 1.2s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* METRICS ROW */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 28px;
        }

        .metric-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-line);
            border-radius: 16px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s, border-color 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-glow);
        }

        .metric-label {
            font-size: 13px;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-val {
            font-size: 32px;
            font-weight: 900;
            margin-top: 8px;
        }

        .metric-val.cyan { color: var(--cyan-neon); }
        .metric-val.green { color: var(--green-neon); }
        .metric-val.red { color: var(--red-neon); }
        .metric-val.yellow { color: var(--yellow-neon); }

        /* MAIN CONTENT GRID */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 24px;
        }

        /* LIVE FEED */
        .feed-section {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-line);
            border-radius: 20px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            min-height: 540px;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .feed-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
            max-height: 600px;
            padding-right: 6px;
        }

        .feed-list::-webkit-scrollbar {
            width: 6px;
        }

        .feed-list::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }

        .event-card {
            background: rgba(10, 14, 22, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-left: 4px solid var(--cyan-neon);
            border-radius: 12px;
            padding: 16px;
            animation: slide-in 0.3s ease-out;
            transition: border-color 0.2s;
        }

        @keyframes slide-in {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .event-card.block { border-left-color: var(--red-neon); }
        .event-card.warn { border-left-color: var(--yellow-neon); }
        .event-card.allow { border-left-color: var(--green-neon); }

        .event-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .event-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--text-muted);
        }

        .channel-tag {
            background: rgba(0, 242, 254, 0.12);
            color: var(--cyan-neon);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .verdict-tag {
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 8px;
        }

        .verdict-tag.allow { background: rgba(0, 245, 160, 0.15); color: var(--green-neon); }
        .verdict-tag.block { background: rgba(255, 0, 85, 0.2); color: var(--red-neon); }
        .verdict-tag.warn { background: rgba(255, 210, 0, 0.18); color: var(--yellow-neon); }

        .prompt-preview {
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            background: rgba(0, 0, 0, 0.35);
            padding: 10px 14px;
            border-radius: 8px;
            color: #d1d9e6;
            margin-bottom: 12px;
            word-break: break-all;
            border: 1px solid rgba(255,255,255,0.03);
        }

        .advisory-box {
            background: rgba(79, 172, 254, 0.08);
            border: 1px solid rgba(79, 172, 254, 0.2);
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
        }

        .advisory-title {
            font-size: 12px;
            font-weight: 700;
            color: var(--cyan-neon);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .edge-case-list {
            list-style: none;
            padding-left: 0;
            font-size: 12px;
            color: #b5c4d6;
        }

        .edge-case-list li {
            margin-bottom: 4px;
            position: relative;
            padding-left: 14px;
        }

        .edge-case-list li::before {
            content: "•";
            color: var(--yellow-neon);
            position: absolute;
            left: 0;
            font-weight: bold;
        }

        .issue-box {
            background: rgba(255, 0, 85, 0.1);
            border: 1px solid rgba(255, 0, 85, 0.25);
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 12px;
            color: #ff8099;
            margin-top: 8px;
        }

        /* RIGHT PANEL: INTERACTIVE TESTER */
        .tester-section {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .interactive-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-line);
            border-radius: 20px;
            padding: 24px;
        }

        .tester-input {
            width: 100%;
            height: 120px;
            background: rgba(10, 14, 22, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 12px;
            color: #ffffff;
            font-size: 13px;
            font-family: 'JetBrains Mono', monospace;
            resize: none;
            margin: 12px 0;
            outline: none;
            transition: border-color 0.2s;
        }

        .tester-input:focus {
            border-color: var(--cyan-neon);
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
        }

        .btn-test {
            width: 100%;
            background: linear-gradient(135deg, var(--cyan-neon), var(--blue-neon));
            border: none;
            border-radius: 12px;
            padding: 12px;
            font-weight: 700;
            font-size: 14px;
            color: #050b14;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }

        .btn-test:hover {
            opacity: 0.92;
            transform: scale(0.99);
        }

        .btn-test:active {
            transform: scale(0.97);
        }

        .quick-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }

        .chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 5px 12px;
            font-size: 11px;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }

        .chip:hover {
            background: rgba(0, 242, 254, 0.12);
            color: var(--cyan-neon);
            border-color: rgba(0, 242, 254, 0.3);
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <header>
            <div class="logo-area">
                <div class="shield-icon">🛡️</div>
                <div class="title-group">
                    <h1>JevGuarAgent Monitor</h1>
                    <p>Realtime SecOps Radar & AI Coding Architecture Advisor</p>
                </div>
            </div>
            <div class="status-badge">
                <div class="radar-dot"></div>
                <span>RADAR ĐANG LẮNG NGHE REALTIME</span>
            </div>
        </header>

        <!-- METRICS ROW -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Tổng Sự Kiện Đã Quét</div>
                <div class="metric-val cyan" id="stat-total">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Lệnh An Toàn Cho Phép</div>
                <div class="metric-val green" id="stat-safe">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Mối Đe Dọa Bị Chặn Đứng</div>
                <div class="metric-val red" id="stat-blocked">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Edge Cases Đã Tiên Lượng</div>
                <div class="metric-val yellow" id="stat-advisories">0</div>
            </div>
        </div>

        <!-- MAIN GRID -->
        <div class="main-grid">
            <!-- LIVE FEED -->
            <div class="feed-section">
                <div class="section-header">
                    <div class="section-title">
                        <span>📡</span> Luồng Sự Kiện Trực Tiếp (Live Stream)
                    </div>
                    <span style="font-size: 12px; color: var(--text-muted);" id="feed-count">0 sự kiện</span>
                </div>
                <div class="feed-list" id="feed-container">
                    <div class="empty-state">
                        <p>Đang chờ sự kiện đầu tiên... Hãy chat với Agent hoặc nhập prompt bên phải để thử nghiệm!</p>
                    </div>
                </div>
            </div>

            <!-- INTERACTIVE TESTER -->
            <div class="tester-section">
                <div class="interactive-card">
                    <div class="section-title" style="font-size: 16px; margin-bottom: 8px;">
                        <span>⚡</span> Thử Nghiệm Prompt Tức Thì
                    </div>
                    <p style="font-size: 12px; color: var(--text-muted);">
                        Nhập prompt hoặc câu lệnh để Guardrail đánh giá an toàn & phỏng đoán kiến trúc ngay trên màn hình:
                    </p>
                    <textarea class="tester-input" id="prompt-input" placeholder="VD: tôi muốn làm tính năng thanh toán thẻ tín dụng qua Stripe..."></textarea>
                    <button class="btn-test" id="btn-submit" onclick="submitPrompt()">QUÉT REALTIME NGAY 🚀</button>
                    
                    <div class="quick-chips">
                        <div class="chip" onclick="fillPrompt('tôi muốn tích hợp thanh toán stripe và momo')">💳 Thanh toán</div>
                        <div class="chip" onclick="fillPrompt('viết api upload ảnh đại diện và resume pdf')">📁 Upload File</div>
                        <div class="chip" onclick="fillPrompt('thêm websocket realtime chat cho phòng cưới')">⚡ Realtime</div>
                        <div class="chip" onclick="fillPrompt('xoa file tam va thu muc tmp')">🚨 Lệnh Xóa</div>
                        <div class="chip" onclick="fillPrompt('deploy voi access key bí mật')">🔑 Kiểm tra Secret</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let totalCount = 0;
        let safeCount = 0;
        let blockedCount = 0;
        let advisoryCount = 0;
        let seenTimestamps = new Set();

        function fillPrompt(text) {
            document.getElementById('prompt-input').value = text;
        }

        async function submitPrompt() {
            const input = document.getElementById('prompt-input');
            const text = input.value.trim();
            if (!text) return;

            const btn = document.getElementById('btn-submit');
            btn.innerText = "ĐANG PHÂN TÍCH...";
            btn.disabled = true;

            try {
                const res = await fetch('/api/check', { signal: AbortSignal.timeout(5000),
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text })
                });
                const data = await res.json();
                input.value = "";
                // Render ngay
                appendEvent(data);
            } catch (err) {
                console.error("Lỗi gửi prompt:", err);
            } finally {
                btn.innerText = "QUÉT REALTIME NGAY 🚀";
                btn.disabled = false;
            }
        }

        function appendEvent(entry) {
            const container = document.getElementById('feed-container');
            const emptyState = container.querySelector('.empty-state');
            if (emptyState) emptyState.remove();

            const key = entry.timestamp + (entry.snippet_preview || '');
            if (seenTimestamps.has(key)) return;
            seenTimestamps.add(key);

            totalCount++;
            const verdict = entry.verdict || 'allow';
            const risk = entry.risk_score || 0;
            const details = entry.details || {};
            const snippet = entry.snippet_preview || entry.raw_snippet || '';
            const advisory = details.predicted_edge_cases;

            let verdictClass = 'allow';
            let verdictBadge = '✓ AN TOÀN';
            if (verdict === 'block_immediately' || verdict === 'reject_force_agent_rewrite' || risk >= 7.5) {
                verdictClass = 'block';
                verdictBadge = '🚨 CHẶN TỨC THỜI';
                blockedCount++;
            } else if (verdict === 'warn_user' || verdict === 'warn_dev_needs_refactor') {
                verdictClass = 'warn';
                verdictBadge = '⚠️ CẢNH BÁO';
                safeCount++;
            } else {
                safeCount++;
            }

            if (advisory) advisoryCount++;

            // Update stats
            document.getElementById('stat-total').innerText = totalCount;
            document.getElementById('stat-safe').innerText = safeCount;
            document.getElementById('stat-blocked').innerText = blockedCount;
            document.getElementById('stat-advisories').innerText = advisoryCount;
            document.getElementById('feed-count').innerText = totalCount + " sự kiện";

            // Format time
            const timeStr = entry.timestamp ? entry.timestamp.split('T')[1].substring(0, 8) : new Date().toLocaleTimeString();

            let advisoryHtml = '';
            if (advisory) {
                const intent = advisory.intent_description || '';
                const risks = advisory.risk_factors || [];
                const recs = advisory.recommended_patterns || [];
                advisoryHtml = `
                    <div class="advisory-box">
                        <div class="advisory-title">🧠 Phỏng Đoán Kiến Trúc & Edge Cases: <span>${intent}</span></div>
                        <ul class="edge-case-list">
                            ${risks.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                        ${recs.length > 0 ? `<div style="font-size: 11px; color: var(--green-neon); margin-top: 6px;"><strong>💡 Đề xuất:</strong> ${recs[0]}</div>` : ''}
                    </div>
                `;
            }

            let issuesHtml = '';
            const issues = details.issues || details.detected_flaws || [];
            const filteredIssues = issues.filter(i => i !== "Câu lệnh an toàn.");
            if (filteredIssues.length > 0) {
                issuesHtml = `
                    <div class="issue-box">
                        <strong>Lỗi phát hiện:</strong><br>
                        ${filteredIssues.map(i => `• ${i}`).join('<br>')}
                    </div>
                `;
            }

            const card = document.createElement('div');
            card.className = `event-card ${verdictClass}`;
            card.innerHTML = `
                <div class="event-top">
                    <div class="event-meta">
                        <span class="channel-tag">${entry.channel || 'CLI'}</span>
                        <span>${timeStr}</span>
                        <span>• Điểm rủi ro: ${risk}/10</span>
                    </div>
                    <span class="verdict-tag ${verdictClass}">${verdictBadge}</span>
                </div>
                ${snippet ? `<div class="prompt-preview">${escapeHtml(snippet)}</div>` : ''}
                ${issuesHtml}
                ${advisoryHtml}
            `;

            container.insertBefore(card, container.firstChild);
        }

        function escapeHtml(str) {
            return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

        // Long-poll / polling for real-time log stream
        let lastTimestamp = null;
        async function fetchLiveUpdates() {
            try {
                const res = await fetch('/api/events', { signal: AbortSignal.timeout(5000) });
                if (res.ok) {
                    const data = await res.json();
                    if (Array.isArray(data)) {
                        data.forEach(entry => appendEvent(entry));
                    }
                }
            } catch (e) {
                console.error("Fetch poll error", e);
            }
            setTimeout(fetchLiveUpdates, 800);
        }

        // Start listening
        fetchLiveUpdates();
    </script>
</body>
</html>
"""


class JogDashboardHandler(BaseHTTPRequestHandler):
    """Xử lý HTTP requests phục vụ Web Dashboard."""

    def log_message(self, format, *args):
        # Ẩn access logs mặc định để không làm bẩn màn hình terminal
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))

        elif self.path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            events = self._read_recent_events()
            self.wfile.write(json.dumps(events, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/check":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
                prompt = data.get("prompt", "")
            except Exception:
                prompt = ""

            from jog.config import load_config
            from jog.jev_engine import JevEngine
            from dataclasses import asdict

            config = load_config()
            engine = JevEngine(config)
            res = engine.check_prompt_and_action(prompt, channel="web_dashboard")
            advisory = getattr(res, "predicted_edge_cases", None) or engine.predict_architecture_advisory(prompt)
            advisory_dict = asdict(advisory) if (advisory and hasattr(advisory, "intent_description")) else advisory

            event = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "event_type": "prompt_and_action_check",
                "channel": "web_dashboard",
                "verdict": res.action_verdict,
                "risk_score": res.destructive_intent_score,
                "snippet_preview": prompt,
                "details": {
                    "has_credential_leak": res.has_credential_leak,
                    "engine_source": res.engine_source,
                    "issues": res.details,
                    "remediation": res.remediation,
                    "predicted_edge_cases": advisory_dict
                }
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(event, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def _read_recent_events(self) -> List[Dict[str, Any]]:
        """Đọc danh sách sự kiện từ các file log gần nhất."""
        events = []
        candidate_logs = [
            Path.cwd() / ".jog" / "logs" / "audit.log",
            Path("/run/media/thietnv/Data/Demo/wedding-manager/.jog/logs/audit.log"),
            Path("/run/media/thietnv/Data/JevGuarAgent/.jog/logs/audit.log")
        ]
        for cl in candidate_logs:
            if cl.exists():
                try:
                    with open(cl, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        for l in lines[-25:]:
                            if l.strip():
                                try:
                                    events.append(json.loads(l.strip()))
                                except Exception:
                                    pass
                except Exception:
                    pass
        # Sắp xếp theo timestamp
        events.sort(key=lambda e: e.get("timestamp", ""))
        return events[-30:]


def start_dashboard_server(port: int = 8888, auto_open: bool = True) -> HTTPServer:
    """Khởi động máy chủ Web Dashboard dưới một luồng nền."""
    server = HTTPServer(("127.0.0.1", port), JogDashboardHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{port}"
    if auto_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    return server
