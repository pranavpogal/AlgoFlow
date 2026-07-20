# Gemini Diagnostics Observability Report

## Scope

Improve Gemini failure visibility after users reported that fresh Google AI Studio keys still produced deterministic fallback results.

## Before

- Gemini API failures fell back safely after the previous fix.
- Fallback reasons could still be too vague, for example `gemini_classification_failed:ClientError`.
- There was no lightweight backend route to verify whether the active `.env` key/model could reach Gemini.
- Debugging required reading terminal stack traces.

## After

- Gemini classification and hint fallback reasons now include sanitized exception message text.
- API-key-looking values are redacted from errors before returning them.
- Added `GET /api/v1/diagnostics/gemini` to run a tiny Gemini JSON probe.
- The diagnostic response reports:
  - whether a key is configured
  - model name
  - whether Gemini classification/hints are enabled
  - ok/status
  - sanitized error type/status/message
  - latency

## How To Use

With backend running, open:

```text
http://localhost:8000/api/v1/diagnostics/gemini
```

or run:

```bash
curl http://localhost:8000/api/v1/diagnostics/gemini
```

Expected success shape:

```json
{
  "key_configured": true,
  "model": "gemini-2.5-flash",
  "classification_enabled": true,
  "hints_enabled": true,
  "ok": true,
  "status": "ok"
}
```

If Google still rejects the key/project, the endpoint should now show a sanitized error message instead of requiring a terminal traceback.

## Verification

Focused Gemini diagnostics/adjudicator tests:

```text
14 passed
```

Full backend tests:

```text
128 passed, 5 warnings
```

Lint:

```text
All checks passed!
```

Accepted deterministic baseline comparison:

```text
status: pass
exit_code: 0
caseset_drift: none
blocking_regressions: none
```

## Known Limitations

- The diagnostic endpoint can confirm the active key/model behavior, but it cannot fix a Google-side project denial.
- If the endpoint returns a Google `PERMISSION_DENIED` or access-restricted message, the key/project/account must be corrected in Google AI Studio or Google Cloud.
