from django.urls import path

from . import views

urlpatterns = [
    path("insertdata", views.insertdata, name="index"),
    path('pokemondata/', views.get_pokemon_data, name="pokemon"),
    path('pokemondata/<int:pk>/', views.get_pokemon_data, name="pokemon"),
]