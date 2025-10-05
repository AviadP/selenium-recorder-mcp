"""Storage for recording sessions."""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class RecordingStorage:
    """Manage recording storage as JSON files."""

    def __init__(self, recordings_dir: str = "recordings"):
        """
        Initialize recording storage.

        Args:
            recordings_dir (str): Directory to store recordings.
        """
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

    def _validate_session_id(self, session_id: str) -> None:
        """
        Validate session_id is proper UUID format (SECURITY FIX #2).

        Args:
            session_id (str): Session ID to validate.

        Raises:
            ValueError: If session_id is not valid UUID format.
        """
        if not re.match(r'^[a-f0-9-]{36}$', session_id):
            raise ValueError("Invalid session_id format")

    def save_recording(self, session_data: dict, url: Optional[str] = None) -> str:
        """
        Save recording session to JSON file.

        Args:
            session_data (dict): Session data with events.
            url (str): Optional URL that was recorded.

        Returns:
            str: Path to saved recording file.
        """
        session_id = session_data.get("session_id")
        if not session_id:
            raise ValueError("Session data must contain 'session_id'")

        # Validate session_id format (security - prevent path traversal)
        self._validate_session_id(session_id)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{timestamp}.json"
        filepath = self.recordings_dir / filename

        recording_data = {
            "session_id": session_id,
            "url": url,
            "start_time": session_data.get("start_time"),
            "end_time": session_data.get("end_time"),
            "events": session_data.get("events", []),
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "event_count": len(session_data.get("events", [])),
            },
        }

        # Security: prevent saving excessively large files
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        data_str = json.dumps(recording_data, indent=2)
        if len(data_str.encode()) > MAX_FILE_SIZE:
            raise ValueError(f"Recording too large: {len(data_str)} bytes (max: {MAX_FILE_SIZE})")

        with open(filepath, "w") as f:
            f.write(data_str)

        return str(filepath)

    def load_recording(self, session_id: str) -> Optional[dict]:
        """
        Load recording by session ID.

        Args:
            session_id (str): Session ID to load.

        Returns:
            dict: Recording data or None if not found.
        """
        # Validate session_id format (security - prevent path traversal)
        self._validate_session_id(session_id)

        pattern = f"{session_id}_*.json"
        matching_files = list(self.recordings_dir.glob(pattern))

        if not matching_files:
            return None

        with open(matching_files[0], "r") as f:
            return json.load(f)

    def list_recordings(self) -> list[dict]:
        """
        List all recordings.

        Returns:
            list[dict]: List of recording metadata.
        """
        recordings = []
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB for reading

        for filepath in self.recordings_dir.glob("*.json"):
            # Security: skip excessively large files
            if filepath.stat().st_size > MAX_FILE_SIZE:
                continue

            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    recordings.append({
                        "session_id": data.get("session_id"),
                        "url": data.get("url"),
                        "start_time": data.get("start_time"),
                        "event_count": data.get("metadata", {}).get("event_count", 0),
                        "filepath": str(filepath),
                    })
            except (json.JSONDecodeError, OSError):
                # Skip invalid files
                continue

        return sorted(recordings, key=lambda x: x.get("start_time", ""), reverse=True)

    def delete_recording(self, session_id: str) -> bool:
        """
        Delete recording by session ID.

        Args:
            session_id (str): Session ID to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        # Validate session_id format (security - prevent path traversal)
        self._validate_session_id(session_id)

        pattern = f"{session_id}_*.json"
        matching_files = list(self.recordings_dir.glob(pattern))

        if not matching_files:
            return False

        for filepath in matching_files:
            filepath.unlink()

        return True
