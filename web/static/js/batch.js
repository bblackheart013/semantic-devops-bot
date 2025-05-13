document.addEventListener("DOMContentLoaded", function () {
  const batchForm = document.getElementById("batch-form");
  const analyzeBtn = document.getElementById("analyze-btn");
  const spinner = document.getElementById("spinner");
  const batchResults = document.getElementById("batch-results");
  const summaryContent = document.getElementById("summary-content");
  const batchDetails = document.getElementById("batch-details");

  batchForm.addEventListener("submit", function (e) {
    e.preventDefault();

    // Check if files are selected
    const fileInput = document.getElementById("log-files");
    if (fileInput.files.length === 0) {
      alert("Please select at least one log file to analyze");
      return;
    }

    // Show loading state
    analyzeBtn.disabled = true;
    spinner.classList.remove("d-none");
    batchResults.classList.add("d-none");

    // Get form data
    const formData = new FormData(batchForm);

    // Send API request
    fetch("/api/batch-analyze", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        // Display results
        displayBatchResults(data);

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("d-none");
        batchResults.classList.remove("d-none");
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred during batch analysis: " + error.message);

        // Reset loading state
        analyzeBtn.disabled = false;
        spinner.classList.add("d-none");
      });
  });

  function displayBatchResults(data) {
    // Display summary information
    let successCount = 0;
    data.results.forEach((result) => {
      if (result.status === "success" || result.status === "routed") {
        successCount++;
      }
    });

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

    window.batchErrorChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: Object.keys(data.error_types),
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
        },
        plugins: {
          legend: {
            display: false,
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
                <td>${result.filename}</td>
                <td>${analysis.error_summary || "Unknown"}</td>
                <td><span class="badge bg-${severityClass}">${severity}</span></td>
                <td>${result.status || "Unknown"}</td>
                <td>
                    <button class="btn btn-sm btn-primary view-details-btn" data-index="${index}">
                        View Details
                    </button>
                </td>
            `;
      batchDetails.appendChild(row);
    });

    // Add event listeners for "View Details" buttons
    document.querySelectorAll(".view-details-btn").forEach((button, index) => {
      button.addEventListener("click", function () {
        showResultDetails(data.results[index]);
      });
    });
  }

  function showResultDetails(result) {
    // Create a modal to show detailed analysis
    const modal = document.createElement("div");
    modal.className = "modal fade";
    modal.id = "detailsModal";
    modal.setAttribute("tabindex", "-1");

    const analysis = result.analysis || {};

    // Determine severity class
    let severityClass = "severity-medium";
    if (
      analysis.severity_level === "HIGH" ||
      analysis.severity_level === "CRITICAL"
    ) {
      severityClass = "severity-high";
    } else if (analysis.severity_level === "LOW") {
      severityClass = "severity-low";
    }

    modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Analysis Details: ${
                          result.filename
                        }</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <h5>Error Summary</h5>
                        <p>${
                          analysis.error_summary || "No summary available"
                        }</p>
                        
                        <h5>Root Cause</h5>
                        <p>${
                          analysis.root_cause || "No root cause identified"
                        }</p>
                        
                        <h5>Severity</h5>
                        <p class="${severityClass}">${
      analysis.severity || "Unknown"
    }</p>
                        
                        <h5>Recommended Solution</h5>
                        <p>${
                          analysis.recommended_solution ||
                          "No solution available"
                        }</p>
                        
                        <h5>Prevention</h5>
                        <p>${
                          analysis.prevention || "No prevention steps provided"
                        }</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;

    document.body.appendChild(modal);

    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();

    // Remove the modal from DOM when hidden
    modal.addEventListener("hidden.bs.modal", function () {
      modal.remove();
    });
  }
});
