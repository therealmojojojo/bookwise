"""
Enrichment Pipeline Service

Triggers and manages the book enrichment pipeline programmatically.
This allows the MCP server to regenerate tags, embeddings, and update Calibre.
"""
import subprocess
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class EnrichmentPipelineService:
    """Service for triggering the enrichment pipeline"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.enrichment_dir = self.project_root / "src" / "dataenrichment"
        self.status_file = self.project_root / "output" / "enrichment" / "pipeline_status.json"
        self.status_lock = threading.Lock()

        # Verify scripts exist
        self.scripts = {
            'generate_input': self.enrichment_dir / "generate_enrichment_input.py",
            'enrich': self.enrichment_dir / "enrich_books.py",
            'add_tags': self.enrichment_dir / "add_tags_to_calibre.py"
        }

        for name, script_path in self.scripts.items():
            if not script_path.exists():
                logger.warning(f"Enrichment script not found: {script_path}")

    def _write_status(self, status: Dict[str, Any]):
        """Write pipeline status to file (thread-safe)"""
        with self.status_lock:
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)

    def _read_status(self) -> Dict[str, Any]:
        """Read pipeline status from file (thread-safe)"""
        with self.status_lock:
            if self.status_file.exists():
                try:
                    with open(self.status_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error reading status: {e}")
            return {'state': 'idle', 'message': 'No pipeline running'}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current enrichment pipeline status"""
        status_file = self.project_root / "output" / "enrichment" / "enrichment_status.json"
        progress_file = self.project_root / "output" / "enrichment" / "enrichment_progress.json"
        
        status = {
            'status_file_exists': status_file.exists(),
            'progress_file_exists': progress_file.exists()
        }
        
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status['enrichment_status'] = json.load(f)
            except Exception as e:
                logger.error(f"Error reading status file: {e}")
                status['enrichment_status'] = None
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    status['enrichment_progress'] = json.load(f)
            except Exception as e:
                logger.error(f"Error reading progress file: {e}")
                status['enrichment_progress'] = None
        
        return status
    
    def trigger_enrichment(
        self,
        step: str = "full",
        batch_size: Optional[int] = None,
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger enrichment pipeline steps (runs in background, returns immediately)

        Args:
            step: Which step(s) to run:
                - 'generate': Generate input file only
                - 'enrich': Run enrichment only
                - 'tags': Add tags to Calibre only
                - 'full': Run all steps (default)
            batch_size: Limit number of books to process (optional)
            resume: Resume from previous run (for 'enrich' step)

        Returns:
            Dict with status and message (returns immediately, pipeline runs in background)
        """
        # Check if pipeline is already running
        current_status = self._read_status()
        if current_status.get('state') == 'running':
            return {
                'status': 'already_running',
                'message': 'Pipeline is already running in the background',
                'current_step': current_status.get('current_step'),
                'started_at': current_status.get('started_at')
            }

        # Initialize status
        start_time = datetime.now().isoformat()
        initial_status = {
            'state': 'running',
            'started_at': start_time,
            'step': step,
            'batch_size': batch_size,
            'resume': resume,
            'current_step': 'starting',
            'steps_completed': [],
            'message': 'Pipeline starting...'
        }
        self._write_status(initial_status)

        # Launch pipeline in background thread
        thread = threading.Thread(
            target=self._run_pipeline_background,
            args=(step, batch_size, resume),
            daemon=True
        )
        thread.start()

        steps_to_run = []
        if step in ['generate', 'full']:
            steps_to_run.append('generate_input')
        if step in ['enrich', 'full']:
            steps_to_run.append('enrich')
        if step in ['tags', 'full']:
            steps_to_run.append('add_tags')

        return {
            'status': 'started',
            'message': f'Enrichment pipeline started in background (steps: {", ".join(steps_to_run)})',
            'started_at': start_time,
            'step': step,
            'batch_size': batch_size,
            'note': 'Pipeline is running in the background. Use get_pipeline_status() to check progress.'
        }

    def _run_pipeline_background(self, step: str, batch_size: Optional[int], resume: bool):
        """Run the pipeline in the background (internal method)"""
        results = {
            'status': 'success',
            'steps_run': [],
            'outputs': {}
        }

        try:
            # Step 1: Generate input (if needed)
            if step in ['generate', 'full']:
                self._write_status({
                    'state': 'running',
                    'current_step': 'generate_input',
                    'message': 'Generating enrichment input...'
                })
                logger.info("Running: generate_enrichment_input.py")
                result = self._run_script('generate_input', [])
                results['steps_run'].append('generate_input')
                results['outputs']['generate_input'] = result

                if result['returncode'] != 0:
                    self._write_status({
                        'state': 'error',
                        'current_step': 'generate_input',
                        'message': f"Failed at generate_input: {result.get('stderr', 'Unknown error')}"
                    })
                    return

            # Step 2: Enrich books (if needed)
            if step in ['enrich', 'full']:
                self._write_status({
                    'state': 'running',
                    'current_step': 'enrich',
                    'steps_completed': results['steps_run'].copy(),
                    'message': 'Enriching books with AI-generated tags...'
                })
                logger.info("Running: enrich_books.py")

                args = ['--yes']  # Auto-confirm
                if batch_size:
                    args.extend(['--batch-size', str(batch_size)])
                if resume:
                    args.append('--resume')

                result = self._run_script('enrich', args)
                results['steps_run'].append('enrich')
                results['outputs']['enrich'] = result

                if result['returncode'] != 0:
                    self._write_status({
                        'state': 'error',
                        'current_step': 'enrich',
                        'steps_completed': results['steps_run'].copy(),
                        'message': f"Failed at enrich: {result.get('stderr', 'Unknown error')}"
                    })
                    return

            # Step 3: Add tags to Calibre (if needed)
            if step in ['tags', 'full']:
                self._write_status({
                    'state': 'running',
                    'current_step': 'add_tags',
                    'steps_completed': results['steps_run'].copy(),
                    'message': 'Adding tags to Calibre library...'
                })
                logger.info("Running: add_tags_to_calibre.py")

                args = ['--yes']  # Auto-confirm
                if batch_size:
                    args.extend(['--batch-size', str(batch_size)])

                result = self._run_script('add_tags', args)
                results['steps_run'].append('add_tags')
                results['outputs']['add_tags'] = result

                if result['returncode'] != 0:
                    self._write_status({
                        'state': 'error',
                        'current_step': 'add_tags',
                        'steps_completed': results['steps_run'].copy(),
                        'message': f"Failed at add_tags: {result.get('stderr', 'Unknown error')}"
                    })
                    return

            # Success
            completed_at = datetime.now().isoformat()
            self._write_status({
                'state': 'completed',
                'completed_at': completed_at,
                'steps_completed': results['steps_run'],
                'message': f"Successfully completed: {', '.join(results['steps_run'])}"
            })
            logger.info(f"Pipeline completed successfully: {', '.join(results['steps_run'])}")

        except Exception as e:
            logger.error(f"Error in background pipeline: {e}", exc_info=True)
            self._write_status({
                'state': 'error',
                'message': f"Pipeline error: {str(e)}"
            })
    
    def _run_script(self, script_name: str, args: list) -> Dict[str, Any]:
        """
        Run a Python script and capture output
        
        Args:
            script_name: Name of the script ('generate_input', 'enrich', 'add_tags')
            args: Command line arguments
        
        Returns:
            Dict with returncode, stdout, stderr
        """
        script_path = self.scripts.get(script_name)
        
        if not script_path or not script_path.exists():
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f"Script not found: {script_path}"
            }
        
        # Build command
        cmd = [sys.executable, str(script_path)] + args
        
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Script timeout: {script_name}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Script execution timed out (1 hour limit)'
            }
        except Exception as e:
            logger.error(f"Error running script {script_name}: {e}", exc_info=True)
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def regenerate_quality_scores(self) -> Dict[str, Any]:
        """
        Regenerate quality scores (typically run after updating datasources)
        
        Returns:
            Dict with status and message
        """
        score_script = self.project_root / "src" / "scripts" / "generate_unified_scores.py"
        
        if not score_script.exists():
            return {
                'status': 'error',
                'message': f"Score generation script not found: {score_script}"
            }
        
        try:
            logger.info("Regenerating quality scores...")
            
            result = subprocess.run(
                [sys.executable, str(score_script)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'message': 'Quality scores regenerated successfully',
                    'output': result.stdout
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Score generation failed: {result.stderr}',
                    'output': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': 'Score generation timed out (10 minute limit)'
            }
        except Exception as e:
            logger.error(f"Error regenerating scores: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }


