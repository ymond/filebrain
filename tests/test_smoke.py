"""Smoke test: verify the filebrain package is importable and pytest runs."""


def test_import_filebrain():
    """The filebrain package should be importable."""
    import filebrain

    assert hasattr(filebrain, "__version__")


def test_subpackages_importable():
    """All subpackages should be importable."""
    import filebrain.watcher
    import filebrain.extractors
    import filebrain.embeddings
    import filebrain.store
    import filebrain.query
    import filebrain.cli
