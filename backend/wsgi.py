"""Production WSGI entry point.

Run with::

    gunicorn --workers 4 --threads 2 --bind 0.0.0.0:8000 wsgi:application

Threads matter: the live status endpoint holds a connection open for its whole
lifetime, so a purely process-based worker model runs out of capacity as soon as
a handful of dashboards are open.

Attributes:
    application: The WSGI callable gunicorn serves.
"""

from flask import Flask

from server import create_app

application: Flask = create_app()
