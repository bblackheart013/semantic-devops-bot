// Enhanced batch.js with improved error handling

document.addEventListener("DOMContentLoaded", function () {
  const batchForm = document.getElementById("batch-form");
  const analyzeBtn = document.getElementById("analyze-btn");
  const spinner = document.getElementById("spinner");
  const batchResults = document.getElementById("batch-results");
  const summaryContent = document.getElementById("summary-content");
  const batchDetails = document.getElementById("batch-details");

  // Add health check on page load
  checkApiHealth();

  batchForm.addEventListener("submit", function (e) {
    e.preventDefault();

    // Check if files are selected
    const fileInput = document.getElementById("log-files");
    if (fileInput.files.length === 0) {
      showAlert("Please select at least one log file to analyze", "warning");
      return;
    }

    // Show loading state
    analyzeBtn.disabled = true;
    spinner.classList.remove("hidden");
    batchResults.classList.add("hidden");

    // Get form data
    const formData = new FormData(batchForm);

    // Send API request
    fetch("/api/batch-analyze", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          // Try to get error message from response
          return response
            .json()
            .then((data) => {
              throw new Error(
                data.error || `Network error: ${response.status}`
              );
            })
            .catch((err) => {
              if (err instanceof SyntaxError) {
                throw new Error(`Network error: ${response.status}`);
              }
              throw err;
            });
        }
        return response.json();
      })
      .then((data) => {
        console.log("Batch analysis results:", data);

        // Check if any results were returned
        if (!data.results || data.results.length === 0) {
          showAlert(
            "No analysis results were returned. Please try again.",
            "warning"
          );
          resetForm();
          return;
        }

        // Display results
        displayBatchResults(data);

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("hidden");
        batchResults.classList.remove("hidden");
      })
      .catch((error) => {
        console.error("Error:", error);
        showAlert(
          "An error occurred during batch analysis: " + error.message,
          "error"
        );

        // Reset loading state
        resetForm();
      });
  });

  function resetForm() {
    analyzeBtn.disabled = false;
    spinner.classList.add("hidden");
  }

  function displayBatchResults(data) {
    // Display summary information
    let successCount = 0;
    data.results.forEach((result) => {
      if (
        result.status === "success" ||
        result.status === "routed" ||
        result.status === "mock"
      ) {
        successCount++;
      }
    });

    // Check if this is mock data
    const isMockData = data.results.some((result) => result.status === "mock");
    if (isMockData) {
      showAlert(
        "Using mock analysis data for some or all files. The AI service may be unavailable.",
        "info"
      );
    }

    summaryContent.innerHTML = `
            <p><strong>Total Files:</strong> ${data.total_files}</p>
            <p><strong>Successfully Analyzed:</strong> ${successCount}</p>
            <p><strong>Failed:</strong> ${data.total_files - successCount}</p>
            <p><strong>Error Types Found:</strong> ${
              Object.keys(data.error_types).length
            }</p>
        `;

    // Create error distribution chart
    const ctx = document.getElementById("batch-error-chart").getContext("2d");

    // Destroy existing chart if it exists
    if (window.batchErrorChart) {
      window.batchErrorChart.destroy();
    }

    // Format chart labels for better display (shorten very long error types)
    const formattedLabels = Object.keys(data.error_types).map((label) =>
      label.length > 25 ? label.substring(0, 25) + "..." : label
    );

    window.batchErrorChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: formattedLabels,
        datasets: [
          {
            label: "Error Count",
            data: Object.values(data.error_types),
            backgroundColor: "rgba(54, 162, 235, 0.7)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
            },
          },
          x: {
            ticks: {
              autoSkip: false,
              maxRotation: 90,
              minRotation: 45,
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              title: function (tooltipItems) {
                // Show the full label in tooltip
                const index = tooltipItems[0].dataIndex;
                return Object.keys(data.error_types)[index];
              },
            },
          },
        },
      },
    });

    // Display detailed results
    batchDetails.innerHTML = "";
    data.results.forEach((result, index) => {
      const analysis = result.analysis || {};
      const severity = analysis.severity_level || "UNKNOWN";

      // Determine severity class
      let severityClass = "secondary";
      if (severity === "HIGH" || severity === "CRITICAL") {
        severityClass = "danger";
      } else if (severity === "MEDIUM") {
        severityClass = "warning";
      } else if (severity === "LOW") {
        severityClass = "success";
      }

      const row = document.createElement("tr");
      row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-800 dark:text-gray-200">${
                  result.filename
                }</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">${
                  analysis.error_summary || "Unknown"
                }</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span class="px-2 py-1 text-xs font-semibold rounded-full 
                  ${
                    severityClass === "danger"
                      ? "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100"
                      : ""
                  }
                  ${
                    severityClass === "warning"
                      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100"
                      : ""
                  }
                  ${
                    severityClass === "success"
                      ? "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100"
                      : ""
                  }
                  ${
                    severityClass === "secondary"
                      ? "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                      : ""
                  }
                  ">${severity}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">${
                  result.status || "Unknown"
                }</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <button class="bg-primary hover:bg-primary-hover text-white py-1 px-3 rounded view-details-btn" data-index="${index}">
                        View Details
                    </button>
                </td>
            `;
      batchDetails.appendChild(row);
    });

    // Add event listeners for "View Details" buttons
    document.querySelectorAll(".view-details-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const index = parseInt(this.getAttribute("data-index"));
        showResultDetails(data.results[index]);
      });
    });
  }

  function showResultDetails(result) {
    // Create a modal to show detailed analysis
    const modal = document.createElement("div");
    modal.className =
      "fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50";

    const analysis = result.analysis || {};

    // Determine severity class
    let severityClass = "text-yellow-600 dark:text-yellow-400";
    if (
      analysis.severity_level === "HIGH" ||
      analysis.severity_level === "CRITICAL"
    ) {
      severityClass = "text-red-600 dark:text-red-400 font-bold";
    } else if (analysis.severity_level === "LOW") {
      severityClass = "text-green-600 dark:text-green-400";
    }

    // Process solution text for code blocks
    let solution = analysis.recommended_solution || "No solution available";
    solution = solution.replace(
      /```([a-z]*)\n([\s\S]*?)\n```/g,
      '<pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg my-3 font-mono text-sm overflow-x-auto">$2</pre>'
    );
    solution = solution.replace(
      /`([^`]+)`/g,
      '<code class="bg-gray-100 dark:bg-gray-900 px-1 py-0.5 rounded font-mono text-sm">$1</code>'
    );
    solution = solution.replace(/\n/g, "<br>");

    modal.innerHTML = `
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden max-w-2xl w-full mx-4">
          <div class="bg-primary text-white px-4 py-3 flex justify-between items-center">
              <h3 class="text-lg font-semibold">Analysis Details: ${
                result.filename
              }</h3>
              <button class="text-white hover:text-gray-200 focus:outline-none close-modal">
                  <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
              </button>
          </div>
          <div class="p-6 max-h-[80vh] overflow-y-auto">
              <div class="mb-4">
                  <h4 class="text-lg font-medium text-gray-800 dark:text-white mb-2">Error Summary</h4>
                  <p class="text-gray-700 dark:text-gray-300">${
                    analysis.error_summary || "No summary available"
                  }</p>
              </div>
              
              <div class="mb-4">
                  <h4 class="text-lg font-medium text-gray-800 dark:text-white mb-2">Root Cause</h4>
                  <p class="text-gray-700 dark:text-gray-300">${
                    analysis.root_cause || "No root cause identified"
                  }</p>
              </div>
              
              <div class="mb-4">
                  <h4 class="text-lg font-medium text-gray-800 dark:text-white mb-2">Severity</h4>
                  <p class="${severityClass}">${
      analysis.severity || "Unknown"
    }</p>
              </div>
              
              <div class="mb-4">
                  <h4 class="text-lg font-medium text-gray-800 dark:text-white mb-2">Recommended Solution</h4>
                  <div class="text-gray-700 dark:text-gray-300">${solution}</div>
              </div>
              
              <div class="mb-4">
                  <h4 class="text-lg font-medium text-gray-800 dark:text-white mb-2">Prevention</h4>
                  <p class="text-gray-700 dark:text-gray-300">${
                    analysis.prevention || "No prevention steps provided"
                  }</p>
              </div>
          </div>
          <div class="bg-gray-100 dark:bg-gray-700 px-4 py-3 flex justify-end">
              <button class="bg-primary hover:bg-primary-hover text-white font-medium py-2 px-4 rounded-lg close-modal">
                  Close
              </button>
          </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Add event listeners to close buttons
    modal.querySelectorAll(".close-modal").forEach((button) => {
      button.addEventListener("click", function () {
        modal.remove();
      });
    });

    // Close when clicking outside the modal content
    modal.addEventListener("click", function (e) {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }

  function showAlert(message, type = "error") {
    // Create alert element
    const alertElement = document.createElement("div");

    // Set appropriate classes based on type
    let alertClass =
      "bg-red-100 border-red-500 text-red-700 dark:bg-red-900 dark:text-red-200";
    if (type === "warning") {
      alertClass =
        "bg-yellow-100 border-yellow-500 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200";
    } else if (type === "info") {
      alertClass =
        "bg-blue-100 border-blue-500 text-blue-700 dark:bg-blue-900 dark:text-blue-200";
    }

    alertElement.className = `${alertClass} border-l-4 p-4 mb-4 rounded`;
    alertElement.innerHTML = `
      <div class="flex items-center">
        <div class="py-1">
          <svg class="w-6 h-6 mr-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <p>${message}</p>
        </div>
      </div>
    `;

    // Insert before the form
    batchForm.parentNode.insertBefore(alertElement, batchForm);

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
});
