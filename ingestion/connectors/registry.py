"""Maps Website.connector_type to a connector class."""
from ingestion.connectors.base import ConnectorError

_REGISTRY = {}


def register(connector_type):
    def decorator(cls):
        cls.connector_type = connector_type
        _REGISTRY[connector_type] = cls
        return cls
    return decorator


def available_types():
    _load_builtin()
    return sorted(_REGISTRY)


def get_connector(website):
    _load_builtin()
    cls = _REGISTRY.get(website.connector_type)
    if cls is None:
        raise ConnectorError(
            f"Website '{website.name}' has connector_type '{website.connector_type}', which cannot be "
            f"synced. Available types: {', '.join(sorted(_REGISTRY))}."
        )
    return cls(website)


def _load_builtin():
    # Importing the package registers the built-in connectors.
    import ingestion.connectors  # noqa: F401
