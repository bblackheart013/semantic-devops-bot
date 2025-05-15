document.addEventListener("DOMContentLoaded", function () {
  // Sample data - in a real app, you would fetch this from your backend
  const errorTypeData = {
    ModuleNotFoundError: 12,
    "Docker Authentication Error": 8,
    "Azure Resource Not Found": 5,
    "Kubernetes CrashLoopBackOff": 3,
    "Other Errors": 6,
  };

  const severityData = {
    HIGH: 10,
    MEDIUM: 18,
    LOW: 6,
  };

  // Create error type chart
  const errorTypeCtx = document
    .getElementById("error-type-chart")
    .getContext("2d");
  const errorTypeChart = new Chart(errorTypeCtx, {
    type: "bar",
    data: {
      labels: Object.keys(errorTypeData),
      datasets: [
        {
          label: "Error Count",
          data: Object.values(errorTypeData),
          backgroundColor: [
            "rgba(54, 162, 235, 0.7)",
            "rgba(255, 99, 132, 0.7)",
            "rgba(255, 206, 86, 0.7)",
            "rgba(75, 192, 192, 0.7)",
            "rgba(153, 102, 255, 0.7)",
          ],
          borderColor: [
            "rgba(54, 162, 235, 1)",
            "rgba(255, 99, 132, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
          ],
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

  // Create severity chart
  const severityCtx = document
    .getElementById("severity-chart")
    .getContext("2d");
  const severityChart = new Chart(severityCtx, {
    type: "doughnut",
    data: {
      labels: Object.keys(severityData),
      datasets: [
        {
          data: Object.values(severityData),
          backgroundColor: [
            "rgba(255, 99, 132, 0.7)",
            "rgba(255, 206, 86, 0.7)",
            "rgba(75, 192, 192, 0.7)",
          ],
          borderColor: [
            "rgba(255, 99, 132, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });

  // In a real app, you would implement fetching real data from the backend
  // And update the charts and table with that data
});
