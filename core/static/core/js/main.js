
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
        e.preventDefault();
        const url = bookmarkBtn.dataset.url;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                bookmarkBtn.classList.toggle('btn-primary', data.bookmarked);
                bookmarkBtn.classList.toggle('btn-outline-primary', !data.bookmarked);
                bookmarkBtn.innerHTML = data.bookmarked ? '<i class="fas fa-bookmark"></i> Bookmarked' : '<i class="far fa-bookmark"></i> Bookmark';
            }
        })
        .catch(error => console.error('Error toggling bookmark:', error));
    }
});

// Use event delegation for form submissions
document.body.addEventListener('submit', function(e) {
    const form = e.target;

    if (form.matches('.report-form')) {
        e.preventDefault();
        const reviewId = form.id.split('-')[1];
        const formData = new FormData(form);
        const url = form.dataset.url;
        const alertContainer = document.getElementById(`report-alert-${reviewId}`);

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrftoken,
            },
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
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
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'vote_type': voteType })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                const scoreSpan = document.querySelector(`.vote-score[data-review-id="${reviewId}"]`);
                scoreSpan.textContent = data.new_score;

                upvoteBtn.classList.toggle('btn-success', data.user_vote == 1);
                upvoteBtn.classList.toggle('btn-outline-success', data.user_vote != 1);
                downvoteBtn.classList.toggle('btn-danger', data.user_vote == -1);
                downvoteBtn.classList.toggle('btn-outline-danger', data.user_vote != -1);
            }
        })
        .catch(error => console.error('Error submitting vote:', error))
        .finally(() => {
            upvoteBtn.disabled = false;
            downvoteBtn.disabled = false;
        });
    }
});
