"""Process and sanitize recorded events."""

import re
from typing import Optional


class EventProcessor:
    """Process events with sensitive field masking and enrichment."""

    DEFAULT_SENSITIVE_SELECTORS = [
        r"input\[type=['\"]?password['\"]?\]",
        r"input\[name\*=['\"]?password['\"]?\]",
        r"input\[name\*=['\"]?passwd['\"]?\]",
        r"input\[id\*=['\"]?password['\"]?\]",
        r"input\[name\*=['\"]?secret['\"]?\]",
        r"input\[name\*=['\"]?token['\"]?\]",
    ]

    def __init__(self, sensitive_selectors: Optional[list[str]] = None):
        """
        Initialize event processor.

        Args:
            sensitive_selectors (list[str]): CSS selector patterns for sensitive fields.
        """
        if sensitive_selectors is None:
            self.sensitive_selectors = self.DEFAULT_SENSITIVE_SELECTORS
        else:
            self.sensitive_selectors = sensitive_selectors + self.DEFAULT_SENSITIVE_SELECTORS

        self.sensitive_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_selectors
        ]

    def _is_sensitive_field(self, node_data: dict) -> bool:
        """
        Check if node represents a sensitive field.

        Args:
            node_data (dict): Node data from CDP event.

        Returns:
            bool: True if field is sensitive.
        """
        if not isinstance(node_data, dict):
            return False

        node_name = node_data.get("nodeName", "").lower()
        if node_name != "input":
            return False

        attributes = node_data.get("attributes", [])
        if not attributes:
            return False

        attr_str = " ".join(str(a) for a in attributes).lower()

        for pattern in self.sensitive_patterns:
            if pattern.search(attr_str):
                return True

        return False

    def _mask_value(self, value: str) -> str:
        """
        Mask sensitive value.

        Args:
            value (str): Original value.

        Returns:
            str: Masked value.
        """
        if not value:
            return value
        return "***MASKED***"

    def process_event(self, event: dict) -> dict:
        """
        Process single event with sanitization and enrichment.

        Args:
            event (dict): Raw event from recorder.

        Returns:
            dict: Processed event.
        """
        event_type = event.get("type")

        if event_type == "dom_attribute_modified":
            return self._process_attribute_modified(event)

        if event_type == "dom_set_child_nodes":
            return self._process_set_child_nodes(event)

        if event_type == "dom_character_data_modified":
            return self._process_character_data_modified(event)

        return event

    def _process_attribute_modified(self, event: dict) -> dict:
        """Process attribute modification event."""
        data = event.get("data", {})
        attr_name = data.get("name", "").lower()

        if attr_name == "value" or "password" in attr_name or "secret" in attr_name:
            data["value"] = self._mask_value(data.get("value", ""))
            data["_masked"] = True

        return event

    def _process_set_child_nodes(self, event: dict) -> dict:
        """Process set child nodes event with sensitive field detection."""
        data = event.get("data", {})
        nodes = data.get("nodes", [])

        if not nodes:
            return event

        processed_nodes = []
        for node in nodes:
            if self._is_sensitive_field(node):
                node = self._mask_node_attributes(node)
            processed_nodes.append(node)

        data["nodes"] = processed_nodes
        return event

    def _process_character_data_modified(self, event: dict) -> dict:
        """Process character data modification event."""
        return event

    def _mask_node_attributes(self, node: dict) -> dict:
        """
        Mask sensitive attributes in node.

        Args:
            node (dict): Node data.

        Returns:
            dict: Node with masked attributes.
        """
        if "attributes" not in node:
            return node

        attributes = node.get("attributes", [])
        masked_attributes = []

        for i, attr in enumerate(attributes):
            if i % 2 == 1:
                attr_name = attributes[i - 1] if i > 0 else ""
                if isinstance(attr_name, str) and (
                    attr_name.lower() == "value"
                    or "password" in attr_name.lower()
                    or "secret" in attr_name.lower()
                ):
                    masked_attributes.append(self._mask_value(str(attr)))
                    continue
            masked_attributes.append(attr)

        node["attributes"] = masked_attributes
        node["_masked"] = True
        return node

    def process_events(self, events: list[dict]) -> list[dict]:
        """
        Process multiple events.

        Args:
            events (list[dict]): List of raw events.

        Returns:
            list[dict]: List of processed events.
        """
        return [self.process_event(event) for event in events]

    def analyze_events(self, events: list[dict]) -> dict:
        """
        Analyze events and provide summary.

        Args:
            events (list[dict]): List of events.

        Returns:
            dict: Summary of events.
        """
        summary = {
            "total_events": len(events),
            "event_types": {},
            "console_logs": 0,
            "js_errors": 0,
            "dom_mutations": 0,
            "clicks": 0,
            "masked_events": 0,
        }

        for event in events:
            event_type = event.get("type", "unknown")
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1

            if event_type == "console_log":
                summary["console_logs"] += 1
            elif event_type == "js_error":
                summary["js_errors"] += 1
            elif event_type == "click":
                summary["clicks"] += 1
            elif event_type.startswith("dom_"):
                summary["dom_mutations"] += 1

            if event.get("data", {}).get("_masked"):
                summary["masked_events"] += 1

        return summary
