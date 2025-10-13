# sipde_project/urls.py
from django.contrib import admin
from django.urls import path, include  # <-- Asegúrate de importar 'include'
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # URLs de autenticación (Login y Logout)
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Incluir todas las URLs de nuestra aplicación 'core'
    path('', include('core.urls')), # <-- AÑADIR ESTA LÍNEA
]