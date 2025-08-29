// Global JavaScript functions for Rental CRM

// API request helper
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return;
    }
    
    return response;
}

// Authentication check
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    
    // Verify token validity
    fetch('/auth/verify', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
    })
    .catch(() => {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    });
    
    return true;
}

// Logout function
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// Loading state management
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.remove('d-none');
    }
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.add('d-none');
    }
}

// Error handling
function showError(message) {
    const errorAlert = document.getElementById('error-alert');
    const errorMessage = document.getElementById('error-message');
    
    if (errorAlert && errorMessage) {
        errorMessage.textContent = message;
        errorAlert.classList.remove('d-none');
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            hideError();
        }, 5000);
    }
}

function hideError() {
    const errorAlert = document.getElementById('error-alert');
    if (errorAlert) {
        errorAlert.classList.add('d-none');
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('ka-GE', {
        style: 'currency',
        currency: 'GEL',
        minimumFractionDigits: 2
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// Format datetime
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Get status badge HTML
function getStatusBadge(status) {
    const statusMap = {
        'available': { text: 'Доступна', class: 'bg-success' },
        'rented': { text: 'Сдана', class: 'bg-danger' },
        'maintenance': { text: 'Обслуживание', class: 'bg-warning text-dark' }
    };
    
    const statusInfo = statusMap[status] || { text: 'Неизвестно', class: 'bg-secondary' };
    return `<span class="badge ${statusInfo.class}">${statusInfo.text}</span>`;
}

// Get rental type text
function getRentalTypeText(type) {
    return type === 'short_term' ? 'Краткосрочная' : 'Долгосрочная';
}

// Create loading spinner
function createLoadingSpinner() {
    return `
        <div class="d-flex justify-content-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        </div>
    `;
}

// Create empty state
function createEmptyState(message, icon = 'bi-inbox') {
    return `
        <div class="text-center p-4">
            <i class="${icon} display-4 text-muted mb-3"></i>
            <p class="text-muted">${message}</p>
        </div>
    `;
}

// Confirm dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Show success toast
function showSuccessToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-check-circle me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Show error toast
function showErrorToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-exclamation-triangle me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Form validation helpers
function validateRequired(value, fieldName) {
    if (!value || value.trim() === '') {
        throw new Error(`${fieldName} обязательно для заполнения`);
    }
    return value.trim();
}

function validateNumber(value, fieldName, min = 0) {
    const num = parseFloat(value);
    if (isNaN(num) || num < min) {
        throw new Error(`${fieldName} должно быть числом больше ${min}`);
    }
    return num;
}

function validateDate(value, fieldName) {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
        throw new Error(`${fieldName} имеет неверный формат`);
    }
    return date;
}

function validatePhone(value, fieldName) {
    const phone = value.replace(/\D/g, '');
    if (phone.length < 9) {
        throw new Error(`${fieldName} должен содержать минимум 9 цифр`);
    }
    return value.trim();
}

// Table helpers
function createDataTable(tableId, data, columns, options = {}) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Clear existing content
    table.innerHTML = '';
    
    // Create table structure
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column.title;
        if (column.sortable) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => sortTable(column.key));
        }
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        columns.forEach(column => {
            const td = document.createElement('td');
            
            if (column.render) {
                td.innerHTML = column.render(row[column.key], row);
            } else {
                td.textContent = row[column.key] || '';
            }
            
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    
    // Add table classes
    table.className = 'table table-striped table-hover';
}

// Sort table function
let currentSortColumn = null;
let currentSortDirection = 'asc';

function sortTable(column) {
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }
    
    // Trigger re-render with sorting
    // This should be implemented in each page's specific sorting logic
}

// Modal helpers
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    }
}

// Form helpers
function clearForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        // Clear validation states
        form.classList.remove('was-validated');
        const invalidElements = form.querySelectorAll('.is-invalid');
        invalidElements.forEach(el => el.classList.remove('is-invalid'));
    }
}

function setFormData(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    Object.keys(data).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = data[key];
            } else {
                input.value = data[key] || '';
            }
        }
    });
}

function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

// URL helpers
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    
    for (let [key, value] of params.entries()) {
        result[key] = value;
    }
    
    return result;
}

function updateUrlParams(params) {
    const url = new URL(window.location);
    
    Object.keys(params).forEach(key => {
        if (params[key]) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    window.history.pushState({}, '', url);
}

// Debounce function
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

// Initialize page on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication on every page except login
    if (!window.location.pathname.includes('/login')) {
        checkAuth();
    }
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Global error handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showErrorToast('Произошла непредвиденная ошибка');
});

// Export functions for use in other scripts
window.RentalCRM = {
    apiRequest,
    checkAuth,
    logout,
    showLoading,
    hideLoading,
    showError,
    hideError,
    formatCurrency,
    formatDate,
    formatDateTime,
    getStatusBadge,
    getRentalTypeText,
    createLoadingSpinner,
    createEmptyState,
    confirmAction,
    showSuccessToast,
    showErrorToast,
    validateRequired,
    validateNumber,
    validateDate,
    validatePhone,
    createDataTable,
    showModal,
    hideModal,
    clearForm,
    setFormData,
    getFormData,
    getUrlParams,
    updateUrlParams,
    debounce
};
