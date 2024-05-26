from django.urls import path
from Teta.views import login_view, register, home, create_organization, create_event, event_detail, logout_view, edit_event, organization_detail
from django.contrib.auth.views import LogoutView
from django.contrib import admin

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('home/', home, name='home'),
    path('create_organization/', create_organization, name='create_organization'),
    path('create_event/', create_event, name='create_event'),
    path('', home, name='home'),
    path('home/', home, name='home'),
    path('create_event/', create_event, name='create_event'),
    path('event_detail/<int:event_id>/', event_detail, name='event_detail'),
    path('logout_confirmation/', logout_view, name='logout'),
    path('edit_event/<int:event_id>/', edit_event, name='edit_event'),
    path('admin/', admin.site.urls),
    path('organization/<int:organization_id>/', organization_detail, name='organization_detail'),

]
