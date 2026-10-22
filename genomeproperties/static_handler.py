from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.contrib.staticfiles.views import serve


def _serve_from_path_info(self, request):
    """Look up files with PATH_INFO, not request.path.

    With FORCE_SCRIPT_NAME and no reverse proxy, request.path is
    SCRIPT_NAME + PATH_INFO, so GraphiQL 404s on
    /genomeproperties/api/static/graphene_django/graphiql.js.
    """
    return serve(request, self.file_path(request.path_info), insecure=True)


# django.contrib.staticfiles' runserver wins over an app-level command,
# so patch the handler class that runserver actually uses.
StaticFilesHandler.serve = _serve_from_path_info
