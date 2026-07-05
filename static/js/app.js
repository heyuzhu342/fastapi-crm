/**
 * FastAPI CRM — 全局前端脚本
 */

// ── 认证拦截 ────────────────────────────────────
(function() {
    'use strict';

    // 非登录页需要 token
    const publicPaths = ['/login', '/register', '/docs', '/redoc', '/api/', '/health'];
    const currentPath = window.location.pathname;

    const isPublic = publicPaths.some(p => currentPath.startsWith(p));
    if (!isPublic) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
    }

    // 全局 fetch 拦截 — 自动附带 Authorization header
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        const token = localStorage.getItem('access_token');
        if (token) {
            options.headers = options.headers || {};
            // 只在调用自家 API 时附加 token
            if (typeof url === 'string' && (url.startsWith('/api/') || url.startsWith(window.location.origin + '/api/'))) {
                if (options.headers instanceof Headers) {
                    options.headers.set('Authorization', 'Bearer ' + token);
                } else {
                    options.headers['Authorization'] = 'Bearer ' + token;
                }
            }
        }
        return originalFetch.call(this, url, options)
            .then(response => {
                // 401 自动跳转登录页
                if (response.status === 401 && !currentPath.startsWith('/login')) {
                    localStorage.clear();
                    window.location.href = '/login?expired=1';
                }
                return response;
            });
    };
})();

// ── 退出登录 ────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.clear();
            window.location.href = '/login';
        });
    }
});

// ── Alert 自动消失 ───────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() { alert.remove(); }, 500);
        });
    }, 5000);
});

// ── XSS 防护 ────────────────────────────────────
window.escapeHtml = function(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
};

// ── 格式化工具 ──────────────────────────────────
window.formatCurrency = function(amount) {
    if (amount === null || amount === undefined) return '—';
    return '¥ ' + Number(amount).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

window.formatDate = function(dateStr) {
    if (!dateStr) return '—';
    var d = new Date(dateStr);
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0') + ' ' +
        String(d.getHours()).padStart(2, '0') + ':' +
        String(d.getMinutes()).padStart(2, '0');
};

// ── 通知轮询 ────────────────────────────────────
setInterval(async function() {
    if (currentPath.startsWith('/login') || currentPath.startsWith('/register')) return;
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
        const res = await fetch('/api/v1/notifications/unread-count', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            const data = await res.json();
            const badge = document.getElementById('notification-badge');
            if (badge && data.data && data.data.count > 0) {
                badge.textContent = data.data.count;
                badge.style.display = 'inline-block';
            }
        }
    } catch (e) {
        // 静默处理
    }
}, 60000); // 每分钟轮询一次
