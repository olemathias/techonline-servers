from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:entry_id>', views.entry),
    path('<int:entry_id>/delete', views.delete_entry),
    path('new', views.new_entry, name='new_entry'),
    path('api/entries/<type>', views.api_entries, name='api_entries'),
]
