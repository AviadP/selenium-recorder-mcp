"""Chrome DevTools Protocol recorder for browser interactions."""

import subprocess
import time
import uuid
from datetime import datetime
from typing import Optional, Callable

import pychrome


class CDPRecorder:
    """Records browser events using Chrome DevTools Protocol."""

    def __init__(
        self,
        chrome_path: str = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        debug_port: int = 9222,
    ):
        """
        Initialize CDP recorder.

        Args:
            chrome_path (str): Path to Chrome executable.
            debug_port (int): Port for remote debugging.
        """
        self.chrome_path = chrome_path
        self.debug_port = debug_port
        self.chrome_process: Optional[subprocess.Popen] = None
        self.browser: Optional[pychrome.Browser] = None
        self.tab: Optional[pychrome.Tab] = None
        self.session_id: Optional[str] = None
        self.events: list[dict] = []
        self.start_time: Optional[datetime] = None
        self.event_callback: Optional[Callable] = None

    def start_chrome(self, url: Optional[str] = None) -> None:
        """
        Launch Chrome with remote debugging enabled.

        Args:
            url (str): Optional URL to navigate to on start.

        Raises:
            RuntimeError: If Chrome fails to start.
        """
        if self.chrome_process:
            return

        cmd = [
            self.chrome_path,
            f"--remote-debugging-port={self.debug_port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--user-data-dir=/tmp/chrome-debug-profile",
        ]

        if url:
            cmd.append(url)

        self.chrome_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        time.sleep(2)

    def connect(self) -> str:
        """
        Connect to Chrome via CDP and start recording session.

        Returns:
            str: Session ID for this recording.

        Raises:
            RuntimeError: If connection fails.
        """
        if not self.chrome_process:
            raise RuntimeError("Chrome not started. Call start_chrome() first.")

        self.browser = pychrome.Browser(url=f"http://127.0.0.1:{self.debug_port}")
        self.tab = self.browser.list_tab()[0]
        self.tab.start()

        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.events = []

        self._enable_domains()
        self._setup_event_listeners()

        return self.session_id

    def _enable_domains(self) -> None:
        """Enable necessary CDP domains for event capture."""
        self.tab.Runtime.enable()
        self.tab.Log.enable()
        self.tab.DOM.enable()
        self.tab.Network.enable()

        # Add binding for click tracking
        self.tab.Runtime.addBinding(name="recordClick")

    def _setup_event_listeners(self) -> None:
        """Set up CDP event listeners for recording."""
        self.tab.Runtime.consoleAPICalled = self._on_console_log
        self.tab.Runtime.exceptionThrown = self._on_js_error
        self.tab.Runtime.bindingCalled = self._on_binding_called
        self.tab.DOM.documentUpdated = self._on_document_updated
        self.tab.DOM.setChildNodes = self._on_set_child_nodes
        self.tab.DOM.attributeModified = self._on_attribute_modified
        self.tab.DOM.characterDataModified = self._on_character_data_modified

        # Inject click tracking script
        self._inject_click_tracker()

    def _add_event(self, event_type: str, data: dict) -> None:
        """
        Add event to recording with timestamp.

        Args:
            event_type (str): Type of event.
            data (dict): Event data.
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        self.events.append(event)

        if self.event_callback:
            self.event_callback(event)

    def _on_console_log(self, **kwargs) -> None:
        """Handle console.log events."""
        self._add_event("console_log", {
            "level": kwargs.get("type", "log"),
            "args": [str(arg.get("value", "")) for arg in kwargs.get("args", [])],
        })

    def _on_js_error(self, **kwargs) -> None:
        """Handle JavaScript error events."""
        exception_details = kwargs.get("exceptionDetails", {})
        self._add_event("js_error", {
            "message": exception_details.get("text", ""),
            "stack": exception_details.get("exception", {}).get("description", ""),
        })

    def _on_document_updated(self, **kwargs) -> None:
        """Handle document updated events."""
        self._add_event("document_updated", {})

        # Reinject click tracker on new page load
        time.sleep(0.5)  # Wait for page to be ready
        self._inject_click_tracker()

    def _on_set_child_nodes(self, **kwargs) -> None:
        """Handle DOM child nodes modification."""
        self._add_event("dom_set_child_nodes", {
            "parent_id": kwargs.get("parentId"),
            "nodes": kwargs.get("nodes", []),
        })

    def _on_attribute_modified(self, **kwargs) -> None:
        """Handle DOM attribute modification."""
        self._add_event("dom_attribute_modified", {
            "node_id": kwargs.get("nodeId"),
            "name": kwargs.get("name"),
            "value": kwargs.get("value"),
        })

    def _on_character_data_modified(self, **kwargs) -> None:
        """Handle DOM text content modification."""
        self._add_event("dom_character_data_modified", {
            "node_id": kwargs.get("nodeId"),
            "character_data": kwargs.get("characterData"),
        })

    def _on_binding_called(self, **kwargs) -> None:
        """Handle binding calls (e.g., from click tracking)."""
        binding_name = kwargs.get("name")
        if binding_name != "recordClick":
            return

        payload = kwargs.get("payload", "{}")
        import json
        try:
            click_data = json.loads(payload)
            self._add_event("click", click_data)
        except json.JSONDecodeError:
            pass

    def _inject_click_tracker(self) -> None:
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

            console.log('[CDP Recorder] Click tracking initialized');
        })();
        """

        try:
            self.tab.Runtime.evaluate(expression=script)
        except Exception as e:
            print(f"Failed to inject click tracker: {e}")

    def set_event_callback(self, callback: Callable) -> None:
        """
        Set callback to be called when events are recorded.

        Args:
            callback (Callable): Function to call with each event.
        """
        self.event_callback = callback

    def get_events(self) -> list[dict]:
        """
        Get all recorded events.

        Returns:
            list[dict]: List of recorded events.
        """
        return self.events

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

    def close(self) -> None:
        """Close CDP connection and Chrome browser."""
        if self.tab:
            self.tab.stop()

        if self.chrome_process:
            self.chrome_process.terminate()
            self.chrome_process.wait(timeout=5)
            self.chrome_process = None
