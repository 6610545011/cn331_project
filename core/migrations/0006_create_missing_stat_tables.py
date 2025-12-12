from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_create_missing_dau_table"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                """
                CREATE TABLE IF NOT EXISTS core_coursesearchstat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    course_id INTEGER NOT NULL REFERENCES core_course(id) ON DELETE CASCADE,
                    UNIQUE(course_id, date)
                );
                CREATE INDEX IF NOT EXISTS core_coursesearchstat_date_idx ON core_coursesearchstat(date);
                CREATE INDEX IF NOT EXISTS core_coursesearchstat_course_idx ON core_coursesearchstat(course_id);

                CREATE TABLE IF NOT EXISTS core_courseviewstat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    course_id INTEGER NOT NULL REFERENCES core_course(id) ON DELETE CASCADE,
                    UNIQUE(course_id, date)
                );
                CREATE INDEX IF NOT EXISTS core_courseviewstat_date_idx ON core_courseviewstat(date);
                CREATE INDEX IF NOT EXISTS core_courseviewstat_course_idx ON core_courseviewstat(course_id);

                CREATE TABLE IF NOT EXISTS core_coursereviewstat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    course_id INTEGER NOT NULL REFERENCES core_course(id) ON DELETE CASCADE,
                    UNIQUE(course_id, date)
                );
                CREATE INDEX IF NOT EXISTS core_coursereviewstat_date_idx ON core_coursereviewstat(date);
                CREATE INDEX IF NOT EXISTS core_coursereviewstat_course_idx ON core_coursereviewstat(course_id);
                """
            ),
            reverse_sql=(
                """
                DROP INDEX IF EXISTS core_coursesearchstat_date_idx;
                DROP INDEX IF EXISTS core_coursesearchstat_course_idx;
                DROP TABLE IF EXISTS core_coursesearchstat;

                DROP INDEX IF EXISTS core_courseviewstat_date_idx;
                DROP INDEX IF EXISTS core_courseviewstat_course_idx;
                DROP TABLE IF EXISTS core_courseviewstat;

                DROP INDEX IF EXISTS core_coursereviewstat_date_idx;
                DROP INDEX IF EXISTS core_coursereviewstat_course_idx;
                DROP TABLE IF EXISTS core_coursereviewstat;
                """
            ),
        ),
    ]
