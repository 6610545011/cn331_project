from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_alter_coursesearchstat_unique_together_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                """
                CREATE TABLE IF NOT EXISTS core_dailyactiveuser (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
                    UNIQUE(user_id, date)
                );
                CREATE INDEX IF NOT EXISTS core_dailya_date_8a8a70_idx ON core_dailyactiveuser(date);
                """
            ),
            reverse_sql=(
                """
                DROP INDEX IF EXISTS core_dailya_date_8a8a70_idx;
                DROP TABLE IF EXISTS core_dailyactiveuser;
                """
            ),
        ),
    ]
