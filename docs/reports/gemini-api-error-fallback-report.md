# Gemini API Error Fallback Report

## Scope

Fix a production-path failure where Google GenAI API errors escaped the Gemini adjudication boundary and caused `POST /api/v1/problems/analyze` to return HTTP 500.

## Observed Error

The live Gemini call reached Google and returned:

```text
google.genai.errors.ClientError: 403 PERMISSION_DENIED
Your project has been denied access. Please contact support.
```

## Before

- Gemini timeout, JSON parsing, validation, runtime, and value errors were handled.
- Google SDK `ClientError` was not caught by the fallback boundary.
- A denied API key/project could crash Analyze Problem with a 500 response.

## After

- Gemini classification catches SDK/API exceptions and falls back to deterministic classification.
- Gemini hints catch SDK/API exceptions and fall back to deterministic hints.
- Fallback reasons include status code when the exception exposes one, for example:

```text
gemini_classification_failed:ClientError:403
gemini_hint_failed:ClientError:403
```

## User Action Still Required

This code change prevents 500s, but it does not fix the Google account/project access problem. The API key or Google Cloud project must be corrected because Google is returning `PERMISSION_DENIED`.

Likely fixes:

- Generate a new Gemini API key from Google AI Studio.
- Ensure the key belongs to a project with Gemini API access.
- Check whether the key/project has restrictions blocking local use.
- Try a fresh key in `backend/.env`.
- Restart the backend after changing `.env`.

## Verification

Focused Gemini tests:

```text
11 passed
```

Full backend tests:

```text
125 passed, 5 warnings
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
