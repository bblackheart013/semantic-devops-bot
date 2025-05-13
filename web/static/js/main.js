// Enhanced main.js with improved error handling and UI feedback

document.addEventListener("DOMContentLoaded", function () {
  const logForm = document.getElementById("log-form");
  const analyzeBtn = document.getElementById("analyze-btn");
  const spinner = document.getElementById("spinner");
  const resultsSection = document.getElementById("analysis-results");
  const resultsContent = document.getElementById("results-content");

  // Add health check on page load to ensure API is available
  checkApiHealth();

  logForm.addEventListener("submit", function (e) {
    e.preventDefault();

    // Validate that at least one input type has data
    const logFile = document.getElementById("log-file").files[0];
    const logText = document.getElementById("log-text").value.trim();

    if (!logFile && !logText) {
      showAlert("Please either upload a log file or paste log text", "warning");
      return;
    }

    // Show loading state
    analyzeBtn.disabled = true;
    spinner.classList.remove("hidden");
    resultsSection.classList.add("hidden");

    // Get form data
    const formData = new FormData(logForm);

    // Send API request
    fetch("/api/analyze", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          // Log details for debugging
          console.error("Response status:", response.status);
          console.error("Response status text:", response.statusText);

          // Extract error details if possible
          return response
            .json()
            .then((data) => {
              throw new Error(data.error || "Server error: " + response.status);
            })
            .catch((err) => {
              if (err instanceof SyntaxError) {
                throw new Error("Server error: " + response.status);
              }
              throw err;
            });
        }
        return response.json();
      })
      .then((data) => {
        console.log("Analysis result:", data);

        // Check if we got mock data
        if (data.status === "mock") {
          showAlert(
            "Using mock analysis data. The AI service may be unavailable.",
            "info"
          );
        }

        // Display results
        displayResults(data);

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("hidden");
        resultsSection.classList.remove("hidden");
      })
      .catch((error) => {
        console.error("Error:", error);

        resultsContent.innerHTML = `
              <div class="bg-red-100 dark:bg-red-900 border-l-4 border-red-500 text-red-700 dark:text-red-200 p-4 mb-4">
                  <h3 class="font-bold">Error</h3>
                  <p>${error.message || "An error occurred during analysis"}</p>
              </div>
              <div class="mt-4">
                <p class="text-gray-700 dark:text-gray-300">Try using the mock analysis endpoint instead:</p>
                <button id="try-mock" class="mt-2 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700">
                  Try Mock Analysis
                </button>
              </div>
          `;

        // Add event listener to the try-mock button
        document
          .getElementById("try-mock")
          .addEventListener("click", function () {
            useMockAnalyzer();
          });

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("hidden");
        resultsSection.classList.remove("hidden");
      });
  });

  function displayResults(data) {
    // Get the analysis data
    const analysis = data.analysis || {};

    // Determine severity class
    let severityColor = "text-yellow-600 dark:text-yellow-400";
    if (
      analysis.severity_level === "HIGH" ||
      analysis.severity_level === "CRITICAL"
    ) {
      severityColor = "text-red-600 dark:text-red-400 font-bold";
    } else if (analysis.severity_level === "LOW") {
      severityColor = "text-green-600 dark:text-green-400";
    }

    // Process code snippets or commands with syntax highlighting
    const solution = analysis.recommended_solution || "No solution available";
    const processedSolution = processSolutionText(solution);

    // Build the results HTML
    let html = `
          <div class="bg-blue-100 dark:bg-blue-900 border-l-4 border-blue-500 text-blue-700 dark:text-blue-200 p-4 mb-6">
              <p class="font-bold">Analysis completed successfully.</p>
              ${
                data.specialist
                  ? `<p>Specialist agent: ${data.specialist}</p>`
                  : ""
              }
              ${data.source ? `<p>Analysis source: ${data.source}</p>` : ""}
          </div>
          
          <div class="mb-5">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Error Summary</h3>
              <p class="text-gray-700 dark:text-gray-300">${
                analysis.error_summary || "No summary available"
              }</p>
          </div>
          
          <div class="mb-5">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Root Cause</h3>
              <p class="text-gray-700 dark:text-gray-300">${
                analysis.root_cause || "No root cause identified"
              }</p>
          </div>
          
          <div class="mb-5">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Severity</h3>
              <p class="${severityColor}">${analysis.severity || "Unknown"}</p>
          </div>
          
          <div class="mb-5">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Recommended Solution</h3>
              <div class="text-gray-700 dark:text-gray-300">${processedSolution}</div>
          </div>
          
          <div class="mb-5">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Prevention</h3>
              <p class="text-gray-700 dark:text-gray-300">${
                analysis.prevention || "No prevention steps provided"
              }</p>
          </div>
      `;

    // Add GitHub issue information if available
    if (data.github_issue_url) {
      html += `
              <div class="bg-green-100 dark:bg-green-900 border-l-4 border-green-500 text-green-700 dark:text-green-200 p-4 mt-6">
                  <h3 class="font-bold">GitHub Issue Created</h3>
                  <p>A GitHub issue has been created for this error.</p>
                  <a href="${data.github_issue_url}" target="_blank" class="mt-2 inline-block bg-green-600 text-white py-1 px-3 rounded-lg hover:bg-green-700 transition duration-200">
                      View GitHub Issue
                  </a>
              </div>
          `;
    }

    // Add GitHub issue error if present
    if (data.github_issue_error) {
      html += `
              <div class="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 text-yellow-700 dark:text-yellow-200 p-4 mt-6">
                  <h3 class="font-bold">GitHub Issue Creation Failed</h3>
                  <p>${data.github_issue_error}</p>
              </div>
          `;
    }

    // Update results content
    resultsContent.innerHTML = html;
  }

  function processSolutionText(solution) {
    // Look for code blocks indicated by backticks or indentation
    let processed = solution;

    // Replace markdown-style code blocks with HTML
    processed = processed.replace(
      /```([a-z]*)\n([\s\S]*?)\n```/g,
      '<pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg my-3 font-mono text-sm overflow-x-auto">$2</pre>'
    );

    // Replace inline code with HTML
    processed = processed.replace(
      /`([^`]+)`/g,
      '<code class="bg-gray-100 dark:bg-gray-900 px-1 py-0.5 rounded font-mono text-sm">$1</code>'
    );

    // Replace newlines with <br> tags
    processed = processed.replace(/\n/g, "<br>");

    return processed;
  }

  function showAlert(message, type = "error") {
    // Create alert element
    const alertElement = document.createElement("div");

    // Set appropriate classes based on type
    let alertClass = "bg-red-100 border-red-500 text-red-700";
    if (type === "warning") {
      alertClass = "bg-yellow-100 border-yellow-500 text-yellow-700";
    } else if (type === "info") {
      alertClass = "bg-blue-100 border-blue-500 text-blue-700";
    }

    alertElement.className = `${alertClass} border-l-4 p-4 mb-4 rounded`;
    alertElement.innerHTML = `
        <div class="flex items-center">
            <div class="py-1"><svg class="w-6 h-6 mr-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg></div>
            <div>
                <p>${message}</p>
            </div>
        </div>
    `;

    // Insert after the form
    logForm.parentNode.insertBefore(alertElement, logForm.nextSibling);

    // Remove after 5 seconds
    setTimeout(() => {
      alertElement.remove();
    }, 5000);
  }

  function checkApiHealth() {
    // Check if the API is available
    fetch("/api/test")
      .then((response) => {
        if (!response.ok) {
          throw new Error("API health check failed");
        }
        return response.json();
      })
      .then((data) => {
        console.log("API health check passed:", data);
      })
      .catch((error) => {
        console.error("API health check failed:", error);
        showAlert(
          "Warning: The API might be unavailable. Some features may not work correctly.",
          "warning"
        );
      });
  }

  function useMockAnalyzer() {
    // Get form data
    const formData = new FormData(logForm);

    // Show loading state
    analyzeBtn.disabled = true;
    spinner.classList.remove("hidden");
    resultsSection.classList.add("hidden");

    // Call the mock analyzer endpoint
    fetch("/api/analyze-mock", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Server error: " + response.status);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Mock analysis result:", data);
        displayResults(data);

        // Show a notice that this is mock data
        showAlert(
          "Using mock analysis - real AI analysis is currently unavailable",
          "info"
        );

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("hidden");
        resultsSection.classList.remove("hidden");
      })
      .catch((error) => {
        console.error("Mock analysis error:", error);
        showAlert(
          "Even mock analysis failed. The server might be down.",
          "error"
        );

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("hidden");
      });
  }
});
