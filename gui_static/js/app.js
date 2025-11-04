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

        const reviseBtn = document.createElement("button");
        reviseBtn.type = "button";
        reviseBtn.className = "revise";
        reviseBtn.textContent = "Revise";
        reviseBtn.addEventListener("click", () => {
            showReviseModal(jobId, result.id);
        });
        actions.appendChild(reviseBtn);

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

    function showReviseModal(jobId, resultId) {
        // Create modal overlay
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        
        // Create modal content
        const modal = document.createElement("div");
        modal.className = "modal";
        
        const title = document.createElement("h2");
        title.textContent = "Revise Image";
        modal.appendChild(title);
        
        const description = document.createElement("p");
        description.textContent = "Describe how you'd like to modify this image:";
        description.className = "modal-description";
        modal.appendChild(description);
        
        const input = document.createElement("textarea");
        input.id = "revise-prompt";
        input.placeholder = "e.g., make it brighter, add more contrast, change the background to blue...";
        input.rows = 4;
        modal.appendChild(input);
        
        const buttonContainer = document.createElement("div");
        buttonContainer.className = "modal-actions";
        
        // Close handler function
        const closeModal = () => {
            if (overlay.parentNode) {
                document.body.removeChild(overlay);
            }
            document.removeEventListener("keydown", escapeHandler);
        };
        
        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.textContent = "Cancel";
        cancelBtn.className = "secondary";
        cancelBtn.addEventListener("click", closeModal);
        buttonContainer.appendChild(cancelBtn);
        
        const submitBtn = document.createElement("button");
        submitBtn.type = "button";
        submitBtn.textContent = "Revise";
        submitBtn.addEventListener("click", () => {
            const prompt = input.value.trim();
            if (!prompt) {
                alert("Please enter a revision prompt.");
                return;
            }
            submitRevision(jobId, resultId, prompt, overlay);
            document.removeEventListener("keydown", escapeHandler);
        });
        buttonContainer.appendChild(submitBtn);
        
        modal.appendChild(buttonContainer);
        overlay.appendChild(modal);
        
        // Close on overlay click
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                closeModal();
            }
        });
        
        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === "Escape") {
                closeModal();
            }
        };
        document.addEventListener("keydown", escapeHandler);
        
        document.body.appendChild(overlay);
        input.focus();
    }

    function submitRevision(jobId, resultId, prompt, modalOverlay) {
        fetch(`/api/jobs/${jobId}/results/${resultId}/revise`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ prompt }),
        })
            .then(async (response) => {
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.error || "Failed to create revision job.");
                }
                return payload;
            })
            .then((payload) => {
                if (modalOverlay.parentNode) {
                    document.body.removeChild(modalOverlay);
                }
                // Start polling the new job
                activeJobId = payload.job_id;
                startPolling(activeJobId);
                resetStatus("Starting revision...");
            })
            .catch((error) => {
                console.error(error);
                showErrors([error.message || "Unable to start revision."]);
            });
    }
});
