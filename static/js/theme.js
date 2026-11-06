/**
 * Lahore City Hub (LCH) - Interactive Client Scripts
 * Pure Vanilla JavaScript (Zero bloated frameworks)
 */

document.addEventListener('DOMContentLoaded', function () {
  // Initialize Toast Notifications
  const toastContainer = document.getElementById('lch-toast-container') || createToastContainer();

  // 1. Interactive Bookmark Toggle
  document.querySelectorAll('.btn-bookmark-toggle').forEach(function (button) {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      const icon = button.querySelector('i');
      const isSaved = icon.classList.contains('bi-bookmark-fill');

      if (isSaved) {
        icon.classList.remove('bi-bookmark-fill', 'text-danger');
        icon.classList.add('bi-bookmark');
        showToast('Removed from your saved bookmarks.', 'info');
      } else {
        icon.classList.remove('bi-bookmark');
        icon.classList.add('bi-bookmark-fill', 'text-danger');
        showToast('Saved to your Lahore City Hub bookmarks!', 'success');
      }
    });
  });

  // 2. Share Listing Trigger (Native Web Share API fallback to clipboard)
  document.querySelectorAll('.btn-share-trigger').forEach(function (button) {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      const title = document.title;
      const url = window.location.href;

      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () {});
      } else {
        navigator.clipboard.writeText(url).then(function () {
          showToast('Listing URL copied to clipboard!', 'success');
        });
      }
    });
  });

  // 3. Grid vs List View Toggle in Category Page
  const viewGridBtn = document.getElementById('view-grid-btn');
  const viewListBtn = document.getElementById('view-list-btn');
  const itemsContainer = document.getElementById('directory-items-container');

  if (viewGridBtn && viewListBtn && itemsContainer) {
    viewGridBtn.addEventListener('click', function () {
      viewGridBtn.classList.add('active');
      viewListBtn.classList.remove('active');
      itemsContainer.classList.remove('directory-list-mode');
      itemsContainer.classList.add('row', 'g-4');
    });

    viewListBtn.addEventListener('click', function () {
      viewListBtn.classList.add('active');
      viewGridBtn.classList.remove('active');
      itemsContainer.classList.add('directory-list-mode');
    });
  }

  // 4. Keyboard Shortcut: Press '/' to focus search input
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      const heroSearch = document.getElementById('hero-search-input');
      if (heroSearch) {
        heroSearch.focus();
        heroSearch.select();
      }
    }
  });

  // 5. Toast Notification Helper
  function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'lch-toast-container';
    container.style.position = 'fixed';
    container.style.bottom = '20px';
    container.style.right = '20px';
    container.style.zIndex = '1090';
    document.body.appendChild(container);
    return container;
  }

  function showToast(message, type) {
    const toast = document.createElement('div');
    const bgClass = type === 'success' ? 'bg-success text-white' : 'bg-dark text-white';
    toast.className = `toast align-items-center ${bgClass} border-0 show mb-2 shadow`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.borderRadius = '10px';

    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body py-2 px-3 fw-medium">
          <i class="bi ${type === 'success' ? 'bi-check-circle-fill' : 'bi-info-circle-fill'} me-2"></i>
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    toastContainer.appendChild(toast);
    setTimeout(function () {
      toast.classList.remove('show');
      setTimeout(function () { toast.remove(); }, 300);
    }, 3200);

    const closeBtn = toast.querySelector('.btn-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () { toast.remove(); });
    }
  }
});
