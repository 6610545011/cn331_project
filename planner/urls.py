from django.urls import path
from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.planner_view, name='planner_view'),
    path('add/<int:section_id>/', views.add_section_to_planner, name='add_section'),
    path('remove/<int:section_id>/', views.remove_section_from_planner, name='remove_section'),
    # Variant endpoints
    path('variant/create/', views.create_variant, name='create_variant'),
    path('variant/list/', views.list_variants, name='list_variants'),
    path('variant/save_current/', views.save_current_variant, name='save_current_variant'),
    path('variant/<int:variant_id>/load/', views.load_variant, name='load_variant'),
    path('variant/<int:variant_id>/delete/', views.delete_variant, name='delete_variant'),
    path('variant/<int:variant_id>/add/<int:section_id>/', views.add_section_to_variant, name='variant_add_section'),
    path('variant/<int:variant_id>/remove/<int:section_id>/', views.remove_section_from_variant, name='variant_remove_section'),
    # user schedule editing: add schedule slot to a section
    path('schedule/add/', views.add_section_schedule, name='add_section_schedule'),
    # search sections
    path('search/', views.search_sections, name='search_sections'),
]
