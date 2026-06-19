# Playwright Navigation Rules

- NEVER use `page.goto()` for external URLs — it throws `ERR_HTTP_RESPONSE_CODE_FAILURE` on gateway/proxy HTTP errors.
- Use `page.evaluate("window.location.href = '...'")` + `wait_for_selector(element, timeout)` instead — the JS navigation handles redirects and error responses silently.
- This applies to both headed and headless browser automation.
