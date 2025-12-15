from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserPokemon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pokemon_id", models.IntegerField()),
                ("name", models.CharField(max_length=128)),
                ("stats", models.JSONField()),
                ("types", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pokemons",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "pokemon_id")},
            },
        ),
        migrations.CreateModel(
            name="Battle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("p1_pokemon_id", models.IntegerField()),
                ("p2_pokemon_id", models.IntegerField()),
                ("seed", models.BigIntegerField()),
                ("status", models.CharField(default="active", max_length=32)),
                ("result", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "p1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="battles_as_p1",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "p2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="battles_as_p2",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LobbyEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pokemon_id", models.IntegerField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Statistics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wins", models.IntegerField(default=0)),
                ("losses", models.IntegerField(default=0)),
                ("damage", models.IntegerField(default=0)),
                ("crits", models.IntegerField(default=0)),
                ("win_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ActivePokemon",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("selected_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("pokemon", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="app.userpokemon")),
            ],
        ),
        migrations.CreateModel(
            name="BattleEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("turn", models.IntegerField()),
                ("payload", models.JSONField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "battle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="events", to="app.battle"
                    ),
                ),
            ],
        ),
    ]
