"""
Semantic DevOps Bot - Batch Log Analyzer
----------------------------------------
This module provides batch analysis capabilities for processing multiple log files,
generating reports, and optionally creating GitHub issues for each error detected.
"""

import os
import sys
import logging
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import concurrent.futures
import traceback

# Import main components
from dotenv import load_dotenv
load_dotenv()
# Fix token passing
github_token = os.getenv("GITHUB_TOKEN")
if github_token:
    os.environ["GITHUB_TOKEN"] = github_token.strip()
    print(f"GitHub token loaded and cleaned: {github_token[:4]}***{github_token[-4:] if len(github_token) > 8 else '***'}")
from main import DevOpsBot, setup_logging

# Constants
MAX_WORKERS = 4  # Maximum number of parallel processing threads
DEFAULT_CONFIG_PATH = "config.json"
REPORT_DIR = "reports"

# Create reports directory at the beginning
os.makedirs(REPORT_DIR, exist_ok=True)
print(f"📁 Ensuring reports directory exists: {REPORT_DIR}")


def scan_log_directory(directory_path: str, recursive: bool = False) -> List[str]:
    """
    Scan a directory for log files.
    
    Args:
        directory_path: Path to the directory containing log files
        recursive: Whether to scan subdirectories recursively
        
    Returns:
        List of paths to log files found
    """
    log_files = []
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"❌ Error: Directory '{directory_path}' does not exist")
        return log_files
    
    if not directory.is_dir():
        print(f"❌ Error: '{directory_path}' is not a directory")
        return log_files
    
    glob_pattern = "**/*.log" if recursive else "*.log"
    log_files = [str(f) for f in directory.glob(glob_pattern) if f.is_file()]
    
    return log_files


def process_log_file(file_path: str, bot: DevOpsBot, logger: logging.Logger) -> Dict[str, Any]:
    """
    Process a single log file.
    
    Args:
        file_path: Path to the log file
        bot: DevOpsBot instance to use for analysis
        logger: Logger instance for logging
        
    Returns:
        Dictionary with analysis results
    """
    start_time = time.time()
    result = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "status": "success",
        "timestamp": datetime.now().isoformat(),
    }
    
    try:
        logger.info(f"Processing file: {file_path}")
        print(f"\n🔍 Analyzing {os.path.basename(file_path)}...")
        
        # Read the log file
        with open(file_path, 'r') as f:
            log_content = f.read()
        
        # Get the file size
        file_size = os.path.getsize(file_path)
        result["file_size_bytes"] = file_size
        
        # Analyze the log
        analysis = bot.analyze_log(log_content)
        
        # Add analysis to result
        result["analysis"] = analysis.get("analysis", {})
        result["severity"] = analysis.get("analysis", {}).get("severity", "UNKNOWN")
        result["error_type"] = analysis.get("analysis", {}).get("error_summary", "Unknown error")
        
        # Add timing information
        elapsed_time = time.time() - start_time
        result["processing_time_seconds"] = elapsed_time
        
        print(f"✅ Completed analysis for {os.path.basename(file_path)} in {elapsed_time:.2f}s")
        logger.info(f"Successfully processed {file_path} in {elapsed_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}", exc_info=True)
        result["status"] = "error"
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"❌ Error processing {os.path.basename(file_path)}: {e}")
    
    return result


def batch_analyze_logs(
    log_dir: str,
    config_path: Optional[str] = None,
    create_issues: bool = False,
    recursive: bool = False,
    parallel: bool = True,
    max_workers: int = MAX_WORKERS
) -> Dict[str, Any]:
    """
    Perform batch analysis on all log files in a directory.
    
    Args:
        log_dir: Directory containing log files
        config_path: Path to configuration file
        create_issues: Whether to create GitHub issues
        recursive: Whether to scan subdirectories recursively
        parallel: Whether to process files in parallel
        max_workers: Maximum number of worker threads for parallel processing
        
    Returns:
        Dictionary with batch analysis results
    """
    # Ensure reports directory exists
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Set up logging
    logger = setup_logging(log_level=logging.INFO)
    logger.info(f"Starting batch analysis of logs in: {log_dir}")
    
    # Scan for log files
    log_files = scan_log_directory(log_dir, recursive=recursive)
    file_count = len(log_files)
    logger.info(f"Found {file_count} log files")
    
    if file_count == 0:
        print("❌ No log files found in the specified directory")
        # Create a minimal report even if no files found
        summary = {
            "status": "error",
            "message": "No log files found",
            "timestamp": datetime.now().isoformat(),
            "directory": log_dir,
            "recursive": recursive,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0,
            "total_processing_time_seconds": 0,
            "results": []
        }
        save_report(summary)
        return summary
    
    # Load configuration
    config = None
    if config_path:
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            config = None
    if config and "github" in config:
        config["github"]["token"] = os.getenv("GITHUB_TOKEN")
    # Enable GitHub issue creation if requested
    if create_issues and config is not None:
        if "github" not in config:
            config["github"] = {}
        config["github"]["create_issues"] = True
        logger.info("GitHub issue creation enabled")
        
        # Validate GitHub configuration
        # validate_github_config()
    
    # Initialize the DevOps Bot
    bot = DevOpsBot(config)
    
    # Process log files
    results = []
    start_time = time.time()
    
    try:
        if parallel and file_count > 1:
            # Process files in parallel
            print(f"🔄 Processing {file_count} files in parallel (max {max_workers} workers)...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_log_file, f, bot, logger) for f in log_files]
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
        else:
            # Process files sequentially
            print(f"🔄 Processing {file_count} files sequentially...")
            for file_path in log_files:
                results.append(process_log_file(file_path, bot, logger))
    except Exception as e:
        logger.error(f"Error during batch processing: {e}", exc_info=True)
        print(f"❌ Error during batch processing: {e}")
    
    # Calculate statistics
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = file_count - success_count
    
    # Generate summary statistics by error type and severity
    error_types = {}
    severities = {}
    
    for result in results:
        if result["status"] == "success":
            error_type = result.get("error_type", "Unknown")
            severity = result.get("severity", "UNKNOWN")
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
    
    # Generate summary
    summary = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "directory": log_dir,
        "recursive": recursive,
        "parallel_processing": parallel,
        "total_files": file_count,
        "successful": success_count,
        "failed": error_count,
        "success_rate": success_count / file_count if file_count > 0 else 0,
        "total_processing_time_seconds": total_time,
        "average_processing_time_seconds": total_time / file_count if file_count > 0 else 0,
        "error_types": error_types,
        "severities": severities,
        "results": results
    }
    
    # Print summary
    print(f"\n📊 Batch Analysis Summary:")
    print(f"  Directory: {log_dir}")
    print(f"  Total files processed: {file_count}")
    print(f"  Successfully analyzed: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"  Success rate: {(success_count / file_count * 100):.1f}%" if file_count > 0 else "N/A")
    print(f"  Total processing time: {total_time:.2f}s")
    
    if error_types:
        print("\n🔍 Error Types Detected:")
        for error_type, count in error_types.items():
            print(f"  - {error_type}: {count}")
    
    if severities:
        print("\n⚠️ Severity Distribution:")
        for severity, count in severities.items():
            print(f"  - {severity}: {count}")
    
    # Save report
    save_report(summary)
    
    return summary


def save_report(report: Dict[str, Any]) -> str:
    """
    Save batch analysis report to a file.
    
    Args:
        report: Batch analysis report
        
    Returns:
        Path to the saved report file
    """
    # Create reports directory if it doesn't exist
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Generate report filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"batch_analysis_report_{timestamp}.json"
    file_path = os.path.join(REPORT_DIR, filename)
    
    try:
        # Save report to file
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {file_path}")
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        # Try saving to current directory as fallback
        fallback_path = filename
        try:
            with open(fallback_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report saved to fallback location: {fallback_path}")
            file_path = fallback_path
        except Exception as inner_e:
            print(f"❌ Critical error: Could not save report anywhere: {inner_e}")
    
    return file_path


def main():
    """Main entry point for batch log analysis."""
    # Create reports directory at the start
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Configure argument parser
    parser = argparse.ArgumentParser(
        description="Semantic DevOps Bot - Batch Log Analyzer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--dir", "-d",
        required=True,
        help="Directory containing log files"
    )
    
    parser.add_argument(
        "--config", "-c",
        default=DEFAULT_CONFIG_PATH,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--create-issues", "-i",
        action="store_true",
        help="Create GitHub issues for errors"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively scan subdirectories for log files"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Process files in parallel"
    )
    
    parser.add_argument(
        "--max-workers", "-w",
        type=int,
        default=MAX_WORKERS,
        help="Maximum number of worker threads for parallel processing"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run batch analysis
    try:
        batch_analyze_logs(
            log_dir=args.dir,
            config_path=args.config,
            create_issues=args.create_issues,
            recursive=args.recursive,
            parallel=args.parallel,
            max_workers=args.max_workers
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        # Create a minimal report even on failure
        error_report = {
            "status": "critical_error",
            "message": f"Critical error in batch processing: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
            "args": vars(args)
        }
        save_report(error_report)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())