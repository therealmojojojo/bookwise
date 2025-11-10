"""
E-reader delivery service using Calibre export to shared folder
"""
import subprocess
from pathlib import Path
from typing import Dict, Optional
import logging
import os
import time

logger = logging.getLogger(__name__)


class DeliveryService:
    """Handles sending books to e-reader via Calibre export to shared folder"""

    def __init__(self, config: Dict):
        """
        Initialize delivery service with Calibre export settings

        Args:
            config: Configuration dict with delivery settings
        """
        self.calibredb_path = config.get('CALIBREDB_PATH', '/Applications/calibre.app/Contents/MacOS/calibredb')
        self.export_folder = config.get('EREADER_EXPORT_FOLDER')
        self.calibre_library_path = config.get('CALIBRE_LIBRARY_PATH')
        self.auto_close_calibre = config.get('AUTO_CLOSE_CALIBRE', True)  # Auto-close Calibre GUI if running

        if not self.export_folder:
            raise ValueError("EREADER_EXPORT_FOLDER must be configured")

        # Create export folder if it doesn't exist
        Path(self.export_folder).mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized delivery service with export folder: {self.export_folder}")
        logger.info(f"Using calibredb at: {self.calibredb_path}")
        logger.info(f"Auto-close Calibre GUI: {self.auto_close_calibre}")

    def _is_calibre_running(self) -> bool:
        """
        Check if Calibre GUI is currently running

        Returns:
            True if Calibre is running, False otherwise
        """
        try:
            # Check if Calibre process is running on macOS
            result = subprocess.run(
                ['pgrep', '-f', 'calibre'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Failed to check if Calibre is running: {e}")
            return False

    def _close_calibre(self) -> bool:
        """
        Close Calibre GUI application

        Returns:
            True if Calibre was closed successfully, False otherwise
        """
        try:
            logger.info("Attempting to close Calibre GUI...")

            # Try graceful shutdown first using AppleScript
            applescript = """
            tell application "calibre"
                quit
            end tell
            """
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Wait a bit for Calibre to fully close
                time.sleep(2)

                # Verify it's closed
                if not self._is_calibre_running():
                    logger.info("Successfully closed Calibre GUI")
                    return True
                else:
                    logger.warning("Calibre GUI still running after quit command")

            # If graceful shutdown failed, try pkill as fallback
            logger.info("Attempting forceful shutdown of Calibre...")
            subprocess.run(['pkill', '-f', 'calibre'], timeout=5)
            time.sleep(2)

            if not self._is_calibre_running():
                logger.info("Successfully force-closed Calibre GUI")
                return True

            logger.warning("Failed to close Calibre GUI")
            return False

        except Exception as e:
            logger.error(f"Error while closing Calibre: {e}", exc_info=True)
            return False

    async def send_to_ereader(
        self, 
        book_id: int,
        book_format: str,
        title: str,
        author: str,
        device_name: Optional[str] = None
    ) -> Dict:
        """
        Export book to shared folder using calibredb export
        
        Args:
            book_id: Calibre book ID
            book_format: File format (epub, mobi, etc.)
            title: Book title
            author: Book author
            device_name: Optional device name (not used, kept for API compatibility)
            
        Returns:
            Dict with status, message, destination, format
        """
        try:
            return await self._export_via_calibredb(book_id, book_format, title, author)
        except Exception as e:
            logger.error(f"Failed to export book: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'destination': None,
                'format': book_format
            }
    
    async def _export_via_calibredb(
        self,
        book_id: int,
        book_format: str,
        title: str,
        author: str
    ) -> Dict:
        """
        Export book using calibredb export to shared folder

        Args:
            book_id: Calibre book ID
            book_format: File format to export
            title: Book title
            author: Book author

        Returns:
            Dict with status, message, destination, format
        """
        # Check if Calibre GUI is running and close it if configured
        if self.auto_close_calibre and self._is_calibre_running():
            logger.warning("Calibre GUI is running, which may interfere with calibredb. Attempting to close it...")
            if self._close_calibre():
                logger.info("Calibre GUI closed successfully, proceeding with export")
            else:
                logger.warning("Could not close Calibre GUI automatically. Export may fail.")

        # Prepare calibredb export command
        cmd = [
            self.calibredb_path,
            'export',
            str(book_id),
            '--to-dir', self.export_folder,
            '--single-dir',  # Export to a single flat folder
            '--formats', book_format.upper(),  # Only export requested format
            '--dont-save-cover',  # Skip cover to save space
            '--dont-write-opf',  # Skip metadata file
            '--template', '{title} - {authors}',  # Simple filename template
        ]

        # Add library path if configured
        if self.calibre_library_path:
            cmd.extend(['--library-path', self.calibre_library_path])

        logger.info(f"Exporting book {book_id} ({title}) to {self.export_folder}")
        logger.debug(f"Command: {' '.join(cmd)}")

        # Execute calibredb export with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60  # Increased timeout for large books
                )

                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip()

                    # Check if error is due to Calibre being open
                    if "Another calibre program" in error_msg or "database is locked" in error_msg.lower():
                        if attempt < max_retries - 1 and self.auto_close_calibre:
                            logger.warning(f"Export failed due to Calibre being open. Attempt {attempt + 1}/{max_retries}")

                            # Try to close Calibre and retry
                            if self._close_calibre():
                                logger.info("Retrying export after closing Calibre...")
                                time.sleep(1)
                                continue
                            else:
                                raise Exception("Cannot export: Calibre GUI is running. Please close Calibre and try again.")
                        else:
                            raise Exception("Cannot export: Calibre GUI is running and could not be closed automatically. Please close Calibre manually and try again.")

                    logger.error(f"calibredb export failed: {error_msg}")
                    raise Exception(f"Export failed: {error_msg}")

                # Success - break out of retry loop
                break

            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    logger.warning(f"Export timeout. Attempt {attempt + 1}/{max_retries}")
                    continue
                raise Exception(f"Export timed out after 60 seconds")

        # Find the exported file (outside retry loop)
        export_path = Path(self.export_folder)
        # The file will be named according to the template
        exported_files = list(export_path.glob(f"*.{book_format.lower()}"))

        if exported_files:
            # Sort by modification time to get the most recently exported file
            exported_file = max(exported_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Successfully exported '{title}' to {exported_file}")

            return {
                'status': 'sent',
                'message': f'Successfully exported "{title}" by {author} to your e-reader folder',
                'destination': exported_file.name,  # Only the filename, not the full path
                'format': book_format
            }
        else:
            logger.warning(f"Export succeeded but file not found in {self.export_folder}")
            return {
                'status': 'sent',
                'message': f'Exported "{title}" by {author} to e-reader folder',
                'destination': 'e-reader folder',  # Generic destination
                'format': book_format
            }
    
    def get_export_folder_contents(self) -> list[Dict]:
        """
        List contents of export folder
        
        Returns:
            List of exported files with metadata
        """
        export_path = Path(self.export_folder)
        
        if not export_path.exists():
            return []
        
        files = []
        for file in export_path.iterdir():
            if file.is_file():
                files.append({
                    'name': file.name,
                    'size': file.stat().st_size,
                    'modified': file.stat().st_mtime,
                    'path': str(file)
                })
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)

