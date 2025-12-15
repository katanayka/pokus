from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from app.interfaces.rest import views as api


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return Response({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", health, name="health"),
    path("auth/register", api.register, name="register"),
    path("auth/login", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("catalog", api.catalog, name="catalog"),
    path("catalog/search", api.catalog_search, name="catalog_search"),
    path("catalog/select", api.select_pokemon, name="select_pokemon"),
    path("catalog/team", api.team, name="team"),
    path("catalog/<int:pokemon_id>", api.pokemon_detail, name="pokemon_detail"),
    path("lobby", api.enter_lobby, name="lobby"),
    path("lobby/code", api.code_lobby, name="lobby_code"),
    path("lobby/code/close", api.close_code_lobby, name="lobby_code_close"),
    path("battle/start", api.start_battle, name="battle_start"),
    path("battle/pve", api.battle_pve, name="battle_pve"),
    path("battle/<int:battle_id>/turn", api.play_turn, name="battle_turn"),
    path("battles", api.history, name="history"),
    path("battles/<int:battle_id>", api.battle_detail, name="battle_detail"),
    path("battles/<int:battle_id>/replay", api.replay, name="replay"),
    path("stats/me", api.stats, name="stats"),
]
