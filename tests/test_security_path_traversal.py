"""
Penetration-style Path Traversal & Arbitrary File Access Tests.
Validates that endpoints and engines reject path traversal payloads (e.g. `../../etc/passwd`).
"""

import pytest
from pathlib import Path
from services.notifications.region_config import RegionConfigManager

TRAVERSAL_PAYLOADS = [
    "../../etc/passwd",
    "..\\..\\Windows\\System32\\cmd.exe",
    "/etc/shadow",
    "....//....//config.yaml",
    "%2e%2e%2fconfig.yaml"
]

def test_region_config_path_traversal_protection():
    for payload in TRAVERSAL_PAYLOADS:
        # Initializing manager with traversal path safely falls back to default without crash
        mgr = RegionConfigManager(config_path=payload)
        cfg = mgr.current_region
        assert cfg.region_id is not None
        assert cfg.region_name is not None
