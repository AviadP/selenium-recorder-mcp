"""Chrome DevTools Protocol recorder for browser interactions."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Callable

from playwright.async_api import async_playwright, Browser, Page, CDPSession

logger = logging.getLogger(__name__)


class CDPRecorder:
    """Records browser events using Chrome DevTools Protocol."""

    def __init__(self, headless: bool = False):
        """
        Initialize CDP recorder.

        Args:
            headless (bool): Run browser in headless mode.
        """
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.cdp_session: Optional[CDPSession] = None
        self.session_id: Optional[str] = None
        self.events: list[dict] = []
        self.start_time: Optional[datetime] = None
        self._pending_url: Optional[str] = None
        self.max_events = 10000  # Security: prevent disk fill attack

    async def start_chrome(self, url: Optional[str] = None) -> None:
        """
        Launch browser with playwright.

        Args:
            url (str): Optional URL to navigate to on start.

        Raises:
            ValueError: If URL scheme is invalid.
            RuntimeError: If browser fails to start.
        """
        if self.browser:
            return

        # URL validation (SECURITY FIX #1 - prevent file:// and other dangerous schemes)
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            # Allow http, https, data (for testing), and empty (relative URLs)
            if parsed.scheme and parsed.scheme not in ('http', 'https', 'data'):
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http/https/data allowed.")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-first-run', '--no-default-browser-check']
        )
        self.page = await self.browser.new_page(ignore_https_errors=True)

        # Don't navigate yet - let connect() set up listeners first
        # Navigation will happen in connect() if URL was provided
        self._pending_url = url

    async def connect(self) -> str:
        """
        Setup event recording on existing page.

        Returns:
            str: Session ID for this recording.

        Raises:
            RuntimeError: If browser not started.
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start_chrome() first.")

        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.events = []

        # Create CDP session for low-level DOM events
        self.cdp_session = await self.page.context.new_cdp_session(self.page)

        await self._enable_domains()
        await self._setup_event_listeners()

        # Now navigate if URL was provided - listeners are ready
        if self._pending_url:
            await self.page.goto(self._pending_url)
            self._pending_url = None

        return self.session_id

    async def _enable_domains(self) -> None:
        """Enable necessary CDP domains for event capture."""
        # Only enable CDP domains (DOM)
        # High-level events (console, errors) don't need enabling in playwright
        await self.cdp_session.send("DOM.enable")

        # Add binding for click tracking
        await self.page.expose_binding("recordClick", self._handle_click_binding)

    async def _setup_event_listeners(self) -> None:
        """Set up event listeners for recording."""
        # High-level playwright events (cleaner API)
        self.page.on("console", self._on_console_log)
        self.page.on("pageerror", self._on_js_error)
        self.page.on("load", self._on_page_load)

        # CDP events for DOM mutations
        self.cdp_session.on("DOM.documentUpdated", self._on_document_updated)
        self.cdp_session.on("DOM.setChildNodes", self._on_set_child_nodes)
        self.cdp_session.on("DOM.attributeModified", self._on_attribute_modified)
        self.cdp_session.on("DOM.characterDataModified", self._on_character_data_modified)

        # Inject click tracking script
        await self._inject_click_tracker()

    def _add_event(self, event_type: str, data: dict) -> None:
        """
        Add event to recording with timestamp.

        Args:
            event_type (str): Type of event.
            data (dict): Event data.

        Raises:
            RuntimeError: If event limit reached.
        """
        # Security: prevent unbounded event recording
        if len(self.events) >= self.max_events:
            raise RuntimeError(f"Event limit reached: {self.max_events}")

        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        self.events.append(event)

    def _on_console_log(self, msg) -> None:
        """Handle console.log events."""
        # Extract args safely - use text representation to avoid async issues
        try:
            args = [str(arg) for arg in msg.args]
        except (AttributeError, TypeError, RuntimeError) as e:
            # Fallback to message text if args extraction fails
            args = [msg.text]

        self._add_event("console_log", {
            "level": msg.type,
            "args": args,
            "location": {
                "url": msg.location.get("url", ""),
                "lineNumber": msg.location.get("lineNumber", 0)
            }
        })

    def _on_js_error(self, error) -> None:
        """Handle JavaScript error events."""
        self._add_event("js_error", {
            "message": str(error),
            "stack": error.stack if hasattr(error, 'stack') else ""
        })

    def _on_page_load(self) -> None:
        """Handle page load events - reinject click tracker."""
        asyncio.create_task(self._inject_click_tracker())

    def _on_document_updated(self, params: dict = None) -> None:
        """Handle document updated events."""
        self._add_event("document_updated", {})

    def _on_set_child_nodes(self, params: dict = None) -> None:
        """Handle DOM child nodes modification."""
        params = params or {}
        self._add_event("dom_set_child_nodes", {
            "parent_id": params.get("parentId"),
            "nodes": params.get("nodes", []),
        })

    def _on_attribute_modified(self, params: dict = None) -> None:
        """Handle DOM attribute modification."""
        params = params or {}
        self._add_event("dom_attribute_modified", {
            "node_id": params.get("nodeId"),
            "name": params.get("name"),
            "value": params.get("value"),
        })

    def _on_character_data_modified(self, params: dict = None) -> None:
        """Handle DOM text content modification."""
        params = params or {}
        self._add_event("dom_character_data_modified", {
            "node_id": params.get("nodeId"),
            "character_data": params.get("characterData"),
        })

    def _handle_click_binding(self, source, data: str) -> None:
        """Handle click binding calls from browser."""
        import json
        try:
            click_data = json.loads(data)
            self._add_event("click", click_data)
        except json.JSONDecodeError:
            pass

    async def _inject_click_tracker(self) -> None:
        """Inject JavaScript to track click events."""
        script = """
        (function() {
            // Generate XPath for an element
            function getXPath(element) {
                if (element.id !== '') {
                    return '//*[@id="' + element.id + '"]';
                }
                if (element === document.body) {
                    return '/html/body';
                }

                let ix = 0;
                const siblings = element.parentNode ? element.parentNode.childNodes : [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
                        return parentPath + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
                return '';
            }

            // Generate CSS selector for an element
            function getCSSSelector(element) {
                if (element.id) {
                    return '#' + element.id;
                }

                let path = [];
                while (element && element.nodeType === Node.ELEMENT_NODE) {
                    let selector = element.nodeName.toLowerCase();
                    if (element.className) {
                        const classes = element.className.trim().split(/\\s+/).filter(c => c);
                        if (classes.length > 0) {
                            selector += '.' + classes.join('.');
                        }
                    }
                    path.unshift(selector);
                    element = element.parentNode;
                }
                return path.join(' > ');
            }

            // Get all attributes as object
            function getAttributes(element) {
                const attrs = {};
                for (let i = 0; i < element.attributes.length; i++) {
                    const attr = element.attributes[i];
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }

            // Track clicks
            document.addEventListener('click', function(event) {
                const element = event.target;

                const clickData = {
                    tagName: element.tagName,
                    id: element.id || null,
                    className: element.className || null,
                    classList: element.classList ? Array.from(element.classList) : [],
                    attributes: getAttributes(element),
                    textContent: element.textContent ? element.textContent.trim().substring(0, 200) : null,
                    innerHTML: element.innerHTML ? element.innerHTML.substring(0, 500) : null,
                    xpath: getXPath(element),
                    cssSelector: getCSSSelector(element),
                    href: element.href || null,
                    src: element.src || null,
                    coordinates: {
                        x: event.clientX,
                        y: event.clientY,
                        pageX: event.pageX,
                        pageY: event.pageY
                    },
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    url: window.location.href
                };

                // Send click data via binding
                window.recordClick(JSON.stringify(clickData));
            }, true);
        })();
        """

        try:
            await self.page.evaluate(script)
        except Exception as e:
            logger.warning(f"Failed to inject click tracker: {e}")

    def stop(self) -> dict:
        """
        Stop recording and return session data.

        Returns:
            dict: Recording session data with metadata and events.
        """
        if not self.session_id:
            raise RuntimeError("No active recording session.")

        session_data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": datetime.now().isoformat(),
            "events": self.events,
        }

        return session_data

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self.cdp_session:
                # Don't need to explicitly detach - page close handles it
                self.cdp_session = None

            if self.page:
                await self.page.close()
                self.page = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            # Best effort cleanup - log but don't raise
            logger.warning(f"Warning during cleanup: {e}")
