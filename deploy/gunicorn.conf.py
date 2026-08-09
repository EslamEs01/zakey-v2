"""Gunicorn configuration for ZAKEY (T-2001).

Values are chosen for a small single-host deployment and are deliberately
conservative. Nothing here is a secret; everything environment-specific comes
from the environment.

**Not deployed.** This file is a reviewed artifact; no ZAKEY process has been
started on any server from this repository.
"""

from __future__ import annotations

import multiprocessing
import os

# Bind to a loopback socket only. Nginx terminates TLS and proxies to it, so the
# application is never directly reachable from the network.
bind = os.environ.get("ZAKEY_GUNICORN_BIND", "127.0.0.1:8001")

# (2 x cores) + 1 is the usual starting point for a sync worker pool. Capped so a
# large host does not spawn more workers than PostgreSQL has connections for.
_suggested = multiprocessing.cpu_count() * 2 + 1
workers = int(os.environ.get("ZAKEY_GUNICORN_WORKERS", min(_suggested, 9)))

# Threads stay at 1: the sync worker is the predictable choice, and the ORM code
# here is not written to be thread-safe beyond Django's own guarantees.
threads = 1
worker_class = "sync"

# Longer than the slowest legitimate request (order creation under contention),
# short enough that a wedged worker is recycled rather than tying up a slot.
timeout = 60
graceful_timeout = 30

# Recycle workers periodically so a slow leak cannot accumulate indefinitely.
# The jitter prevents every worker restarting in the same instant.
max_requests = 1000
max_requests_jitter = 100

# Log to stdout/stderr so the service manager owns log routing; the application's
# own RedactingFilter has already scrubbed the records (FR-007, NFR-012).
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("ZAKEY_GUNICORN_LOGLEVEL", "info")

# Do not log query strings or cookies. A query string can carry a `next=` target
# or a token, and an access log is the least protected file on the host.
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(M)sms'

proc_name = "zakey-web"
forwarded_allow_ips = "127.0.0.1"
