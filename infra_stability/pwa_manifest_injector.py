"""
PWA Manifest & Service Worker Injector for MANDOROS.
Injects Web App Manifest metadata and Service Worker lifecycle code so users can install
MANDOROS as a standalone Desktop or Mobile app in 1 click with offline asset caching.
"""

from __future__ import annotations


PWA_HEAD_TAGS = """
<!-- MANDOROS Progressive Web App (PWA) Tags -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0F172A">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="MANDOROS">
<link rel="apple-touch-icon" href="/assets/favicon.ico">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/sw.js').then(function(reg) {
        console.log('[MANDOROS PWA] Service Worker registered at scope:', reg.scope);
      }).catch(function(err) {
        console.warn('[MANDOROS PWA] Service Worker registration failed:', err);
      });
    });
  }

  let mandorosPwaDeferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    mandorosPwaDeferredPrompt = e;
    const btns = document.querySelectorAll('.mandoros-pwa-install-btn');
    btns.forEach(btn => {
      btn.style.display = 'inline-flex';
      btn.onclick = () => {
        if (mandorosPwaDeferredPrompt) {
          mandorosPwaDeferredPrompt.prompt();
          mandorosPwaDeferredPrompt.userChoice.then((choice) => {
            if (choice.outcome === 'accepted') {
              console.log('[MANDOROS PWA] App installed successfully');
            }
            mandorosPwaDeferredPrompt = null;
          });
        }
      };
    });
  });

  window.addEventListener('appinstalled', () => {
    console.log('[MANDOROS PWA] Application was successfully installed');
    const btns = document.querySelectorAll('.mandoros-pwa-install-btn');
    btns.forEach(btn => {
      btn.innerHTML = '✅ MANDOROS App Installed';
      btn.disabled = true;
    });
  });
</script>
"""


def get_pwa_head_html() -> str:
    """Returns standard PWA head tags and service worker registration script."""
    return PWA_HEAD_TAGS


def inject_pwa_head_tags(existing_head: str) -> str:
    """Safely appends PWA tags to existing custom head string if not already present."""
    if "rel=\"manifest\"" in existing_head or "rel='manifest'" in existing_head:
        return existing_head
    return (existing_head or "") + "\n" + PWA_HEAD_TAGS
