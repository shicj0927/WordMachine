// Basic utility functions

// Global error handlers to avoid third-party script failures (e.g. adoptedStyleSheets issues)
window.addEventListener('error', function (event) {
    try {
        const msg = event && event.message ? event.message.toString() : '';
        if (msg && msg.includes('adoptedStyleSheets')) {
            // swallow this specific error so it doesn't break our app
            console.warn('Ignored non-fatal error:', msg);
            event.preventDefault && event.preventDefault();
            return true;
        }
    } catch (e) {
        // no-op
    }
});

window.addEventListener('unhandledrejection', function (event) {
    try {
        const reason = event && event.reason ? event.reason : '';
        if (typeof reason === 'string' && reason.includes('adoptedStyleSheets')) {
            console.warn('Ignored non-fatal promise rejection:', reason);
            event.preventDefault && event.preventDefault();
        }
    } catch (e) {
        // no-op
    }
});

// Show error message
function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
        errorEl.style.display = 'block';
    }
}

// Clear error message
function clearError(elementId) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = '';
        errorEl.classList.add('hidden');
        errorEl.style.display = 'none';
    }
}

// Validate email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate password strength
function validatePassword(password) {
    return password && password.length >= 6;
}

// Validate username
function validateUsername(username) {
    return username && username.length >= 3 && username.length <= 255;
}

// Show loading spinner
function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    // If element is a table or tbody, insert a loading table row instead of
    // replacing innerHTML (which would remove existing rows).
    const tag = el.tagName;
    if (tag === 'TBODY' || tag === 'TABLE') {
        // avoid duplicate loading rows
        if (el.querySelector('.loading-row')) return;

        const table = tag === 'TABLE' ? el : el.closest('table');
        const ths = table ? table.querySelectorAll('thead th').length : 1;
        const colspan = ths && ths > 0 ? ths : 1;

        const tr = document.createElement('tr');
        tr.className = 'loading-row';
        const td = document.createElement('td');
        td.colSpan = colspan;
        td.className = 'text-center';
        td.innerHTML = '<div class="loading"></div> 加载中...';
        tr.appendChild(td);

        if (tag === 'TABLE') {
            let tbody = el.querySelector('tbody');
            if (!tbody) {
                tbody = document.createElement('tbody');
                el.appendChild(tbody);
            }
            tbody.appendChild(tr);
        } else {
            el.appendChild(tr);
        }

        return;
    }

    // Generic container: append a loading wrapper rather than clearing content
    if (el.querySelector('.loading-wrapper')) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'loading-wrapper';
    wrapper.innerHTML = '<div class="loading"></div>';
    el.appendChild(wrapper);
    wrapper.style.display = 'block';
}

// Clear loading spinner
function clearLoading(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const tag = el.tagName;
    if (tag === 'TBODY' || tag === 'TABLE') {
        // remove any loading rows inside the table/tbody
        const rows = el.querySelectorAll('.loading-row');
        rows.forEach(r => r.remove());
        return;
    }

    const wrapper = el.querySelector('.loading-wrapper');
    if (wrapper) {
        wrapper.remove();
    }
}

// Show alert message
function showAlert(message, type = 'danger') {
    const alertEl = document.getElementById('alert');
    if (alertEl) {
        alertEl.className = `alert alert-${type}`;
        alertEl.textContent = message;
        alertEl.style.display = 'block';
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            alertEl.style.display = 'none';
        }, 5000);
    }
}

// Make API request
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Disable form button
function disableButton(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        // If it's a form, disable all buttons in it
        if (el.tagName === 'FORM') {
            const buttons = el.querySelectorAll('button[type="submit"]');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('disabled');
            });
        } else {
            el.disabled = true;
            el.classList.add('disabled');
        }
    }
}

// Enable form button
function enableButton(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        // If it's a form, enable all buttons in it
        if (el.tagName === 'FORM') {
            const buttons = el.querySelectorAll('button[type="submit"]');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('disabled');
            });
        } else {
            el.disabled = false;
            el.classList.remove('disabled');
        }
    }
}

// Get form data as object
function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value.trim();
    }
    
    return data;
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Get current date formatted
function getCurrentDate() {
    const date = new Date();
    return date.toISOString().split('T')[0];
}

// Truncate text
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Debounce function for search and input events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Check if string is empty
function isEmpty(str) {
    return !str || str.trim().length === 0;
}

// Escape HTML characters
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Diagnostic intercepts: log and block accidental navigation or requests to `/delete`.
// This helps identify whether a request to 127.0.0.1:3000/delete originates
// from our app or from an external extension/dev-server.
(function () {
    // Wrap fetch
    try {
        const _fetch = window.fetch;
        window.fetch = async function (input, init) {
            try {
                const url = typeof input === 'string' ? input : (input && input.url) || '';
                if (url && url.includes('/delete') && !url.includes('/api/admin')) {
                    console.warn('[diagnostic] fetch to /delete detected:', url);
                    console.trace();
                }
            } catch (e) {
                console.warn('fetch diagnostic error:', e);
            }
            return _fetch.apply(this, arguments);
        };
    } catch (e) {
        // ignore
    }

    // Wrap XHR open to detect calls to /delete
    try {
        const origOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function (method, url) {
            try {
                if (url && url.includes('/delete') && !url.includes('/api/admin')) {
                    console.warn('[diagnostic] XHR open to /delete detected:', method, url);
                    console.trace();
                }
            } catch (e) {
                // ignore
            }
            return origOpen.apply(this, arguments);
        };
    } catch (e) {
        // ignore
    }

    // Prevent direct anchor navigation to /delete (may be from injected link)
    document.addEventListener('click', function (e) {
        try {
            const a = e.target.closest && e.target.closest('a[href]');
            if (!a) return;
            const href = a.getAttribute('href');
            if (!href) return;
            // Exact match or path ending with /delete
            if (href === '/delete' || /\/delete($|\?|#)/.test(href)) {
                console.warn('[diagnostic] prevented anchor navigation to /delete', href);
                e.preventDefault();
                e.stopPropagation && e.stopPropagation();
            }
        } catch (err) {
            // ignore
        }
    }, true);

})();
