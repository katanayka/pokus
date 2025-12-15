from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_team_battles"),
    ]

    operations = [
        migrations.AddField(
            model_name="lobbyentry",
            name="code",
            field=models.CharField(blank=True, db_index=True, max_length=4, null=True),
        ),
        migrations.AddConstraint(
            model_name="lobbyentry",
            constraint=models.UniqueConstraint(
                fields=("code",),
                condition=models.Q(("code__isnull", False)),
                name="uniq_lobby_code",
            ),
        ),
    ]
