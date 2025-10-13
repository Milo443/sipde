# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL para el Dashboard principal
    path('', views.dashboard_view, name='dashboard'),

    # URL para la lista de todos los estudiantes
    path('estudiantes/', views.lista_estudiantes_view, name='lista_estudiantes'),

    # URL para ver el detalle de un estudiante específico
    path('estudiantes/<str:id_estudiante>/', views.detalle_estudiante_view, name='detalle_estudiante'),

    #URL para el modulo de validacion experimental de la prediccion.
    path('validacion/', views.validacion_view, name='validacion'),
]