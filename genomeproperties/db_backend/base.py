from django.db.backends.sqlite3 import base

"""
Custom SQLite database backend with WAL mode and performance optimizations.

This backend extends Django's default SQLite backend to enable Write-Ahead Logging (WAL)
mode and other performance optimizations for production use.

Based on recommendations from: https://blog.pecar.me/sqlite-django-config
"""

class DatabaseWrapper(base.DatabaseWrapper):
    """
    Custom SQLite database wrapper with optimized settings.

    Configures SQLite with:
    - WAL (Write-Ahead Logging) mode for better concurrency
    - Optimized synchronous mode (NORMAL instead of FULL)
    - Memory-mapped I/O for faster access
    - Increased cache size
    - Foreign key constraints enabled
    - Journal size limits to manage WAL file growth
    """

    def get_new_connection(self, conn_params):
        """
        Create a new database connection with optimized PRAGMA settings.

        :param conn_params: Connection parameters
        :type conn_params: dict
        :return: Database connection with optimizations applied
        :rtype: sqlite3.Connection
        """
        conn = super().get_new_connection(conn_params)
        cursor = conn.cursor()

        # Enable WAL mode for better concurrency (readers don't block writers)
        cursor.execute("PRAGMA journal_mode=WAL;")

        # NORMAL synchronous mode balances safety with performance
        # Still crash-safe but faster than FULL
        cursor.execute("PRAGMA synchronous=NORMAL;")

        # Enable memory-mapped I/O (128MB) for faster file access
        cursor.execute("PRAGMA mmap_size=134217728;")

        # Limit WAL file size to ~25MB to prevent unbounded growth
        cursor.execute("PRAGMA journal_size_limit=27103364;")

        # Increase page cache size (negative = KB, positive = pages)
        # 2000 pages is roughly 8MB with 4KB page size
        cursor.execute("PRAGMA cache_size=2000;")

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON;")

        # Disable legacy alter table behavior for atomic renames on macOS
        cursor.execute("PRAGMA legacy_alter_table=OFF;")

        # Set busy timeout to 5 seconds
        cursor.execute("PRAGMA busy_timeout=5000;")

        cursor.close()
        return conn
