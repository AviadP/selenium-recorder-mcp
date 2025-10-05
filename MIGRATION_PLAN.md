# 🚀 Playwright Migration Plan

**Status:** In Progress
**Started:** 2025-10-05
**Estimated Completion:** 9.5 hours
**Current Phase:** Phase 0 - Preparation

---

## 📋 Executive Summary

### Migration Goals
- Replace unmaintained `pychrome` (last updated Jul 2023) with Microsoft-backed `playwright`
- Address security vulnerabilities identified in audit
- Implement cleaner, more maintainable API
- Ensure better long-term support and active maintenance

### Breaking Changes
- ⚠️ CDPRecorder constructor signature changes: `chrome_path` parameter removed
- ⚠️ `CHROME_PATH` environment variable no longer used
- ✅ Playwright auto-detects browser location
- ✅ New optional `HEADLESS` environment variable

### Benefits
- ✅ Microsoft-backed, enterprise-grade library
- ✅ Active development (v1.55.0, Aug 2025)
- ✅ Cleaner API with less boilerplate
- ✅ Better security posture with active patches
- ✅ Multi-browser support capability (future)
- ✅ Eliminates biggest dependency risk from security audit

---

## 📊 Phase Overview

| Phase | Duration | Risk | Status |
|-------|----------|------|--------|
| 0. Preparation & Setup | 30 min | LOW | 🔄 In Progress |
| 1. Dependency Management | 15 min | LOW | ⏸️ Pending |
| 2. Core CDPRecorder Migration | 4 hours | MEDIUM-HIGH | ⏸️ Pending |
| 3. Integration Updates | 30 min | MEDIUM | ⏸️ Pending |
| 4. Testing & Validation | 1.5 hours | LOW | ⏸️ Pending |
| 5. Security Hardening | 2 hours | LOW | ⏸️ Pending |
| 6. Documentation Updates | 45 min | NONE | ⏸️ Pending |
| 7. Final Validation | 30 min | LOW | ⏸️ Pending |
| 8. Deployment & Cleanup | 20 min | LOW | ⏸️ Pending |

**Total Estimated Time:** 9.5 hours

---

## 📋 PHASE 0: PREPARATION & SETUP
**Duration: 30 minutes | Risk: LOW | Status: 🔄 In Progress**

### Task 0.1: Create Migration Branch ✅
- **Status:** ✅ Complete
- **Risk:** LOW
- **Effort:** 2 minutes
- **Command:** `git checkout -b migrate-to-playwright`
- **Rollback:** `git checkout master`

### Task 0.2: Install Playwright
- **Status:** ⏸️ Pending
- **Risk:** LOW
- **Effort:** 5 minutes
- **Steps:**
  1. Install playwright: `pip install playwright`
  2. Install chromium: `playwright install chromium`
- **Validation:** `playwright --version` shows version

### Task 0.3: Create Backup Reference
- **Status:** ⏸️ Pending
- **Risk:** NONE
- **Effort:** 1 minute
- **Command:** `cp src/cdp_recorder.py src/cdp_recorder.py.backup`
- **Purpose:** Side-by-side comparison during migration

### Task 0.4: Research Playwright API
- **Status:** ✅ Complete (done during planning)
- **Risk:** NONE
- **Effort:** 15 minutes
- **Key Findings:**
  - `page.on("console")` for console events
  - `page.on("pageerror")` for JS errors
  - `page.context.new_cdp_session()` for CDP access
  - `page.expose_binding()` for click tracking

### Task 0.5: Create Migration Tracking Document
- **Status:** 🔄 In Progress (this file)
- **Risk:** NONE
- **Effort:** 5 minutes
- **File:** `MIGRATION_PLAN.md`

---

## 📦 PHASE 1: DEPENDENCY MANAGEMENT
**Duration: 15 minutes | Risk: LOW | Status: ⏸️ Pending**

### Task 1.1: Update pyproject.toml
- **File:** `pyproject.toml`
- **Lines:** 6-10
- **Risk:** LOW
- **Effort:** 3 minutes
- **Changes:**
  ```toml
  dependencies = [
      "mcp==0.9.0",          # Pin exact version
      "playwright==1.55.0",  # Replace pychrome
  ]
  ```
- **Remove:** `pychrome>=0.2.4`, `websocket-client>=1.6.0`

### Task 1.2: Install Dependencies
- **Risk:** LOW
- **Effort:** 5 minutes
- **Commands:**
  ```bash
  pip uninstall -y pychrome websocket-client
  pip install -e .
  playwright install chromium
  ```

### Task 1.3: Verify Installation
- **Risk:** NONE
- **Effort:** 2 minutes
- **Test:**
  ```bash
  python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright ready')"
  ```

### Task 1.4: Update .gitignore
- **Risk:** NONE
- **Effort:** 1 minute
- **Add:**
  ```
  # Playwright
  .playwright/
  playwright-state/
  ```

---

## 🔧 PHASE 2: CORE MIGRATION - CDPRecorder
**Duration: 4 hours | Risk: MEDIUM-HIGH | Status: ⏸️ Pending**

### Task 2.1: Update Imports
- **File:** `src/cdp_recorder.py`
- **Lines:** 1-9
- **Risk:** LOW
- **Effort:** 5 minutes
- **Changes:**
  ```python
  # REMOVE:
  import pychrome

  # ADD:
  from playwright.sync_api import sync_playwright, Browser, Page, CDPSession
  ```

### Task 2.2: Refactor `__init__()` Method
- **Lines:** 15-35
- **Risk:** MEDIUM (breaking change)
- **Effort:** 15 minutes
- **Old Signature:**
  ```python
  def __init__(self, chrome_path: str = "...", debug_port: int = 9222)
  ```
- **New Signature:**
  ```python
  def __init__(self, headless: bool = False)
  ```
- **New Attributes:**
  ```python
  self.headless = headless
  self.playwright = None
  self.browser: Optional[Browser] = None
  self.page: Optional[Page] = None
  self.cdp_session: Optional[CDPSession] = None
  # Keep: session_id, events, start_time, event_callback
  ```
- **⚠️ Impact:** Must update `server.py` and `record.py`

### Task 2.3: Refactor `start_chrome()` Method
- **Lines:** 37-67
- **Risk:** MEDIUM
- **Effort:** 20 minutes
- **New Implementation:**
  ```python
  def start_chrome(self, url: Optional[str] = None) -> None:
      """Launch browser with playwright."""
      if self.browser:
          return

      # URL validation (SECURITY FIX #1)
      if url:
          from urllib.parse import urlparse
          parsed = urlparse(url)
          if parsed.scheme and parsed.scheme not in ('http', 'https'):
              raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

      self.playwright = sync_playwright().start()
      self.browser = self.playwright.chromium.launch(
          headless=self.headless,
          args=['--no-first-run', '--no-default-browser-check']
      )
      self.page = self.browser.new_page()

      if url:
          self.page.goto(url)
  ```
- **Removes:** subprocess logic, debug port, temp profile
- **Adds:** URL validation for security

### Task 2.4: Refactor `connect()` Method
- **Lines:** 69-93
- **Risk:** MEDIUM
- **Effort:** 20 minutes
- **New Implementation:**
  ```python
  def connect(self) -> str:
      """Setup event recording on existing page."""
      if not self.page:
          raise RuntimeError("Browser not started. Call start_chrome() first.")

      self.session_id = str(uuid.uuid4())
      self.start_time = datetime.now()
      self.events = []

      # Create CDP session for DOM events
      self.cdp_session = self.page.context.new_cdp_session(self.page)

      self._enable_domains()
      self._setup_event_listeners()

      return self.session_id
  ```

### Task 2.5: Refactor `_enable_domains()` Method
- **Lines:** 95-103
- **Risk:** LOW
- **Effort:** 10 minutes
- **New Implementation:**
  ```python
  def _enable_domains(self) -> None:
      """Enable CDP domains for event capture."""
      # Only enable CDP domains (DOM)
      # High-level events (console, errors) don't need enabling
      self.cdp_session.send("DOM.enable")

      # Add binding for click tracking
      self.page.expose_binding("recordClick", self._handle_click_binding)
  ```

### Task 2.6a: Setup High-Level Page Events
- **Lines:** 105-116
- **Risk:** MEDIUM-HIGH
- **Effort:** 12 minutes
- **Add to `_setup_event_listeners()`:**
  ```python
  def _setup_event_listeners(self) -> None:
      """Set up event listeners for recording."""
      # High-level playwright events
      self.page.on("console", self._on_console_log)
      self.page.on("pageerror", self._on_js_error)
      self.page.on("load", self._on_page_load)
  ```
- **⚠️ CHECKPOINT:** Test console events work before continuing

### Task 2.6b: Setup CDP Event Listeners
- **Risk:** MEDIUM
- **Effort:** 10 minutes
- **Add to `_setup_event_listeners()`:**
  ```python
      # CDP events for DOM mutations
      self.cdp_session.on("DOM.documentUpdated", self._on_document_updated)
      self.cdp_session.on("DOM.setChildNodes", self._on_set_child_nodes)
      self.cdp_session.on("DOM.attributeModified", self._on_attribute_modified)
      self.cdp_session.on("DOM.characterDataModified", self._on_character_data_modified)
  ```

### Task 2.6c: Inject Click Tracker
- **Risk:** LOW
- **Effort:** 3 minutes
- **Add to `_setup_event_listeners()`:**
  ```python
      # Inject click tracking script
      self._inject_click_tracker()
  ```

### Task 2.7: Migrate `_on_console_log()` Handler
- **Lines:** 136-141
- **Risk:** LOW
- **Effort:** 10 minutes
- **New Implementation:**
  ```python
  def _on_console_log(self, msg) -> None:
      """Handle console.log events."""
      self._add_event("console_log", {
          "level": msg.type,
          "args": [arg.json_value() for arg in msg.args],
          "location": {
              "url": msg.location.get("url", ""),
              "lineNumber": msg.location.get("lineNumber", 0)
          }
      })
  ```

### Task 2.8: Migrate `_on_js_error()` Handler
- **Lines:** 143-149
- **Risk:** LOW
- **Effort:** 10 minutes
- **New Implementation:**
  ```python
  def _on_js_error(self, error) -> None:
      """Handle JavaScript error events."""
      self._add_event("js_error", {
          "message": str(error),
          "stack": error.stack if hasattr(error, 'stack') else ""
      })
  ```

### Task 2.9: Add `_on_page_load()` Handler
- **Risk:** LOW
- **Effort:** 8 minutes
- **New Method:**
  ```python
  def _on_page_load(self) -> None:
      """Handle page load - reinject click tracker."""
      self._inject_click_tracker()
  ```

### Task 2.10: Migrate Click Binding Handler
- **Lines:** 181-193
- **Risk:** MEDIUM
- **Effort:** 15 minutes
- **New Implementation:**
  ```python
  def _handle_click_binding(self, source, data: str) -> None:
      """Handle click binding calls from browser."""
      import json
      try:
          click_data = json.loads(data)
          self._add_event("click", click_data)
      except json.JSONDecodeError:
          pass
  ```
- **Note:** Playwright binding signature differs from pychrome

### Task 2.11: Refactor `_inject_click_tracker()` Method
- **Lines:** 195-294
- **Risk:** MEDIUM
- **Effort:** 15 minutes
- **Change:**
  ```python
  def _inject_click_tracker(self) -> None:
      """Inject JavaScript to track click events."""
      script = """
      /* ... KEEP ALL EXISTING JAVASCRIPT ... */
      """

      try:
          self.page.evaluate(script)  # Changed from tab.Runtime.evaluate
      except Exception as e:
          print(f"Failed to inject click tracker: {e}")
  ```
- **JavaScript:** No changes needed

### Task 2.12: Update DOM Event Handlers
- **Lines:** 151-179
- **Risk:** LOW
- **Effort:** 10 minutes
- **Changes:**
  - `_on_document_updated()` - Remove click reinject (moved to `_on_page_load`)
  - `_on_set_child_nodes()` - Keep as-is
  - `_on_attribute_modified()` - Keep as-is
  - `_on_character_data_modified()` - Keep as-is

### Task 2.13: Refactor `close()` Method
- **Lines:** 333-341
- **Risk:** MEDIUM
- **Effort:** 15 minutes
- **New Implementation:**
  ```python
  def close(self) -> None:
      """Close browser and cleanup resources."""
      try:
          if self.cdp_session:
              self.cdp_session = None

          if self.page:
              self.page.close()
              self.page = None

          if self.browser:
              self.browser.close()
              self.browser = None

          if self.playwright:
              self.playwright.stop()
              self.playwright = None
      except Exception as e:
          # Best effort cleanup
          print(f"Warning during cleanup: {e}")
  ```
- **Improvement:** Better error handling, no zombie processes

**⚠️ MAJOR CHECKPOINT:** After Task 2.13, CDPRecorder migration complete - test thoroughly before proceeding

---

## 🔄 PHASE 3: INTEGRATION UPDATES
**Duration: 30 minutes | Risk: MEDIUM | Status: ⏸️ Pending**

### Task 3.1: Update `server.py` - Remove chrome_path
- **File:** `src/server.py`
- **Lines:** 124-128
- **Risk:** MEDIUM (breaking change)
- **Effort:** 10 minutes
- **Old Code:**
  ```python
  chrome_path = os.environ.get("CHROME_PATH", "...")
  recorder = CDPRecorder(chrome_path=chrome_path)
  ```
- **New Code:**
  ```python
  headless = os.environ.get("HEADLESS", "false").lower() == "true"
  recorder = CDPRecorder(headless=headless)
  ```
- **Eliminates:** CHROME_PATH security risk from audit

### Task 3.2: Update Error Handling in server.py
- **Lines:** 173-174
- **Risk:** LOW
- **Effort:** 10 minutes
- **New Code:**
  ```python
  try:
      session_data = recorder.stop()
      processed_events = event_processor.process_events(session_data["events"])
      session_data["events"] = processed_events
      file_path = storage.save_recording(session_data)
  finally:
      try:
          recorder.close()
      finally:
          if session_id in active_recorders:
              del active_recorders[session_id]
  ```
- **Security Fix:** Ensures cleanup always happens

### Task 3.3: Update record.py
- **File:** `record.py`
- **Lines:** 23-24
- **Risk:** LOW
- **Effort:** 5 minutes
- **Change:**
  ```python
  recorder = CDPRecorder(headless=False)
  ```

---

## ✅ PHASE 4: TESTING & VALIDATION
**Duration: 1.5 hours | Risk: LOW | Status: ⏸️ Pending**

### Phase 4A: Component Tests (40 min)

#### Task 4.1: Test Browser Launch
- **Effort:** 10 minutes
- **Test:**
  ```python
  from src.cdp_recorder import CDPRecorder
  recorder = CDPRecorder(headless=True)
  recorder.start_chrome()
  session_id = recorder.connect()
  assert session_id
  recorder.close()
  ```

#### Task 4.2: Test Console Event Capture
- **Effort:** 10 minutes
- **Test:**
  ```python
  recorder.start_chrome("data:text/html,<script>console.log('test')</script>")
  recorder.connect()
  import time; time.sleep(2)
  events = recorder.get_events()
  assert any(e['type'] == 'console_log' for e in events)
  ```

#### Task 4.3: Test Click Event Capture
- **Effort:** 15 minutes
- **Test:** HTML page with button, verify click captured

#### Task 4.4: Test Error Capture
- **Effort:** 10 minutes
- **Test:** Page with JS error, verify captured

### Phase 4B: Integration Tests (50 min)

#### Task 4.5: Full record.py Workflow
- **Effort:** 15 minutes
- **Steps:**
  1. Run `python record.py https://example.com`
  2. Click elements
  3. Stop recording
  4. Verify JSON saved with all event types

#### Task 4.6: MCP Server Test
- **Effort:** 20 minutes
- **Steps:**
  1. Start server: `python -m src.server`
  2. Send start_recording request
  3. Interact
  4. Send stop_recording request
  5. Verify saved

#### Task 4.7: Validate Event Masking
- **Effort:** 10 minutes
- **Test:** Password field, verify masked

#### Task 4.8: Performance Test
- **Effort:** 10 minutes
- **Test:** Complex page with many DOM mutations

#### Task 4.9: Cleanup Test
- **Effort:** 5 minutes
- **Test:** No zombie processes after close()

---

## 🔒 PHASE 5: SECURITY HARDENING
**Duration: 2 hours | Risk: LOW | Status: ⏸️ Pending**

### Phase 5A: Input Validation (40 min)

#### Task 5.1: URL Validation
- **Status:** ✅ Already done in Task 2.3

#### Task 5.2: Create session_id Validation Helper
- **File:** `src/storage.py`
- **Effort:** 15 minutes
- **Add:**
  ```python
  import re

  def _validate_session_id(self, session_id: str) -> None:
      """Validate session_id is UUID format."""
      if not re.match(r'^[a-f0-9-]{36}$', session_id):
          raise ValueError(f"Invalid session_id format")
  ```

#### Task 5.3-5.5: Apply Validation to Storage Methods
- **Files:** `src/storage.py`
- **Effort:** 10 minutes (combined)
- **Apply to:** `load_recording()`, `delete_recording()`, `save_recording()`

#### Task 5.6: Apply Validation to Server Handlers
- **File:** `src/server.py`
- **Lines:** 158, 195, 221
- **Effort:** 10 minutes
- **Add to each handler:**
  ```python
  import re
  if not re.match(r'^[a-f0-9-]{36}$', session_id):
      raise ValueError("Invalid session_id format")
  ```

### Phase 5B: Resource Limits (30 min)

#### Task 5.7: Add Event Count Limit
- **File:** `src/cdp_recorder.py`
- **Effort:** 10 minutes
- **Add to __init__:**
  ```python
  self.max_events = 10000
  ```
- **Add to _add_event:**
  ```python
  if len(self.events) >= self.max_events:
      raise RuntimeError(f"Event limit reached: {self.max_events}")
  ```

#### Task 5.8: Add File Size Limit to save_recording()
- **File:** `src/storage.py`
- **Effort:** 10 minutes
- **Add:**
  ```python
  MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
  data_str = json.dumps(recording_data, indent=2)
  if len(data_str.encode()) > MAX_FILE_SIZE:
      raise ValueError(f"Recording too large")
  ```

#### Task 5.9: Add File Size Check to list_recordings()
- **File:** `src/storage.py`
- **Effort:** 8 minutes
- **Add size check before reading**

### Phase 5C: Error Hardening (20 min)

#### Task 5.10: Sanitize Error Messages
- **Files:** Multiple
- **Effort:** 15 minutes
- **Remove sensitive details from error messages**

#### Task 5.11: Validate Regex Patterns
- **File:** `src/event_processor.py`
- **Effort:** 15 minutes
- **Add regex validation for custom selectors**

---

## 📚 PHASE 6: DOCUMENTATION UPDATES
**Duration: 45 minutes | Risk: NONE | Status: ⏸️ Pending**

### Task 6.1: Update README - Installation
- **Lines:** 14-21
- **Effort:** 10 minutes
- **Add:** `playwright install chromium` step

### Task 6.2: Update README - MCP Configuration
- **Lines:** 69-131
- **Effort:** 15 minutes
- **Remove:** CHROME_PATH examples
- **Add:** HEADLESS option

### Task 6.3: Update README - Troubleshooting
- **Lines:** 349-368
- **Effort:** 10 minutes
- **Update:** Browser detection section

### Task 6.4: Update CLAUDE.md
- **Effort:** 15 minutes
- **Update:** Architecture, dependencies, examples

### Task 6.5: Update Inline Comments
- **File:** `src/cdp_recorder.py`
- **Effort:** 10 minutes
- **Update:** Docstrings to reference playwright

### Task 6.6: Create MIGRATION_NOTES.md
- **Effort:** 10 minutes
- **Document:** Migration rationale, breaking changes, benefits

---

## 🧪 PHASE 7: FINAL VALIDATION
**Duration: 30 minutes | Risk: LOW | Status: ⏸️ Pending**

### Task 7.1: Run All Tests
- **Effort:** 5 minutes
- **Command:** `pytest`

### Task 7.2: Manual E2E Test
- **Effort:** 15 minutes
- **Test:** Full workflow on real website

### Task 7.3: Performance Comparison
- **Effort:** 10 minutes
- **Compare:** Old vs new implementation

### Task 7.4: Security Validation
- **Effort:** 15 minutes
- **Test:** All security fixes work

---

## 📦 PHASE 8: DEPLOYMENT & CLEANUP
**Duration: 20 minutes | Risk: LOW | Status: ⏸️ Pending**

### Task 8.1: Update Version Number
- **File:** `pyproject.toml`
- **Change:** `version = "0.2.0"`

### Task 8.2: Create Git Commit
- **Message:**
  ```
  Migrate from pychrome to playwright

  BREAKING CHANGES:
  - CDPRecorder constructor signature changed
  - CHROME_PATH env var removed

  Security improvements:
  - URL validation
  - session_id validation
  - Event/file size limits

  Benefits:
  - Better maintained (Microsoft)
  - Cleaner API
  - Active security updates
  ```

### Task 8.3: Tag Release
- **Command:** `git tag -a v0.2.0 -m "Playwright migration"`

### Task 8.4: Remove Backup Files
- **Command:** `rm src/cdp_recorder.py.backup`

### Task 8.5: Update MCP Configuration
- **Action:** Remove CHROME_PATH, restart Claude Code

---

## 🎯 Risk Mitigation

### High-Risk Tasks
1. **Task 2.6** - Event listener setup
   - **Mitigation:** Split into 3 sub-tasks, test each

2. **Task 2.2** - Constructor refactor
   - **Mitigation:** Update all callers immediately

3. **Task 3.1** - Server integration
   - **Mitigation:** Update docs simultaneously

### Mandatory Checkpoints
1. ✋ After Task 2.6 - Validate event listeners work
2. ✋ After Task 2.13 - Full CDPRecorder migration complete
3. ✋ After Phase 4 - All tests must pass
4. ✋ After Phase 5 - Security validation

### Rollback Plan
If migration fails at any point:
```bash
git checkout master
pip install pychrome==0.2.4
pip uninstall playwright
```

---

## 📊 Progress Tracking

### Completed Tasks
- [x] Task 0.1: Create migration branch
- [x] Task 0.4: Research playwright API
- [x] Task 0.5: Create this document

### In Progress
- [ ] Task 0.2: Install playwright

### Pending
- All remaining tasks

---

## 📝 Notes & Observations

### Migration Date
- Started: 2025-10-05

### Key Decisions
1. Using sync API instead of async for simplicity
2. Keeping CDP for DOM events (playwright doesn't expose high-level DOM mutation events)
3. Hybrid approach: High-level events (console, errors) + CDP (DOM)

### Issues Encountered
- None yet

### Performance Observations
- TBD after testing

---

**Last Updated:** 2025-10-05
**Next Task:** Install Playwright (Task 0.2)
