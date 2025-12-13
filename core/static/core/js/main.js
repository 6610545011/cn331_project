document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sideNav = document.getElementById('sideNav');
    const overlay = document.getElementById('overlay');
    const mainContainer = document.getElementById('mainContainer');

    // Toggle menu when clicking the menu button
    menuToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        sideNav.classList.toggle('minimized');
        overlay.classList.toggle('active');
    });

    // Close menu when clicking the overlay
    overlay.addEventListener('click', function() {
        sideNav.classList.add('minimized');
        overlay.classList.remove('active');
    });

    // Close menu when clicking the main container
    mainContainer.addEventListener('click', function(e) {
        if (!sideNav.contains(e.target) && !menuToggle.contains(e.target)) {
            sideNav.classList.add('minimized');
            overlay.classList.remove('active');
        }
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

// Use event delegation for clicks
document.body.addEventListener('click', function(e) {
    const bookmarkBtn = e.target.closest('.bookmark-btn');
    if (bookmarkBtn) {
        // If this is a review bookmark (has reviewId), the review script handles this behavior.
        if (bookmarkBtn.dataset.reviewId) return;
        e.preventDefault();
        const url = bookmarkBtn.dataset.url;

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
        })
        .then(response => {
            if (response.redirected && response.url && response.url.includes('/accounts/login')) {
                window.location.href = response.url + '?next=' + encodeURIComponent(location.pathname + location.search);
                return Promise.reject(new Error('auth'));
            }
            if (!response.ok) return Promise.reject(new Error('network')); 
            return response.json();
        })
        .then(data => {
                if (data.status === 'ok') {
                bookmarkBtn.classList.toggle('btn-primary', data.bookmarked);
                bookmarkBtn.classList.toggle('btn-outline-primary', !data.bookmarked);
                bookmarkBtn.innerHTML = data.bookmarked ? '<i class="fas fa-bookmark"></i>' : '<i class="far fa-bookmark"></i>';
            }
        })
        .catch(error => console.error('Error toggling bookmark:', error));
    }

    const deleteBtn = e.target.closest('.delete-review-btn');
    if (deleteBtn) {
        e.preventDefault();
        if (!confirm('Are you sure you want to delete this review?')) return;
        const url = deleteBtn.dataset.url;
        const reviewCard = deleteBtn.closest('.review-card');
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
        })
        .then(response => {
            if (response.redirected && response.url && response.url.includes('/accounts/login')) {
                window.location.href = response.url + '?next=' + encodeURIComponent(location.pathname + location.search);
                return Promise.reject(new Error('auth'));
            }
            if (!response.ok) return Promise.reject(new Error('network')); 
            return response.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                if (reviewCard) reviewCard.remove();
            }
        })
        .catch(error => console.error('Error deleting review:', error));
    }
});

// Use event delegation for form submissions
document.body.addEventListener('submit', function(e) {
    const form = e.target;

    if (form.matches('.report-form')) {
        // Skip review-specific report forms (handled by review_actions_js)
        if (form.id && form.id.startsWith('reportForm-')) return;
        e.preventDefault();
        const reviewId = form.id.split('-')[1];
        const formData = new FormData(form);
        const url = form.dataset.url;
        const alertContainer = document.getElementById(`report-alert-${reviewId}`);

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            body: formData,
            headers: {
                'X-CSRFToken': csrftoken,
            },
        })
        .then(response => {
            if (response.redirected && response.url && response.url.includes('/accounts/login')) {
                window.location.href = response.url + '?next=' + encodeURIComponent(location.pathname + location.search);
                return Promise.reject(new Error('auth'));
            }
            return response.json().then(data => ({ status: response.status, body: data }));
        })
        .then(({ status, body }) => {
            let alertClass = 'alert-danger';
            let message = 'An unknown error occurred.';

            if (status === 200 && body.status === 'ok') {
                alertClass = 'alert-success';
                message = body.message;
                form.reset();
                setTimeout(() => {
                    const modalEl = document.getElementById(`reportModal-${reviewId}`);
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) {
                        modal.hide();
                    }
                    alertContainer.innerHTML = '';
                }, 2500);
            } else {
                message = body.message || 'Please correct the errors below.';
            }
            alertContainer.innerHTML = `<div class="alert ${alertClass}" role="alert">${message}</div>`;
        })
        .catch(error => {
            console.error('Error:', error);
            alertContainer.innerHTML = `<div class="alert alert-danger" role="alert">A network error occurred. Please try again.</div>`;
        });
    }

    if (form.matches('.vote-form')) {
        // Skip review vote forms handled by review_actions_js
        if (form.dataset && form.dataset.reviewId) return;
        e.preventDefault();
        const reviewId = form.dataset.reviewId;
        const voteType = e.submitter.value;
        const url = form.dataset.url;

        const upvoteBtn = form.querySelector('.upvote-btn');
        const downvoteBtn = form.querySelector('.downvote-btn');
        upvoteBtn.disabled = true;
        downvoteBtn.disabled = true;

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'vote_type': voteType })
        })
        .then(response => {
            if (response.redirected && response.url && response.url.includes('/accounts/login')) {
                window.location.href = response.url + '?next=' + encodeURIComponent(location.pathname + location.search);
                return Promise.reject(new Error('auth'));
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                    // Update all score displays for this review (real-time on page)
                    const scoreSpans = document.querySelectorAll(`.vote-score[data-review-id="${reviewId}"]`);
                    scoreSpans.forEach(s => { s.textContent = data.new_score; });

                    // Update all vote buttons/forms for this review across the page
                    const voteForms = document.querySelectorAll(`.vote-form[data-review-id="${reviewId}"]`);
                    voteForms.forEach(formEl => {
                        const upBtn = formEl.querySelector('.upvote-btn');
                        const downBtn = formEl.querySelector('.downvote-btn');
                        if (upBtn) {
                            upBtn.classList.toggle('btn-success', data.user_vote == 1);
                            upBtn.classList.toggle('btn-outline-success', data.user_vote != 1);
                        }
                        if (downBtn) {
                            downBtn.classList.toggle('btn-danger', data.user_vote == -1);
                            downBtn.classList.toggle('btn-outline-danger', data.user_vote != -1);
                        }
                    });
            }
        })
        .catch(error => console.error('Error submitting vote:', error))
        .finally(() => {
            upvoteBtn.disabled = false;
            downvoteBtn.disabled = false;
        });
    }
});

// Modal helpers and fallback show/hide for report modal when Bootstrap is not available
document.addEventListener('shown.bs.modal', function(evt) {
    const modal = evt.target;
    if (!modal) return;
    const ta = modal.querySelector('textarea');
    if (ta) ta.focus();
});

document.addEventListener('hidden.bs.modal', function(evt) {
    const modal = evt.target;
    if (!modal) return;
    const alert = modal.querySelector('[id^="report-alert-"]');
    if (alert) alert.innerHTML = '';
    const form = modal.querySelector('form.report-form');
    if (form) form.reset();
});

// Fallback: if Bootstrap JS is not loaded, provide simple show/hide behavior for report modal
document.body.addEventListener('click', function(e) {
    const rb = e.target.closest('.report-btn');
    if (!rb) return;
    const reviewId = rb.dataset.reviewId;
    const modalEl = document.getElementById(`reportModal-${reviewId}`);
    console.log('Report button clicked:', { reviewId, modalExists: !!modalEl, bootstrap: typeof bootstrap });
    if (!modalEl) return;
    if (typeof bootstrap === 'undefined') {
        e.preventDefault();
        modalEl.style.display = 'block';
        modalEl.classList.add('show');
        modalEl.removeAttribute('aria-hidden');
        modalEl.setAttribute('aria-modal', 'true');
        if (!document.getElementById('_fallback_backdrop')) {
            const bd = document.createElement('div');
            bd.id = '_fallback_backdrop';
            bd.className = 'modal-backdrop fade show';
            document.body.appendChild(bd);
        }
        const ta = modalEl.querySelector('textarea');
        if (ta) ta.focus();
    }
});

// Fallback: close modal when clicking Cancel / close icon if Bootstrap not present
document.body.addEventListener('click', function(e) {
    const dismissBtn = e.target.closest('[data-bs-dismiss="modal"], .btn-close');
    if (!dismissBtn) return;
    console.log('Dismiss clicked (fallback handler):', { bootstrap: typeof bootstrap });
    if (typeof bootstrap !== 'undefined') return;
    const modalEl = e.target.closest('.modal');
    if (!modalEl) return;
    e.preventDefault();
    modalEl.style.display = 'none';
    modalEl.classList.remove('show');
    modalEl.setAttribute('aria-hidden', 'true');
    modalEl.removeAttribute('aria-modal');
    const bd = document.getElementById('_fallback_backdrop');
    if (bd) bd.remove();
});
