"""
Simple file-based OAuth token and client persistence
Stores tokens and clients in JSON files so they survive restarts
"""
import json
import os
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class OAuthStore:
    """File-based storage for OAuth tokens and clients"""

    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.bookwise/oauth")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.tokens_file = self.storage_dir / "tokens.json"
        self.codes_file = self.storage_dir / "auth_codes.json"
        self.clients_file = self.storage_dir / "clients.json"

        logger.info(f"OAuth storage initialized at: {self.storage_dir}")

    def load_tokens(self) -> Dict:
        """Load OAuth tokens from disk"""
        try:
            if self.tokens_file.exists():
                with open(self.tokens_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} OAuth tokens from disk")
                    return data
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
        return {}

    def save_tokens(self, tokens: Dict):
        """Save OAuth tokens to disk"""
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            logger.debug(f"Saved {len(tokens)} OAuth tokens to disk")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def load_auth_codes(self) -> Dict:
        """Load authorization codes from disk"""
        try:
            if self.codes_file.exists():
                with open(self.codes_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} authorization codes from disk")
                    return data
        except Exception as e:
            logger.error(f"Failed to load auth codes: {e}")
        return {}

    def save_auth_codes(self, codes: Dict):
        """Save authorization codes to disk"""
        try:
            with open(self.codes_file, 'w') as f:
                json.dump(codes, f, indent=2)
            logger.debug(f"Saved {len(codes)} authorization codes to disk")
        except Exception as e:
            logger.error(f"Failed to save auth codes: {e}")

    def load_clients(self) -> Dict:
        """Load registered clients from disk"""
        try:
            if self.clients_file.exists():
                with open(self.clients_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} registered clients from disk")
                    return data
        except Exception as e:
            logger.error(f"Failed to load clients: {e}")
        return {}

    def save_clients(self, clients: Dict):
        """Save registered clients to disk"""
        try:
            with open(self.clients_file, 'w') as f:
                json.dump(clients, f, indent=2)
            logger.debug(f"Saved {len(clients)} registered clients to disk")
        except Exception as e:
            logger.error(f"Failed to save clients: {e}")
