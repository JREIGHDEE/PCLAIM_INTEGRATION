"""One-time logging configuration, replacing scattered print() statements."""
import logging
import sys


def configure_logging(debug=False):
    """Configure the root logger once. Safe to call multiple times."""
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ))
        root.addHandler(handler)

    root.setLevel(level)
    # Werkzeug's own request-line logging is noisy at INFO; keep it at
    # WARNING unless we're actively debugging.
    logging.getLogger("werkzeug").setLevel(logging.INFO if debug else logging.WARNING)
    return root
