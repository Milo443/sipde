# sipde_project/urls.py
from django.contrib import admin
from django.urls import path, include  # <-- Asegúrate de importar 'include'
from django.contrib.auth import views as auth_views
from core.views import Logout

urlpatterns = [
    path('admin/', admin.site.urls),

    # URLs de autenticación (Login y Logout)
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    #Url Modificada para redirigir a /login/ despues de cerrar sesion.
    #path('logout/', custom_logout, name='logout'),
    path('logout/', Logout, name='logout'),

    # Incluir todas las URLs de nuestra aplicación 'core'
    path('', include('core.urls')), # <-- AÑADIR ESTA LÍNEA
]