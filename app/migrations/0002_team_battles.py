from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActiveTeam",
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
                ("pokemon_ids", models.JSONField(default=list)),
                ("selected_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.AddField(
            model_name="lobbyentry",
            name="team_ids",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="battle",
            name="p1_team_ids",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="battle",
            name="p2_team_ids",
            field=models.JSONField(default=list),
        ),
    ]
