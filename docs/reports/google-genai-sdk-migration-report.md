# Google GenAI SDK Migration Report

## Scope

Migrate AlgoFlow's live Gemini classification and hint invokers away from the deprecated `google.generativeai` package to the current `google.genai` SDK surface.

## Before

- Gemini classification and hint invokers imported `google.generativeai`.
- Local runs emitted a deprecation warning stating that support for `google.generativeai` has ended.
- The deprecated SDK also contributed to noisy test output when local `.env` enabled Gemini.

## After

- Classification invoker uses `from google import genai` and `from google.genai import types`.
- Hint invoker uses the same current SDK surface.
- Calls now use `client.models.generate_content(...)` with `types.GenerateContentConfig`.
- Existing timeout, structured JSON parsing, validation, and deterministic fallback behavior are preserved.
- No deprecated `google.generativeai` references remain in application or test code.

## Verification

Focused Gemini tests:

```text
20 passed
```

Full backend tests:

```text
123 passed, 5 warnings
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

- CI tests still use fake invokers and do not call the live Gemini API.
- This migration removes deprecated SDK usage, but live API timeout behavior can still depend on network, key validity, model availability, and request size.
