# REST API: adding new endpoints

This page explains how to add a new REST endpoint to `aurora.api`, following
the conventions of the existing codebase.

## Routing

All API routes are defined in `aurora/api/urls.py` and mounted at `/api/`.
Resources are registered on an `AuroraRouter` (a DRF `DefaultRouter` whose API
root answers `401` for anonymous users):

```python
from . import viewsets
from .router import AuroraRouter

router = AuroraRouter()
router.register(r"counter", viewsets.CounterViewSet)
# ... new resources here ...
```

Non-model endpoints (actions, custom views) can be added to `urlpatterns`
next to `path("sys/", viewsets.system_info)`. Model-backed endpoints should
always be registered on the router so that the schema and API root stay in
sync.

## Viewsets

Extend `SmartViewSet` (`aurora/api/viewsets/base.py`), which provides:

- read-only behavior (`ReadOnlyModelViewSet`),
- session, token and basic authentication,
- root-user / model-permissions based authorization,
- filtering with the `modified_after` filter.

```python
from .base import SmartViewSet

class MyViewSet(SmartViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
```

Custom actions use the DRF `@action` decorator, e.g. the `records` and `csv`
actions of `RegistrationViewSet` (`aurora/api/viewsets/registration.py`).
Actions that must be reachable without authentication can relax permissions
per action:

```python
@action(detail=True, permission_classes=[AllowAny])
def metadata(self, request, pk=None):
    return Response(self.get_object().metadata)
```

## Serializers

Serializers live in `aurora/api/serializers/`, one module per resource.
Nested and versioned payloads are split in multiple serializers when needed
(the registration module exposes list, detail and record serializers, plus
encrypted and storage variants).

## Schema

The OpenAPI schema is generated automatically by drf-spectacular from the
viewset declarations. Keep the `SPECTACULAR_SETTINGS` block in
`aurora/config/settings.py` up to date when you change the API surface, and
verify the schema renders with the new routes.

## Testing

API tests live next to the viewsets. Test at minimum:

- the permission matrix (anonymous, authenticated without permissions, root),
- pagination and the `modified_after` filter,
- every custom action, including its error cases.

Run the API tests with:

    pytest tests -k api
