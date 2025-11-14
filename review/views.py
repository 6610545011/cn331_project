# review/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q, Sum

from .forms import ReviewForm, ReportForm, ReviewUpvoteForm
from .models import Review, Bookmark, Report, ReviewUpvote
from core.models import Course, Section, Prof


@login_required
def write_review(request):
    # This is a placeholder for your existing write_review view
    # to make this file complete.
    # You would have your full logic here.
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            return redirect('core:homepage')
    else:
        form = ReviewForm()
    return render(request, 'review/write_review.html', {'form': form})


@login_required
@require_POST
def vote_review(request, review_id):
    """
    Handles AJAX requests for upvoting or downvoting a review.
    """
    review = get_object_or_404(Review, pk=review_id)
    form = ReviewUpvoteForm(request.POST)

    if form.is_valid():
        vote_type = form.cleaned_data['vote_type']

        try:
            with transaction.atomic():
                # Get the existing vote, or create a new one
                vote, created = ReviewUpvote.objects.get_or_create(
                    user=request.user,
                    review=review,
                    defaults={'vote_type': vote_type}
                )

                if not created:
                    # If the user is clicking the same button again, cancel the vote
                    if vote.vote_type == vote_type:
                        vote.delete()
                    else:
                        # If they are changing their vote (e.g., from up to down)
                        vote.vote_type = vote_type
                        vote.save()

                # Recalculate the score
                new_score = ReviewUpvote.objects.filter(review=review).aggregate(score=Sum('vote_type'))['score'] or 0
                return JsonResponse({'status': 'ok', 'new_score': new_score})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid form submission.'}, status=400)


@login_required
@require_POST
def toggle_bookmark(request, review_id):
    # Placeholder for your bookmark logic
    review = get_object_or_404(Review, pk=review_id)
    # ... your logic here ...
    return JsonResponse({'status': 'ok', 'bookmarked': True})


@login_required
@require_POST
def report_review(request, review_id):
    # Placeholder for your report logic
    review = get_object_or_404(Review, pk=review_id)
    # ... your logic here ...
    return JsonResponse({'status': 'ok', 'message': 'Report submitted.'})


# Placeholder for your AJAX views
def ajax_search_courses(request):
    return JsonResponse({'results': []})

def ajax_get_professors(request):
    return JsonResponse({'professors': []})

def ajax_get_sections_for_course(request):
    return JsonResponse({'sections': []})