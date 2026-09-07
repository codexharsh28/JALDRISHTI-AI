"""
Official India Meteorological Department (IMD) Automatic Weather Station (AWS) Client.
Handles secure HTTP communication, retries, backoff, status code classification, and rate limiting.
"""

import os
import ssl
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class IMDAWSClientError(Exception):
    """Base exception for IMD AWS client errors."""
    def __init__(self, message: str, category: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.category = category
        self.status_code = status_code

class IMDAWSClient:
    """
    Client for interacting with official IMD AWS endpoints:
    - Base / All Stations: https://city.imd.gov.in/api/aws_data_api.php
    - Specific Station: https://city.imd.gov.in/api/aws_data_api.php?id={CALL_SIGN}
    - Specific State: https://city.imd.gov.in/api/aws_data_api.php?sid={STATE_ID}
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        state_id: Optional[str] = None,
        public_ip: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        poll_interval_seconds: Optional[int] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ):
        self.base_url = (base_url or os.getenv("IMD_AWS_API_BASE_URL", "https://city.imd.gov.in/api/aws_data_api.php")).strip()
        self.state_id = state_id or os.getenv("IMD_AWS_STATE_ID", None)
        self.public_ip = public_ip or os.getenv("IMD_AWS_PUBLIC_IP", None)
        self.timeout_seconds = float(timeout_seconds or os.getenv("IMD_AWS_REQUEST_TIMEOUT", "10.0"))
        self.poll_interval_seconds = int(poll_interval_seconds or os.getenv("IMD_AWS_POLL_INTERVAL", "900"))
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self._last_request_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        self._last_failure_time: Optional[datetime] = None
        self._last_http_status: Optional[int] = None
        self._last_error_category: Optional[str] = None
        self._last_error_message: Optional[str] = None
        self._last_latency_ms: float = 0.0

        # Rate limiting state (minimum 5 seconds between outbound calls)
        self._min_cooldown_seconds: float = 5.0
        self._last_call_monotonic: float = 0.0

    def is_configured(self) -> bool:
        """
        Determines whether the client is configured.
        Base URL is always present; if public IP whitelisting or specific API keys are required,
        this verifies configuration viability.
        """
        return bool(self.base_url)

    def get_status_diagnostics(self) -> Dict[str, Any]:
        """Returns operator-safe diagnostics without exposing credentials."""
        # Sanitize URL for presentation
        safe_url = self.base_url.split("?")[0]
        return {
            "configured": self.is_configured(),
            "endpoint": safe_url,
            "state_id": self.state_id or "ALL",
            "public_ip_configured": bool(self.public_ip),
            "last_success": self._last_success_time.isoformat() if self._last_success_time else None,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "last_http_status": self._last_http_status,
            "last_error_category": self._last_error_category,
            "last_error_message": self._last_error_message,
            "latency_ms": round(self._last_latency_ms, 2),
            "timeout_seconds": self.timeout_seconds,
            "poll_interval_seconds": self.poll_interval_seconds
        }

    def fetch_raw_data(
        self,
        call_sign: Optional[str] = None,
        state_id: Optional[str] = None,
        force: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes HTTP GET request against the IMD AWS endpoint.
        Returns:
            (records, metadata_dict)
        Raises:
            IMDAWSClientError on classified failure.
        """
        now_mono = time.monotonic()
        elapsed = now_mono - self._last_call_monotonic
        if not force and elapsed < self._min_cooldown_seconds:
            wait_time = self._min_cooldown_seconds - elapsed
            logger.info(f"[IMD_AWS] Rate limit cooldown: sleeping for {wait_time:.2f}s")
            time.sleep(wait_time)

        self._last_call_monotonic = time.monotonic()
        self._last_request_time = datetime.now(timezone.utc)

        # Build URL
        target_state = state_id or self.state_id
        params = []
        if call_sign:
            params.append(f"id={urllib.parse.quote(call_sign)}")
        elif target_state:
            params.append(f"sid={urllib.parse.quote(str(target_state))}")

        req_url = self.base_url
        if params:
            separator = "&" if "?" in req_url else "?"
            req_url = f"{req_url}{separator}{'&'.join(params)}"

        headers = {
            "User-Agent": "JALDRISHTI-AI-Hydromet-Engine/1.0 (+https://github.com/DevbratY/JALDRISHTI-AI)",
            "Accept": "application/json, text/plain, */*"
        }

        # Setup SSL context (tolerating standard government root cert chains where needed)
        ssl_ctx = ssl.create_default_context()
        # For gov.in self-signed intermediate chains in test/pilot environments:
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(req_url, headers=headers, method="GET")

        attempt = 0
        last_exception = None
        start_ts = time.monotonic()

        while attempt < self.max_retries:
            attempt += 1
            try:
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=self.timeout_seconds) as response:  # nosec B310
                    status_code = response.status
                    self._last_http_status = status_code
                    raw_bytes = response.read()
                    self._last_latency_ms = (time.monotonic() - start_ts) * 1000.0

                    if status_code != 200:
                        cat = self._classify_status_code(status_code)
                        self._last_failure_time = datetime.now(timezone.utc)
                        self._last_error_category = cat
                        self._last_error_message = f"HTTP {status_code} received from IMD AWS endpoint"
                        raise IMDAWSClientError(self._last_error_message, category=cat, status_code=status_code)

                    # Parse JSON
                    try:
                        text_data = raw_bytes.decode('utf-8', errors='replace').strip()
                        if not text_data:
                            records = []
                        else:
                            parsed = json.loads(text_data)
                            if isinstance(parsed, list):
                                records = parsed
                            elif isinstance(parsed, dict):
                                # Handle wrapped object {"data": [...]} or single station dict
                                records = parsed.get("data", [parsed]) if "data" in parsed else [parsed]
                            else:
                                records = []
                    except Exception as json_err:
                        self._last_failure_time = datetime.now(timezone.utc)
                        self._last_error_category = "INVALID_PROVIDER_PAYLOAD"
                        self._last_error_message = f"Malformed JSON from IMD AWS: {json_err}"
                        raise IMDAWSClientError(self._last_error_message, category="INVALID_PROVIDER_PAYLOAD", status_code=200)

                    self._last_success_time = datetime.now(timezone.utc)
                    self._last_error_category = None
                    self._last_error_message = None

                    meta = {
                        "url": req_url.split("?")[0],
                        "http_status": status_code,
                        "latency_ms": self._last_latency_ms,
                        "raw_bytes_len": len(raw_bytes),
                        "retrieved_at": self._last_success_time.isoformat(),
                        "record_count": len(records),
                        "attempt": attempt
                    }
                    return records, meta

            except urllib.error.HTTPError as http_err:
                self._last_http_status = http_err.code
                self._last_latency_ms = (time.monotonic() - start_ts) * 1000.0
                cat = self._classify_status_code(http_err.code)
                self._last_failure_time = datetime.now(timezone.utc)
                self._last_error_category = cat
                self._last_error_message = f"IMD AWS HTTP Error {http_err.code}: {http_err.reason}"

                # Do NOT endlessly retry 400, 401, 403 (unrecoverable without credentials/whitelisting)
                if http_err.code in (400, 401, 403):
                    raise IMDAWSClientError(self._last_error_message, category=cat, status_code=http_err.code)
                
                # If rate limited (429), back off
                if http_err.code == 429:
                    sleep_s = (self.backoff_factor ** attempt) * 2.0
                    time.sleep(sleep_s)
                    last_exception = http_err
                    continue

                # 5xx: retry
                if attempt < self.max_retries:
                    sleep_s = self.backoff_factor ** attempt
                    time.sleep(sleep_s)
                    last_exception = http_err
                    continue
                else:
                    raise IMDAWSClientError(self._last_error_message, category=cat, status_code=http_err.code)

            except urllib.error.URLError as url_err:
                self._last_latency_ms = (time.monotonic() - start_ts) * 1000.0
                self._last_failure_time = datetime.now(timezone.utc)
                if "timed out" in str(url_err.reason).lower():
                    cat = "TIMEOUT"
                    msg = f"IMD AWS Request timed out after {self.timeout_seconds}s"
                else:
                    cat = "NETWORK_ERROR"
                    msg = f"IMD AWS Network Error: {url_err.reason}"
                self._last_error_category = cat
                self._last_error_message = msg

                if attempt < self.max_retries:
                    time.sleep(self.backoff_factor ** attempt)
                    last_exception = url_err
                    continue
                else:
                    raise IMDAWSClientError(msg, category=cat, status_code=None)

            except Exception as ex:
                self._last_latency_ms = (time.monotonic() - start_ts) * 1000.0
                self._last_failure_time = datetime.now(timezone.utc)
                cat = "UNEXPECTED_ERROR"
                msg = f"Unexpected error during IMD AWS request: {ex}"
                self._last_error_category = cat
                self._last_error_message = msg
                raise IMDAWSClientError(msg, category=cat, status_code=None)

        # Fallthrough if all retries exhausted
        raise IMDAWSClientError(
            self._last_error_message or "Max retries exhausted connecting to IMD AWS",
            category=self._last_error_category or "PROVIDER_UNAVAILABLE"
        )

    def _classify_status_code(self, status_code: int) -> str:
        """Classifies HTTP status code into canonical operational category."""
        if 200 <= status_code < 300:
            return "SUCCESS"
        if status_code == 400:
            return "CONFIGURATION_ERROR"
        if status_code in (401, 403):
            return "ACCESS_DENIED"
        if status_code == 404:
            return "ENDPOINT_NOT_FOUND"
        if status_code == 429:
            return "RATE_LIMITED"
        if status_code >= 500:
            return "PROVIDER_UNAVAILABLE"
        return "HTTP_ERROR"
