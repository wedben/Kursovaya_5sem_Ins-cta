/**
 * Виджет уведомлений пользователя (колокольчик + список).
 * UserNotifications.init({ mount: '#notifications-mount', pollMs: 30000 })
 */
(function () {
  const TYPE_LABELS = {
    moderator_warning: 'Предупреждение',
    request_rejected: 'Запрос отклонён',
    expert_response: 'Ответ эксперта',
  };

  function formatDate(s) {
    if (!s) return '';
    try {
      return new Date(s).toLocaleString('ru-RU');
    } catch (_) {
      return s;
    }
  }

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  class UserNotificationsWidget {
    constructor(options) {
      this.mount = document.querySelector(options.mount);
      if (!this.mount) return;
      this.pollMs = options.pollMs || 30000;
      this.open = false;
      this.items = [];
      this.unread = 0;
      this.timer = null;
      this.renderShell();
      this.load();
      this.timer = setInterval(() => this.load({ silent: true }), this.pollMs);
      document.addEventListener('click', (e) => {
        if (!this.root.contains(e.target)) this.closePanel();
      });
      this.trySocket();
    }

    renderShell() {
      this.mount.innerHTML = `
        <div class="notif-widget">
          <button type="button" class="notif-bell" aria-label="Уведомления" aria-expanded="false">
            🔔
            <span class="notif-badge">0</span>
          </button>
          <div class="notif-panel" aria-hidden="true">
            <div class="notif-panel-head">
              <strong>Уведомления</strong>
              <button type="button" class="notif-read-all">Прочитать все</button>
            </div>
            <div class="notif-list"></div>
          </div>
        </div>`;
      this.root = this.mount.querySelector('.notif-widget');
      this.bell = this.root.querySelector('.notif-bell');
      this.badge = this.root.querySelector('.notif-badge');
      this.panel = this.root.querySelector('.notif-panel');
      this.list = this.root.querySelector('.notif-list');
      this.readAllBtn = this.root.querySelector('.notif-read-all');
      this.bell.addEventListener('click', (e) => {
        e.stopPropagation();
        this.togglePanel();
      });
      this.root.querySelector('.notif-read-all').addEventListener('click', (e) => {
        e.stopPropagation();
        this.readAll();
      });
    }

    setPanelOpen(open) {
      this.open = open;
      this.panel.classList.toggle('is-open', open);
      this.panel.setAttribute('aria-hidden', open ? 'false' : 'true');
      this.bell.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    async load(opts = {}) {
      try {
        const res = await fetch('/api/notifications');
        if (res.status === 401) return;
        const json = await res.json();
        if (!json.success) return;
        this.items = json.notifications || [];
        this.unread = json.unread_count || 0;
        this.updateBadge();
        this.updateReadAllButton();
        if (this.open) this.renderList();
      } catch (_) {
        if (!opts.silent) console.warn('Не удалось загрузить уведомления');
      }
    }

    updateReadAllButton() {
      if (!this.readAllBtn) return;
      const hasUnread = this.unread > 0;
      this.readAllBtn.disabled = !hasUnread;
      this.readAllBtn.textContent = hasUnread ? 'Прочитать все' : 'Все прочитаны';
      this.readAllBtn.style.opacity = hasUnread ? '1' : '0.5';
      this.readAllBtn.style.cursor = hasUnread ? 'pointer' : 'default';
    }

    updateBadge() {
      if (this.unread > 0) {
        this.badge.classList.add('is-visible');
        this.badge.textContent = this.unread > 99 ? '99+' : String(this.unread);
      } else {
        this.badge.classList.remove('is-visible');
      }
    }

    renderList() {
      if (!this.items.length) {
        this.list.innerHTML = '<div class="notif-empty">Нет уведомлений</div>';
        return;
      }
      this.list.innerHTML = this.items.map((n) => {
        const unread = !n.прочитано;
        const typeLabel = TYPE_LABELS[n.тип] || n.тип;
        return `
          <button type="button" class="notif-item ${unread ? 'unread' : ''}" data-id="${n.id_уведомления}" data-request="${n.id_запроса || ''}" data-type="${n.тип || ''}">
            <div class="notif-item-type">${escapeHtml(typeLabel)}</div>
            <div class="notif-item-title">${escapeHtml(n.заголовок)}</div>
            <div class="notif-item-text">${escapeHtml(n.текст)}</div>
            <div class="notif-item-date">${escapeHtml(formatDate(n.дата_создания))}</div>
          </button>`;
      }).join('');
      this.list.querySelectorAll('.notif-item').forEach((el) => {
        el.addEventListener('click', () => this.onItemClick(el));
      });
    }

    togglePanel() {
      this.setPanelOpen(!this.open);
      if (this.open) {
        this.load().then(() => this.renderList());
      }
    }

    closePanel() {
      this.setPanelOpen(false);
    }

    async onItemClick(el) {
      const id = el.dataset.id;
      await fetch(`/api/notifications/${id}/read`, {
        method: 'POST',
        credentials: 'same-origin',
      });
      await this.load({ silent: true });
      this.renderList();
    }

    async readAll() {
      if (this.unread <= 0) return;
      const res = await fetch('/api/notifications/read-all', {
        method: 'POST',
        credentials: 'same-origin',
      });
      const json = await res.json();
      if (!json.success) return;
      this.unread = json.unread_count || 0;
      this.updateBadge();
      this.updateReadAllButton();
      await this.load({ silent: true });
      this.renderList();
    }

    trySocket() {
      if (typeof io === 'undefined') return;
      try {
        const socket = io({ transports: ['websocket', 'polling'] });
        socket.on('new_notification', () => this.load({ silent: true }));
      } catch (_) {}
    }
  }

  window.UserNotifications = {
    init(options) {
      return new UserNotificationsWidget(options || {});
    },
  };
})();
