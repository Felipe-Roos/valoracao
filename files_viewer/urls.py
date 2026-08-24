from django.urls import path, re_path

from . import views

app_name = 'files_viewer'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('projeto/<slug:project_slug>/', views.file_list, name='file_list'),
    re_path(
        r'^projeto/(?P<project_slug>[-\w]+)/preview/(?P<rel_path>.+)$',
        views.file_preview,
        name='file_preview',
    ),
    re_path(
        r'^projeto/(?P<project_slug>[-\w]+)/download/(?P<rel_path>.+)$',
        views.file_download,
        name='file_download',
    ),
]
