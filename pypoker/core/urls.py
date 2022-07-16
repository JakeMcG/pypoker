from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('retrieve/', views.retrieve, name='retrieve'),
    path('preflop/', views.preflop, name='preflop'),
    path('outcomes/', views.outcomes, name='outcomes')
]