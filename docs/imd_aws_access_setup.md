# IMD AWS Access & Whitelisting Setup Guide

## Official Endpoint Overview

The official IMD Automatic Weather Station (AWS) / Automatic Rain Gauge (ARG) API is hosted by the India Meteorological Department at:

```
https://city.imd.gov.in/api/aws_data_api.php
```

### URL Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | String | Optional | Filter by station call sign (e.g. `42971` for Bhubaneswar) |
| `sid` | String | Optional | Filter by State ID or State Name (e.g. `ODISHA`) |

---

## IP Whitelisting Requirement

The official IMD AWS API is protected by government gateway access control policies. Requests originating from non-whitelisted IP addresses return `HTTP 401: Unauthorized` or `HTTP 403: Forbidden`.

### How to Request Whitelisting:
1. Submit an official request to the **India Meteorological Department (IMD) Numerical Weather Prediction & Observations Division**.
2. Specify the static public egress IP address of your JALDRISHTI deployment node.
3. State the operational purpose (Disaster Management, Early Warning & Flood Nowcasting).

---

## Environment Variable Configuration

Configure the following variables in your deployment environment or `.env`:

```env
# IMD AWS Integration Configuration
IMD_AWS_BASE_URL=https://city.imd.gov.in/api/aws_data_api.php
IMD_AWS_STATE_ID=ODISHA
IMD_AWS_PUBLIC_IP=203.0.113.10
IMD_AWS_TIMEOUT_SECONDS=10.0
IMD_AWS_POLL_INTERVAL_MINUTES=15
```

---

## Testing & Verification

Run the diagnostics endpoint:
```bash
curl -X GET http://localhost:8000/api/v1/live/imd-aws/status
```

Trigger an on-demand manual ingestion cycle:
```bash
curl -X POST http://localhost:8000/api/v1/live/imd-aws/refresh?force=true
```
