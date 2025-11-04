document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("job-form");
    const statusText = document.getElementById("status-text");
    const progressBar = document.getElementById("progress-bar");
    const resultsGrid = document.getElementById("results");
    const clearBtn = document.getElementById("clear-results");
    const errorsBox = document.getElementById("errors");

    let pollTimer = null;
    let activeJobId = null;
    const renderedResults = new Map();

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(form);

        disableForm(true);
        resetStatus("Submitting job...");
        clearErrors();

        fetch("/api/jobs", { method: "POST", body: formData })
            .then(async (response) => {
                let payload = null;
                try {
                    payload = await response.json();
                } catch (err) {
                    // ignore JSON parsing errors
                }
                if (!response.ok) {
                    const message =
                        (payload && (payload.error || payload.message)) ||
                        "Failed to create job.";
                    throw new Error(message);
                }
                return payload;
            })
            .then((payload) => {
                activeJobId = payload.job_id;
                startPolling(activeJobId);
            })
            .catch((error) => {
                console.error(error);
                setStatus("Failed to submit job.", 0);
                showErrors([error.message || "Unable to start job."]);
                disableForm(false);
            });
    });

    clearBtn.addEventListener("click", () => {
        stopPolling();
        activeJobId = null;
        renderedResults.clear();
        resultsGrid.innerHTML = "";
        clearErrors();
        resetStatus("Idle");
        disableForm(false);
    });

    function startPolling(jobId) {
        stopPolling();
        updateJob(jobId);
        pollTimer = setInterval(() => updateJob(jobId), 2000);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function updateJob(jobId) {
        fetch(`/api/jobs/${jobId}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to fetch job status");
                }
                return response.json();
            })
            .then((job) => {
                setStatus(job.message || job.status, job.progress || 0);
                renderErrors(job.errors || []);
                renderResults(jobId, job.results || []);

                if (job.status === "success" || job.status === "failed") {
                    stopPolling();
                    disableForm(false);
                }
            })
            .catch((error) => {
                console.error(error);
                showErrors(["Lost connection to the server."]);
                stopPolling();
                disableForm(false);
            });
    }

    function renderResults(jobId, results) {
        results.forEach((result) => {
            if (renderedResults.has(result.id)) {
                return;
            }
            const card = buildResultCard(jobId, result);
            resultsGrid.appendChild(card);
            renderedResults.set(result.id, card);
        });
    }

    function buildResultCard(jobId, result) {
        const card = document.createElement("article");
        card.className = "result-card";
        card.dataset.id = result.id;

        const image = document.createElement("img");
        image.src = result.thumbnail_url;
        image.alt = `${result.operation} output`;
        card.appendChild(image);

        const meta = document.createElement("div");
        meta.className = "result-meta";
        meta.innerHTML = `
            <strong>${result.operation.toUpperCase()}</strong>
            <span>Provider: ${result.provider || "N/A"}</span>
            <span>Source: ${result.source || "unknown"}</span>
            <span>Size: ${formatDimensions(result.width, result.height)}</span>
        `;
        card.appendChild(meta);

        const actions = document.createElement("div");
        actions.className = "result-actions";

        const viewLink = document.createElement("a");
        viewLink.href = result.image_url;
        viewLink.target = "_blank";
        viewLink.rel = "noopener";
        viewLink.textContent = "View";
        actions.appendChild(viewLink);

        const downloadLink = document.createElement("a");
        downloadLink.href = result.download_url;
        downloadLink.textContent = "Download";
        actions.appendChild(downloadLink);

        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.className = "danger";
        deleteBtn.textContent = "Delete";
        deleteBtn.addEventListener("click", () => {
            deleteResult(jobId, result.id, card);
        });
        actions.appendChild(deleteBtn);

        card.appendChild(actions);
        return card;
    }

    function deleteResult(jobId, resultId, card) {
        fetch(`/api/jobs/${jobId}/results/${resultId}`, { method: "DELETE" })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Request failed");
                }
                renderedResults.delete(resultId);
                card.remove();
            })
            .catch((error) => {
                console.error(error);
                showErrors(["Unable to delete file."]);
            });
    }

    function disableForm(disabled) {
        Array.from(form.elements).forEach((el) => {
            el.disabled = disabled;
        });
        clearBtn.disabled = false; // Always allow clearing the UI
    }

    function formatDimensions(width, height) {
        if (!width || !height) {
            return "unknown";
        }
        return `${width} x ${height}`;
    }

    function resetStatus(message) {
        setStatus(message, 0);
    }

    function setStatus(message, progress) {
        statusText.textContent = message;
        progressBar.style.width = `${progress}%`;
    }

    function renderErrors(messages) {
        if (!messages.length) {
            clearErrors();
            return;
        }
        showErrors(messages);
    }

    function showErrors(messages) {
        errorsBox.innerHTML = "";
        messages.forEach((msg) => {
            const line = document.createElement("div");
            line.textContent = msg;
            errorsBox.appendChild(line);
        });
    }

    function clearErrors() {
        errorsBox.innerHTML = "";
    }
});
