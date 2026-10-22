from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _configure_sqlite(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=5000;")


class GenomePropertiesConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "genomeproperties"
    verbose_name = "Genome Properties"

    def ready(self):
        connection_created.connect(_configure_sqlite)
