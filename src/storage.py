"""Storage for recording sessions."""

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

        with open(filepath, "w") as f:
            json.dump(recording_data, f, indent=2)

        return str(filepath)

    def load_recording(self, session_id: str) -> Optional[dict]:
        """
        Load recording by session ID.

        Args:
            session_id (str): Session ID to load.

        Returns:
            dict: Recording data or None if not found.
        """
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

        for filepath in self.recordings_dir.glob("*.json"):
            with open(filepath, "r") as f:
                data = json.load(f)
                recordings.append({
                    "session_id": data.get("session_id"),
                    "url": data.get("url"),
                    "start_time": data.get("start_time"),
                    "event_count": data.get("metadata", {}).get("event_count", 0),
                    "filepath": str(filepath),
                })

        return sorted(recordings, key=lambda x: x.get("start_time", ""), reverse=True)

    def delete_recording(self, session_id: str) -> bool:
        """
        Delete recording by session ID.

        Args:
            session_id (str): Session ID to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        pattern = f"{session_id}_*.json"
        matching_files = list(self.recordings_dir.glob(pattern))

        if not matching_files:
            return False

        for filepath in matching_files:
            filepath.unlink()

        return True
