"""
E-reader delivery service using Calibre export to shared folder
"""
import subprocess
from pathlib import Path
from typing import Dict, Optional
import logging
import os

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
        
        if not self.export_folder:
            raise ValueError("EREADER_EXPORT_FOLDER must be configured")
        
        # Create export folder if it doesn't exist
        Path(self.export_folder).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized delivery service with export folder: {self.export_folder}")
        logger.info(f"Using calibredb at: {self.calibredb_path}")
    
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
        
        # Execute calibredb export
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Increased timeout for large books
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"calibredb export failed: {error_msg}")
                raise Exception(f"Export failed: {error_msg}")
            
            # Find the exported file
            export_path = Path(self.export_folder)
            # The file will be named according to the template
            exported_files = list(export_path.glob(f"*{book_format}"))
            
            if exported_files:
                exported_file = exported_files[-1]  # Get most recent
                logger.info(f"Successfully exported '{title}' to {exported_file}")
                
                return {
                    'status': 'sent',
                    'message': f'Exported "{title}" by {author} to shared folder',
                    'destination': str(exported_file),
                    'format': book_format
                }
            else:
                logger.warning(f"Export succeeded but file not found in {self.export_folder}")
                return {
                    'status': 'sent',
                    'message': f'Exported "{title}" by {author} to {self.export_folder}',
                    'destination': self.export_folder,
                    'format': book_format
                }
                
        except subprocess.TimeoutExpired:
            raise Exception(f"Export timed out after 30 seconds")
        except FileNotFoundError:
            raise Exception(f"calibredb not found at {self.calibredb_path}")
    
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

