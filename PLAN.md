# Implementation Plan -- Audit Remediation (2026-03-19)

Based on the comprehensive audit at `analysis/comprehensive_audit_20260319.md`.
All file paths are relative to the repository root `/Users/wells/Projects/tychons`.

---

## Wave 1 -- Security and Input Validation (no interdependencies within wave)

### Task 1.1 -- Sanitize `lang` parameter against path traversal [C1]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Critical
- **Files:** `src/tychons/tychons.py` (lines 106-108, 149-190)
- **What to change:**
  1. Add a validation function `_validate_lang(lang: str) -> None` that raises `ValueError` if `lang` does not match the regex `^[a-zA-Z0-9_-]+$`. Place it near `_lang_to_filename()` (around line 106).
  2. Call `_validate_lang(lang)` at the top of `load_wordlist()` (line 149), before any path construction.
  3. Also call it in `_resolve_wordlist()` (line 193) when `lang is not None`, as a defense-in-depth measure.
- **Acceptance criteria:**
  - `Badge("key", lang="en")` works normally.
  - `Badge("key", lang="../../etc/passwd")` raises `ValueError` with a message mentioning invalid characters.
  - `Badge("key", lang="../foo")` raises `ValueError`.
  - `Badge("key", lang="zh-hans")` works (hyphens are allowed).
  - `Badge("key", lang="chinese_simplified")` works (underscores are allowed).
  - A new test in `tests/test_validation.py` covers all of the above cases.

### Task 1.2 -- Validate `bg_color` parameter [H1]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** High
- **Files:** `src/tychons/tychons.py` (lines 656-677)
- **What to change:**
  1. In `Badge.__init__()`, after the `size` validation block (line 671), add validation for `bg_color`:
     - Must be a `tuple` (not list, not other iterable).
     - Must have exactly 3 elements.
     - Each element must be an `int` in range `[0, 255]`.
     - Raise `ValueError` with a descriptive message on failure.
- **Acceptance criteria:**
  - `Badge("key", bg_color=(8, 13, 20))` works (default).
  - `Badge("key", bg_color=(0, 0, 0))` works.
  - `Badge("key", bg_color=(255, 255, 255))` works.
  - `Badge("key", bg_color=(256, 0, 0))` raises `ValueError`.
  - `Badge("key", bg_color=(-1, 0, 0))` raises `ValueError`.
  - `Badge("key", bg_color=(0, 0))` raises `ValueError` (wrong length).
  - `Badge("key", bg_color=[8, 13, 20])` raises `ValueError` (wrong type).
  - `Badge("key", bg_color=(8.0, 13, 20))` raises `ValueError` (float element).
  - New tests in `tests/test_validation.py` cover all of the above cases.

---

## Wave 2 -- Code Quality Fixes (no interdependencies within wave)

### Task 2.1 -- Swap HMAC-SHA256 key/message ordering [H2]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Medium
- **Files:** `src/tychons/tychons.py` (lines 209-218)
- **What to change:**
  1. In the `_derive()` HMAC fallback, swap the arguments so the input key material (`key + counter`) is the HMAC key and the context string is the message:
     ```
     hmac.new(key + counter.to_bytes(4, "big"), context.encode(), hashlib.sha256).digest()
     ```
  2. Update the inline comment on line 210 from `"context as the salt"` to `"key material as HMAC key, context as message (HKDF-like pattern)"`.
- **Note:** This is a breaking change for any user relying on the HMAC fallback. Since the fallback is documented as non-interoperable and no test vectors exist for it, this is acceptable. The HMAC fallback path should be tested (see Task 3.2).
- **Acceptance criteria:**
  - The HMAC key is `key + counter.to_bytes(4, "big")`.
  - The HMAC message is `context.encode()`.
  - The fallback still produces 32+ bytes when `length > 32` (counter extension works).
  - Tests from Task 3.2 pass.

### Task 2.2 -- Remove unused `cjk` variable in `_render()` [M5]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Low
- **Files:** `src/tychons/tychons.py` (line 474)
- **What to change:**
  1. Remove the line `cjk = _is_cjk(lang)` from `_render()` at line 474. It is computed but never referenced in the PNG rendering path.
- **Acceptance criteria:**
  - Line `cjk = _is_cjk(lang)` no longer exists in `_render()`.
  - No `NameError` or behavioral change in any existing test.
  - `_is_cjk(lang)` is still called in `_render_svg()` (line 532) -- that is correct and must remain.

### Task 2.3 -- Catch `FileNotFoundError` in CLI `main()` [M6]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Low
- **Files:** `src/tychons/tychons.py` (lines 757-761)
- **What to change:**
  1. Expand the `except` clause on line 759 from `except ValueError as exc` to `except (ValueError, FileNotFoundError) as exc`.
- **Acceptance criteria:**
  - Running the CLI with an invalid `lang` value (e.g., `tychons "key" badge.svg 128 nonexistent_lang`) prints a clean error message starting with `"Error:"` and exits with code 1, rather than an unhandled traceback.

### Task 2.4 -- Rename ambiguous parameter `l` to `lightness` in `_hsl_to_rgb` [L7]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Informational
- **Files:** `src/tychons/tychons.py` (lines 368-379)
- **What to change:**
  1. Rename the parameter `l` to `lightness` in the function signature and all references within `_hsl_to_rgb`.
  2. There are 3 occurrences of `l` in the function body (lines 370, 372) that must be updated.
- **Acceptance criteria:**
  - `_hsl_to_rgb` signature reads `def _hsl_to_rgb(h: int, s: float, lightness: float)`.
  - No reference to bare `l` remains in the function body.
  - All existing tests pass unchanged.

### Task 2.5 -- Add `py.typed` marker [L3]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Informational
- **Files:** `src/tychons/py.typed` (new file)
- **What to change:**
  1. Create an empty file at `src/tychons/py.typed`.
- **Acceptance criteria:**
  - File `src/tychons/py.typed` exists and is empty.

### Task 2.6 -- Export `__version__` from package [L1]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Informational
- **Files:** `src/tychons/__init__.py`
- **What to change:**
  1. Add `__version__ = "0.1.0"` to `src/tychons/__init__.py`.
  2. Add `"__version__"` to the `__all__` list.
- **Acceptance criteria:**
  - `from tychons import __version__; assert __version__ == "0.1.0"` succeeds.

---

## Wave 3 -- Tests (depends on Wave 1 and Wave 2)

### Task 3.1 -- Add regression test vectors for the spec sample key
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Medium (addresses M1 and L6)
- **Files:** `tests/test_derivation.py`, `tests/conftest.py`
- **What to change:**
  1. Write a script or use the REPL to compute the concrete derived values for key `b"ssh-rsa AAAAB3NzaC1yc2E"` with BLAKE3:
     - `_derive_hue(key)` -- record the exact integer (0-359).
     - `_derive_stars(key, 128)` -- record the star count.
     - `_derive_words(key, _FALLBACK_WORDLIST)` -- record the exact two words.
  2. Add a test `test_spec_test_vector_values()` in `tests/test_derivation.py` that asserts these exact values.
  3. These values will also be used for Task 4.1 (spec update).
- **Acceptance criteria:**
  - The test asserts specific expected values for hue, star count, word1, and word2.
  - The test passes with the current BLAKE3-based derivation.
  - If anyone changes byte ordering or context strings, this test breaks.

### Task 3.2 -- Add HMAC-SHA256 fallback tests [M3]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Medium
- **Files:** `tests/test_derivation.py`
- **What to change:**
  1. Add a test `test_hmac_fallback_derive()` that patches `tychons.tychons.HAS_BLAKE3 = False` (using `unittest.mock.patch`) and verifies:
     - `_derive(key, context, length=32)` returns exactly 32 bytes.
     - `_derive(key, context, length=64)` returns exactly 64 bytes (counter extension).
     - Output is deterministic (same inputs produce same output).
     - Output differs from the BLAKE3 path (i.e., fallback is not accidentally using BLAKE3).
  2. Add a test `test_hmac_fallback_badge()` that patches `HAS_BLAKE3 = False` and creates a full `Badge`, verifying it produces valid SVG without error.
- **Acceptance criteria:**
  - Tests exercise the `else` branch in `_derive()`.
  - Tests pass after the key/message swap from Task 2.1.
  - Tests verify correct output length for both 32-byte and 64-byte requests.

### Task 3.3 -- Add `lang` path traversal security tests [C1]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Critical
- **Files:** `tests/test_validation.py`
- **What to change:**
  1. Add tests for the `lang` validation introduced in Task 1.1:
     - `test_lang_path_traversal_dot_dot` -- `lang="../../etc/passwd"` raises `ValueError`.
     - `test_lang_path_traversal_slash` -- `lang="foo/bar"` raises `ValueError`.
     - `test_lang_null_byte` -- `lang="en\x00"` raises `ValueError`.
     - `test_lang_valid_codes` -- `lang="en"`, `"zh-hans"`, `"chinese_simplified"` do not raise `ValueError` (they may raise `FileNotFoundError` if no wordlist file exists, which is acceptable).
- **Acceptance criteria:**
  - All traversal attempts raise `ValueError` before any filesystem access.
  - Valid lang codes pass the validation step.

### Task 3.4 -- Add `bg_color` validation tests [H1]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** High
- **Files:** `tests/test_validation.py`
- **What to change:**
  1. Add tests for the `bg_color` validation introduced in Task 1.2 (see acceptance criteria in Task 1.2 for the full set of cases).
- **Acceptance criteria:**
  - Invalid `bg_color` values raise `ValueError` at construction time.
  - Valid `bg_color` values are accepted.

---

## Wave 4 -- Documentation Updates (depends on Wave 1, 2, and 3)

### Task 4.1 -- Populate spec test vectors [M1]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Medium
- **Files:** `docs/src/tychons-spec-v0.1.0.md` (lines 350-356)
- **What to change:**
  1. Replace the placeholder text in Appendix A with the concrete values computed in Task 3.1:
     ```
     Input:  "ssh-rsa AAAAB3NzaC1yc2E"
     Hue:    <exact integer>
     Stars:  <exact count>
     Word 1: <exact word from fallback list>
     Word 2: <exact word from fallback list>
     ```
  2. Remove the line `"Test vectors will be populated upon publication of the reference implementation."` (line 358).
- **Acceptance criteria:**
  - All four placeholder values are replaced with concrete values.
  - Values match the assertions in the test from Task 3.1.

### Task 4.2 -- Update `technical-reference.md` layout formulas [H3]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Medium
- **Files:** `docs/technical-reference.md` (lines 82-101, 163-172)
- **What to change:**
  1. **Lines 86-88 (star radius):** Replace `1.5 + scalar * 3.0` with `size * 0.012 + scalar * (size * 0.035 - size * 0.012)`. At size=128 this yields `[1.536, 4.48]`.
  2. **Lines 92-101 (layout constants):** Replace the `pad / inner_width / label_reserve` block with the 10-division grid model:
     ```
     div = size / 10
     pad = div                         (1 division)
     star zone x: [div, 9*div]         (8 divisions wide)
     star zone y: [div, 6.5*div]       (5.5 divisions tall, from top)
     label zone y: [6.5*div, 9*div]    (2.5 divisions tall)
     ```
  3. **Line 167 (edge width):** Replace `~ 0.6px at size=128` with `size * 0.008` (= `1.024px at size=128`).
  4. **Line 170 (font size):** Replace `~8.5pt at size=128` with `label_h * 0.60 / 1.20` which at size=128 yields `~16px`. Document the formula.
  5. **Line 169 (gradient):** Replace `"bottom ~17%"` with `"label zone (bottom 25% of canvas)"`.
- **Acceptance criteria:**
  - All numeric values in the technical reference match the implementation in `tychons.py`.
  - The 10-division grid model is clearly described.
  - No references to the old `pad / inner_width / label_reserve` model remain.

### Task 4.3 -- Fix import path in docs [L4]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Informational
- **Files:** `README.md` (line 34), `docs/getting-started.md` (line 36)
- **What to change:**
  1. In `README.md` line 34, change `from tychons.tychons import Badge` to `from tychons import Badge`.
  2. In `docs/getting-started.md` line 36, change `from tychons.tychons import Badge` to `from tychons import Badge`.
- **Acceptance criteria:**
  - Both files use `from tychons import Badge`.
  - No other references to `tychons.tychons` remain in user-facing docs.

### Task 4.4 -- Fix CLI default output path in docs [M2]
- **Status:** [x] complete
- **Agent:** @developer
- **Severity:** Medium
- **Files:** `docs/getting-started.md` (lines 53-56, 62), `README.md` (line 44)
- **What to change:**
  1. In `docs/getting-started.md` line 54, change the CLI example output from `badge.png` to `badge.svg` to match the actual CLI default.
  2. In `docs/getting-started.md` line 62, update the default output column from `badge.png` to `badge.svg`.
  3. In `README.md` line 44, change the CLI example output from `badge.png` to `badge.svg`.
  4. Mention SVG as the default format in the getting-started description.
  5. Also add `badge.svg` and `badge.png` as table entries showing that both are supported and the format is inferred from the extension.
- **Acceptance criteria:**
  - CLI examples in docs show `.svg` as the default output.
  - The docs table shows `badge.svg` as the default, not `badge.png`.

---

## Parallelization Strategy

```
Wave 1: [Task 1.1, Task 1.2]               -- run in parallel, no dependencies
Wave 2: [Task 2.1, Task 2.2, Task 2.3,     -- run in parallel, no dependencies
          Task 2.4, Task 2.5, Task 2.6]        between tasks or on Wave 1
Wave 3: [Task 3.1, Task 3.2, Task 3.3,     -- depends on Wave 1 (1.1 -> 3.3,
          Task 3.4]                             1.2 -> 3.4) and Wave 2 (2.1 -> 3.2)
                                               Task 3.1 has no code dependency and
                                               can run in parallel with Wave 1/2
Wave 4: [Task 4.1, Task 4.2, Task 4.3,     -- depends on Wave 3 (3.1 -> 4.1)
          Task 4.4]                             Tasks 4.2, 4.3, 4.4 can run in
                                               parallel with each other anytime
                                               after Wave 2
```

Tasks 4.2, 4.3, and 4.4 have no code dependencies and could technically run in any wave, but are grouped in Wave 4 so that documentation is updated last, after the code it describes is finalized.

---

## Out of Scope (noted but not planned)

- **M4 (star index wrapping for >12 stars):** The current max is 10 stars; no code change needed. If the star count formula changes in the future, revisit.
- **L2 (save_svg extension validation):** By-design behavior, no change.
- **L5 (stale .state/PLAN.md):** This plan supersedes the old `.state/PLAN.md`.
