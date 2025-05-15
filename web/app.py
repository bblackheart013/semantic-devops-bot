from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import sys
import json
import logging
import re
from datetime import datetime

# Add project root to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your existing code
try:
    from main import DevOpsBot, setup_logging, create_llm_config
    from agents.coordinator_agent import CoordinatorAgent
    from agents.analyzer_agent import AnalyzerAgent
    from agents.agent_router import AgentRouter
    imports_successful = True
except ImportError as e:
    print(f"Error importing project modules: {e}")
    imports_successful = False
    # Fallback setup if imports fail
    def setup_logging():
        logger = logging.getLogger("web_app")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Set up basic config
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-for-testing')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Configure logging and initialize DevOps Bot
logger = setup_logging()
logger.info("Starting Semantic DevOps Bot Web Application")

# Initialize the DevOps Bot with error handling
try:
    if imports_successful:
        bot = DevOpsBot()
        logger.info("DevOps Bot initialized successfully")
    else:
        bot = None
        logger.warning("DevOps Bot initialization skipped due to import errors")
except Exception as e:
    logger.error(f"Failed to initialize DevOpsBot: {e}")
    bot = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/batch')
def batch_analysis():
    return render_template('batch.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    try:
        # First, check if log text was provided
        log_text = request.form.get('log_text', '')
        
        # If text is provided, use that
        if log_text.strip():
            log_content = log_text
            logger.info(f"Using provided log text: {log_content[:50]}...")
        # Otherwise, try to get a file
        elif 'log_file' in request.files:
            log_file = request.files['log_file']
            if log_file.filename == '':
                return jsonify({'error': 'No content provided - please either upload a file or enter log text'}), 400
            try:
                log_content = log_file.read().decode('utf-8')
                logger.info(f"Using uploaded file: {log_file.filename}")
            except UnicodeDecodeError:
                return jsonify({'error': 'File encoding not supported. Please use UTF-8 encoded text files.'}), 400
        else:
            return jsonify({'error': 'No content provided - please either upload a file or enter log text'}), 400
        
        # Process the log content
        if not log_content:
            return jsonify({'error': 'Empty log content'}), 400
        
        # Check if GitHub issue creation is requested
        create_issue = request.form.get('create_issue') == 'on'
        
        # Use the DevOpsBot to analyze the log
        if bot:
            result = bot.analyze_log(log_content)
            
            # If GitHub issue creation is requested
            if create_issue:
                try:
                    from tools.github_issue_tool import create_github_issue
                    github_token = os.getenv("GITHUB_TOKEN")
                    repo_owner = os.getenv("GITHUB_REPO_OWNER")
                    repo_name = os.getenv("GITHUB_REPO_NAME")
                    
                    if github_token and repo_owner and repo_name:
                        issue_result = create_github_issue(
                            issue_details=result.get('analysis', {}),
                            repo_owner=repo_owner,
                            repo_name=repo_name,
                            github_token=github_token
                        )
                        # Add GitHub issue URL to result
                        if isinstance(issue_result, str) and "created" in issue_result:
                            # Extract the URL if it's in the result
                            url_match = re.search(r'https://github\.com/[^\s]+', issue_result)
                            if url_match:
                                result['github_issue_url'] = url_match.group(0)
                except Exception as e:
                    logger.error(f"Failed to create GitHub issue: {e}")
                    result['github_issue_error'] = str(e)
            
            logger.info(f"Analysis successful: {str(result)[:100]}...")
            return jsonify(result)
        else:
            # If bot initialization failed, use mock data
            logger.warning("Bot not initialized, using mock data")
            mock_result = {
                "status": "mock",
                "analysis": {
                    "error_summary": "ModuleNotFoundError: No module named 'requests'",
                    "root_cause": "The Python script is trying to import the 'requests' library, but it's not installed in the current environment",
                    "severity": "Medium - Application cannot run without this dependency",
                    "severity_level": "MEDIUM",
                    "recommended_solution": "Install the missing package using pip:\n\npip install requests",
                    "prevention": "Use requirements.txt to document dependencies and virtual environments to isolate project dependencies"
                }
            }
            return jsonify(mock_result)
            
    except Exception as e:
        logger.error(f"Request handling error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        'status': 'success',
        'message': 'API is working correctly',
        'time': datetime.now().isoformat()
    })

@app.route('/api/analyze-mock', methods=['POST'])
def analyze_log_mock():
    """A simple mock analyzer that always returns success"""
    try:
        # Get log content from request
        if 'log_file' in request.files:
            log_file = request.files['log_file']
            log_content = log_file.read().decode('utf-8')
        else:
            log_content = request.form.get('log_text', '')
        
        # Create a simple mock response
        mock_response = {
            'status': 'success',
            'specialist': 'MockAnalyzer',
            'error_type': 'mock_error',
            'analysis': {
                'error_summary': 'This is a mock analysis',
                'root_cause': f'You entered: {log_content[:50]}...',
                'severity': 'MEDIUM',
                'severity_level': 'MEDIUM',
                'recommended_solution': 'This is a mock solution',
                'prevention': 'This is mock prevention advice'
            }
        }
        
        return jsonify(mock_response)
            
    except Exception as e:
        logger.error(f"Error in mock analyzer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    try:
        files = request.files.getlist('log_files')
        create_issues = request.form.get('create_issues') == 'on'
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No log files provided'}), 400
        
        # Process each file
        results = []
        error_types = {}
        severities = {}
        
        for i, file in enumerate(files):
            try:
                log_content = file.read().decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"Skipping file {file.filename} due to encoding issues")
                continue
                
            filename = file.filename
            
            # Analyze the log
            if bot:
                result = bot.analyze_log(log_content)
                result['filename'] = filename
                result['index'] = i
                results.append(result)
                
                # Update summary stats
                analysis = result.get('analysis', {})
                error_type = analysis.get('error_summary', 'Unknown')
                severity = analysis.get('severity_level', 'UNKNOWN')
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
                severities[severity] = severities.get(severity, 0) + 1
            else:
                # Use mock data if bot is not initialized
                mock_result = {
                    "status": "mock",
                    "filename": filename,
                    "index": i,
                    "analysis": {
                        "error_summary": "ModuleNotFoundError: No module named 'requests'",
                        "root_cause": "The Python script is trying to import the 'requests' library, but it's not installed",
                        "severity": "Medium - Application cannot run without this dependency",
                        "severity_level": "MEDIUM",
                        "recommended_solution": "Install the missing package using pip install requests",
                        "prevention": "Use requirements.txt to document dependencies"
                    }
                }
                results.append(mock_result)
                
                # Update summary stats with mock data
                error_types["ModuleNotFoundError"] = error_types.get("ModuleNotFoundError", 0) + 1
                severities["MEDIUM"] = severities.get("MEDIUM", 0) + 1
        
        # Prepare response
        response = {
            'total_files': len(results),
            'results': results,
            'error_types': error_types,
            'severities': severities,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save results to reports directory
        os.makedirs('reports', exist_ok=True)
        report_filename = f"reports/web_batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Batch analysis completed for {len(results)} files, saved to {report_filename}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'bot_initialized': bot is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    
    print(f"Starting Semantic DevOps Bot Web Interface on port {port}")
    print(f"Debug mode: {'ON' if debug else 'OFF'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)