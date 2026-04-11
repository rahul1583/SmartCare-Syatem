from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    # Prescription Management
    path('', views.prescription_list_view, name='list'),
    path('<int:prescription_id>/', views.prescription_detail_view, name='detail'),
    path('create/', views.create_prescription_view, name='create'),
    path('<int:prescription_id>/update/', views.update_prescription_view, name='update'),
    path('<int:prescription_id>/download/', views.download_prescription_view, name='download'),
    path('<int:prescription_id>/print/', views.print_prescription_view, name='print'),
]
