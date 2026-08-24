from django.urls import path

from . import views

app_name = 'valuation'

urlpatterns = [
    path('projeto/<slug:project_slug>/valoracao/', views.year_list, name='year_list'),
    path('projeto/<slug:project_slug>/valoracao/novo-ano/', views.year_create, name='year_create'),
    path('projeto/<slug:project_slug>/valoracao/<int:year>/', views.year_detail, name='year_detail'),
    path('projeto/<slug:project_slug>/valoracao/<int:year>/itens/', views.entry_create, name='entry_create'),
    path(
        'projeto/<slug:project_slug>/valoracao/<int:year>/itens/<int:entry_id>/excluir/',
        views.entry_delete,
        name='entry_delete',
    ),
]
