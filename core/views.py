# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Exists, OuterRef, Sum, Case, When, IntegerField
from .models import Prof, Course, Section
from itertools import chain
from django.http import Http404, HttpResponsePermanentRedirect
from review.models import Bookmark, Review, ReviewUpvote

def homepage_view(request):
    return render(request, 'core/homepage.html')

# เพิ่มฟังก์ชันนี้เข้าไป
def about_view(request):
    return render(request, 'core/about.html')

def search(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', 'alphabetical') # Default to 'alphabetical'
    order = request.GET.get('order', 'asc') # Default to 'asc'

    order_prefix = '-' if order == 'desc' else ''    

    # Annotate reviews with vote score and the current user's vote
    # This annotation must work for both authenticated and unauthenticated users.
    reviews_queryset = Review.objects.annotate(
        vote_score=Sum('votes__vote_type', default=0),
        user_vote=Case(
            # When the user is not authenticated, request.user is AnonymousUser,
            # which doesn't have a pk, so the filter `votes__user=request.user`
            # will correctly not match anything.
            # This is more robust than checking `is_authenticated` beforehand.
            When(votes__user=request.user, then='votes__vote_type'),
            default=0,
            output_field=IntegerField()
        )
    ).select_related('course', 'prof', 'user').distinct()

    if query:
        # Use __icontains for broad, case-insensitive matching.
        professors = Prof.objects.filter(
            Q(prof_name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

        courses = Course.objects.filter(
            Q(course_code__icontains=query) |
            Q(course_name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

        sections = Section.objects.filter(
            Q(course__course_code__icontains=query) |
            Q(course__course_name__icontains=query) |
            Q(teachers__prof_name__icontains=query)
        ).select_related('course').prefetch_related('teachers').distinct()

        reviews = reviews_queryset.filter(
            Q(head__icontains=query) |
            Q(body__icontains=query)
        )
    else:
        # If no query is provided, return all objects.
        professors = Prof.objects.all()
        courses = Course.objects.all()
        sections = Section.objects.select_related('course').prefetch_related('teachers').all()
        reviews = reviews_queryset.all()
    
    # Apply sorting to individual querysets
    if sort_by == 'alphabetical':
        professors = professors.order_by(f'{order_prefix}prof_name')
        courses = courses.order_by(f'{order_prefix}course_name')
        sections = sections.order_by(f'{order_prefix}course__course_name', f'{order_prefix}section_number')
        reviews = reviews.order_by(f'{order_prefix}head')

    # Combine all querysets into a single list for the "All" tab
    # The individual querysets are already sorted, so we just need to merge them.
    # The lambda sort here is a fallback and helps group similar items if not perfectly pre-sorted.
    all_results = sorted(
        list(chain(professors, courses, sections, reviews)),
        key=lambda instance: getattr(instance, 'prof_name', 
                                 getattr(instance, 'course_name', 
                                         getattr(instance, 'head', str(instance)))),
        reverse=(order == 'desc')
    )

    context = {
        'query': query,
        'sort_by': sort_by,
        'order': order,
        'results': all_results, # This is for the "All" tab, which is not currently implemented in the template but the logic is here.
        'professors': professors,
        'courses': courses,
        'sections': sections,
        'reviews': reviews,
    }
    return render(request, 'core/search.html', context)

def prof_detail(request, pk):
    # Prepare subqueries for annotations
    user_bookmark_subquery = Bookmark.objects.none()
    if request.user.is_authenticated:
        user_bookmark_subquery = Bookmark.objects.filter(
            user=request.user,
            review=OuterRef('pk')
        )

    prof = get_object_or_404(
        Prof.objects.prefetch_related('teaching_sections__course'), 
        pk=pk
    )

    # Annotate the reviews for this professor
    reviews = prof.reviews.select_related('user', 'course').annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        vote_score=Sum('votes__vote_type', default=0),
        user_vote=Case(
            When(votes__user=request.user, then='votes__vote_type'),
            default=0,
            output_field=IntegerField()
        )
    ).distinct()

    return render(request, 'core/prof_detail.html', {'prof': prof, 'reviews': reviews})

def course_detail(request, pk):
    # Prepare subqueries for annotations
    user_bookmark_subquery = Bookmark.objects.none()
    if request.user.is_authenticated:
        user_bookmark_subquery = Bookmark.objects.filter(
            user=request.user,
            review=OuterRef('pk')
        )

    course = get_object_or_404(
        Course.objects.prefetch_related('sections__teachers', 'sections__campus'),
        pk=pk
    )
    
    reviews = course.reviews.select_related('user', 'prof').annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        vote_score=Sum('votes__vote_type', default=0),
        user_vote=Case(
            When(votes__user=request.user, then='votes__vote_type'),
            default=0,
            output_field=IntegerField()
        )
    ).distinct()

    return render(request, 'core/course_detail.html', {'course': course, 'reviews': reviews})