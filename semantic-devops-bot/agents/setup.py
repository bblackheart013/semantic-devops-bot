from setuptools import setup, find_packages

setup(
    name="semantic-devops-bot",
    version="1.0.0",
    description="AI-powered DevOps error analysis tool with multi-agent collaboration",
    author="DevOps Bot Team",
    author_email="dev@example.com",
    url="https://github.com/bblackheart013/semantic-devops-bot",
    packages=find_packages(),
    install_requires=[
        "autogen-agentchat>=0.2.0",
        "openai>=1.0.0",
        "colorama>=0.4.4",
        "python-dotenv>=0.19.0",
        "PyGithub>=1.55",
    ],
    entry_points={
        'console_scripts': [
            'devops-bot=coordinator_agent:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: DevOps",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.10",
    long_description="""
    # Semantic DevOps Bot

    A next-generation AI DevOps assistant that intelligently analyzes error logs, 
    recommends precise fixes, and can file GitHub issues on your behalf — now 
    supercharged with Microsoft AutoGen for seamless multi-agent collaboration.

    ## Key Features

    - AI-Powered Log Analysis: Detects and interprets common build, deployment, and cloud errors
    - Multi-Agent Collaboration: Uses AutoGen to coordinate multiple specialized agents
    - Intelligent Routing: Delegates log analysis to the right expert agent based on context
    - Error-to-Issue Automation: Automatically generates GitHub issues with fix suggestions

    ## Usage

    ```bash
    # Analyze a log file
    devops-bot analyze --log-file errors.log

    # Direct log text analysis
    devops-bot analyze --log-text "ModuleNotFoundError: No module named 'requests'"

    # Get a list of registered specialist agents
    devops-bot list-agents
    ```

    For more information, visit the GitHub repository.
    """,
    long_description_content_type="text/markdown",
)