from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


class UserPokemon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pokemons")
    pokemon_id = models.IntegerField()
    name = models.CharField(max_length=128)
    stats = models.JSONField()
    types = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "pokemon_id")


class ActivePokemon(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    pokemon = models.ForeignKey(UserPokemon, on_delete=models.CASCADE)
    selected_at = models.DateTimeField(default=timezone.now)


class ActiveTeam(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    pokemon_ids = models.JSONField(default=list)
    selected_at = models.DateTimeField(default=timezone.now)


class LobbyEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pokemon_id = models.IntegerField()
    team_ids = models.JSONField(default=list)
    code = models.CharField(max_length=4, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], condition=Q(code__isnull=False), name="uniq_lobby_code"),
        ]


class Battle(models.Model):
    p1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="battles_as_p1")
    p2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="battles_as_p2")
    p1_pokemon_id = models.IntegerField()
    p2_pokemon_id = models.IntegerField()
    p1_team_ids = models.JSONField(default=list)
    p2_team_ids = models.JSONField(default=list)
    seed = models.BigIntegerField()
    status = models.CharField(max_length=32, default="active")
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)


class BattleEvent(models.Model):
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name="events")
    turn = models.IntegerField()
    payload = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)


class Statistics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    damage = models.IntegerField(default=0)
    crits = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
