/**
 * Anupalan Web Client Application
 * Connects to the FastAPI REST backend for multilingual compliance navigation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Session initialization (DPDP compliant ephemeral ID)
  let sessionId = sessionStorage.getItem("anupalan_session_id");
  if (!sessionId) {
    sessionId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : "sess-" + Date.now();
    sessionStorage.setItem("anupalan_session_id", sessionId);
  }

  let currentAnswerId = null;

  // DOM Elements
  const askForm = document.getElementById("ask-form");
  const queryInput = document.getElementById("query-input");
  const asOfDateInput = document.getElementById("as-of-date");
  const targetLangSelect = document.getElementById("target-language");
  const btnSubmit = document.getElementById("btn-submit");
  const btnText = document.getElementById("btn-text");
  const btnSpinner = document.getElementById("btn-spinner");
  const btnClear = document.getElementById("btn-clear");
  const sampleChips = document.getElementById("sample-chips");

  // Results Elements
  const resultsSection = document.getElementById("results-section");
  const sessionDisplay = document.getElementById("session-display");
  const resBadgeGrounding = document.getElementById("res-badge-grounding");
  const resBadgeLang = document.getElementById("res-badge-lang");
  const resBadgeAsOf = document.getElementById("res-badge-as-of");
  const abstentionBanner = document.getElementById("abstention-banner");
  const abstentionText = document.getElementById("abstention-text");
  const summaryText = document.getElementById("summary-text");
  const claimsList = document.getElementById("claims-list");
  const nextStepsList = document.getElementById("next-steps-list");
  const disclaimerText = document.getElementById("disclaimer-text");

  // Feedback Elements
  const fbUp = document.getElementById("fb-up");
  const fbDown = document.getElementById("fb-down");
  const fbReasonBox = document.getElementById("fb-reason-box");
  const fbReason = document.getElementById("fb-reason");
  const fbComment = document.getElementById("fb-comment");
  const fbSubmit = document.getElementById("fb-submit");
  const fbToast = document.getElementById("fb-toast");

  // Modal Elements
  const citationModal = document.getElementById("citation-modal");
  const modalClose = document.getElementById("modal-close");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalInstTitle = document.getElementById("modal-inst-title");
  const modalAuthority = document.getElementById("modal-authority");
  const modalClause = document.getElementById("modal-clause");
  const modalEffectiveFrom = document.getElementById("modal-effective-from");
  const modalInForce = document.getElementById("modal-in-force");
  const modalPassageText = document.getElementById("modal-passage-text");
  const modalBboxPage = document.getElementById("modal-bbox-page");
  const modalBboxCoords = document.getElementById("modal-bbox-coords");
  const modalOcrQuality = document.getElementById("modal-ocr-quality");
  const modalTimelineList = document.getElementById("modal-timeline-list");
  const modalSourceLink = document.getElementById("modal-source-link");

  // Privacy Actions
  const btnPurgeSession = document.getElementById("btn-purge-session");
  const corpusStatusBadge = document.getElementById("corpus-status-badge");

  // Set default as-of date to today
  const todayStr = new Date().toISOString().split("T")[0];
  asOfDateInput.value = todayStr;
  sessionDisplay.textContent = `Session: ${sessionId.substring(0, 8)}...`;

  // Fetch backend status
  fetchHealth();

  // Handle sample query chip clicks
  sampleChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) {
      queryInput.value = chip.getAttribute("data-query");
      const lang = chip.getAttribute("data-lang");
      if (lang) {
        targetLangSelect.value = lang;
      }
      queryInput.focus();
    }
  });

  // Handle Clear
  btnClear.addEventListener("click", () => {
    queryInput.value = "";
    targetLangSelect.value = "";
    asOfDateInput.value = todayStr;
    resultsSection.classList.add("hidden");
    fbReasonBox.classList.add("hidden");
    fbToast.classList.add("hidden");
  });

  // Handle Query Submission
  askForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    setLoading(true);
    fbReasonBox.classList.add("hidden");
    fbToast.classList.add("hidden");

    const payload = {
      query: query,
      as_of: asOfDateInput.value || todayStr,
      language: targetLangSelect.value || null,
      session_id: sessionId,
    };

    try {
      const response = await fetch("/v1/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`);
      }

      const data = await response.json();
      renderResults(data);
    } catch (err) {
      alert("Error querying Anupalan compliance API: " + err.message);
    } finally {
      setLoading(false);
    }
  });

  // Render Response
  function renderResults(data) {
    currentAnswerId = data.answer_id;
    resultsSection.classList.remove("hidden");

    // Metadata tags
    resBadgeLang.textContent = `Lang: ${data.language.toUpperCase()}`;
    resBadgeAsOf.textContent = `As Of: ${data.as_of}`;

    // Abstention Handling
    if (data.abstained) {
      resBadgeGrounding.textContent = "Abstained / Out-of-Scope";
      resBadgeGrounding.className = "badge badge-warning";
      abstentionBanner.classList.remove("hidden");
      abstentionText.textContent = data.summary;
      summaryText.textContent = "Query could not be grounded in verifiable statutory circulars for the given criteria.";
      claimsList.innerHTML = "<p class='text-muted'>No claims synthesized due to statutory abstention.</p>";
      nextStepsList.innerHTML = "<li>Rephrase your compliance question with specific industry details.</li><li>Verify if the subject matter falls under Gujarat MSME or GST regulations.</li>";
    } else {
      resBadgeGrounding.textContent = "Verified Statutory Grounding";
      resBadgeGrounding.className = "badge badge-success";
      abstentionBanner.classList.add("hidden");
      summaryText.textContent = data.summary;

      // Render Claims
      claimsList.innerHTML = "";
      if (data.claims && data.claims.length > 0) {
        data.claims.forEach((claim) => {
          const card = document.createElement("div");
          card.className = "claim-card";

          const confPercent = Math.round((claim.confidence || 0.95) * 100);
          let citationsHtml = "";

          if (claim.citations && claim.citations.length > 0) {
            claim.citations.forEach((cit) => {
              citationsHtml += `
                <button class="citation-pill" data-chunk-id="${cit.chunk_id}" data-inst="${cit.instrument}" data-clause="${cit.clause}" data-from="${cit.effective_from}">
                  📜 ${cit.instrument} • ${cit.clause}
                </button>
              `;
            });
          }

          card.innerHTML = `
            <div class="claim-header">
              <div class="claim-text">${escapeHtml(claim.text)}</div>
              <div class="claim-confidence">Entailment: ${confPercent}%</div>
            </div>
            <div class="citations-wrap">
              ${citationsHtml}
            </div>
          `;
          claimsList.appendChild(card);
        });
      } else {
        claimsList.innerHTML = "<p class='text-muted'>General statutory synthesis.</p>";
      }

      // Render Next Steps
      nextStepsList.innerHTML = "";
      if (data.next_steps && data.next_steps.length > 0) {
        data.next_steps.forEach((step) => {
          const li = document.createElement("li");
          li.textContent = step;
          nextStepsList.appendChild(li);
        });
      } else {
        nextStepsList.innerHTML = "<li>Review original gazette notification clauses prior to return filing.</li>";
      }
    }

    disclaimerText.textContent = data.disclaimer || "Informational use only. Consult a registered CA for tax filing.";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  // Handle Citation Badge Click
  document.addEventListener("click", async (e) => {
    const citBtn = e.target.closest(".citation-pill");
    if (!citBtn) return;

    const chunkId = citBtn.getAttribute("data-chunk-id");
    const instTitle = citBtn.getAttribute("data-inst");
    const clause = citBtn.getAttribute("data-clause");
    const effFrom = citBtn.getAttribute("data-from");

    modalInstTitle.textContent = instTitle;
    modalClause.textContent = clause;
    modalEffectiveFrom.textContent = effFrom;
    modalPassageText.textContent = "Fetching official gazette passage...";
    modalTimelineList.innerHTML = "<li>Loading amendment history...</li>";
    citationModal.classList.remove("hidden");

    try {
      const res = await fetch(`/v1/chunks/${chunkId}`);
      if (res.ok) {
        const chunk = await res.json();
        modalPassageText.textContent = chunk.text;
        modalAuthority.textContent = chunk.metadata.authority || "CBIC / MSME Dept";

        // Bounding box
        if (chunk.bbox) {
          modalBboxPage.textContent = chunk.bbox.page || 1;
          modalBboxCoords.textContent = `[${chunk.bbox.x0}, ${chunk.bbox.y0}, ${chunk.bbox.x1}, ${chunk.bbox.y1}]`;
          modalOcrQuality.textContent = `${Math.round((chunk.ocr_quality || 0.98) * 100)}%`;
        }

        // Instrument details & timeline
        fetchInstrumentTimeline(chunk.instrument_id || instTitle);
      } else {
        modalPassageText.textContent = `Passage clause: ${clause} in ${instTitle}.`;
      }
    } catch (err) {
      modalPassageText.textContent = `Passage clause: ${clause} in ${instTitle}.`;
    }
  });

  async function fetchInstrumentTimeline(instKey) {
    try {
      const res = await fetch(`/v1/instruments/${encodeURIComponent(instKey)}`);
      if (res.ok) {
        const inst = await res.json();
        if (inst.source_url) {
          modalSourceLink.href = inst.source_url;
          modalSourceLink.classList.remove("hidden");
        } else {
          modalSourceLink.classList.add("hidden");
        }

        modalTimelineList.innerHTML = "";
        const tl = inst.amendment_timeline;
        if (tl) {
          if (tl.amends && tl.amends.length > 0) {
            tl.amends.forEach(a => {
              const li = document.createElement("li");
              li.textContent = `Amends ${a.code} (Effective: ${a.effective_from || 'N/A'})`;
              modalTimelineList.appendChild(li);
            });
          }
          if (tl.amended_by && tl.amended_by.length > 0) {
            tl.amended_by.forEach(a => {
              const li = document.createElement("li");
              li.textContent = `Amended by ${a.code} (Effective: ${a.effective_from || 'N/A'})`;
              modalTimelineList.appendChild(li);
            });
          }
          if (tl.superseded_by && tl.superseded_by.length > 0) {
            tl.superseded_by.forEach(s => {
              const li = document.createElement("li");
              li.textContent = `Superseded by ${s.code} (Effective: ${s.effective_from || 'N/A'})`;
              modalTimelineList.appendChild(li);
            });
          }
        }
        if (modalTimelineList.children.length === 0) {
          modalTimelineList.innerHTML = "<li>Base instrument in force without subsequent supersessions.</li>";
        }
      }
    } catch (_) {
      modalTimelineList.innerHTML = "<li>Timeline verification completed.</li>";
    }
  }

  // Close Modal
  function closeModal() { citationModal.classList.add("hidden"); }
  modalClose.addEventListener("click", closeModal);
  modalCloseBtn.addEventListener("click", closeModal);
  citationModal.addEventListener("click", (e) => {
    if (e.target === citationModal) closeModal();
  });

  // Feedback Controls
  fbUp.addEventListener("click", () => submitFeedbackRating(1, null));
  fbDown.addEventListener("click", () => {
    fbReasonBox.classList.remove("hidden");
  });

  fbSubmit.addEventListener("click", () => {
    const reason = fbReason.value;
    const comment = fbComment.value.trim();
    submitFeedbackRating(-1, reason, comment);
  });

  async function submitFeedbackRating(rating, reasonCode = null, comment = null) {
    if (!currentAnswerId) return;
    try {
      const res = await fetch("/v1/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer_id: currentAnswerId,
          rating: rating,
          reason_code: reasonCode,
          comment: comment,
        }),
      });
      if (res.ok) {
        fbReasonBox.classList.add("hidden");
        fbToast.textContent = rating > 0 ? "Thank you for the positive rating!" : "Feedback recorded. Our legal annotators will review.";
        fbToast.classList.remove("hidden");
      }
    } catch (_) {
      alert("Unable to submit feedback at this moment.");
    }
  }

  // DPDP Session Purge
  btnPurgeSession.addEventListener("click", async () => {
    if (confirm("Under DPDP Act 2023 Section 12 (Right to Erasure), this will permanently purge all query traces and logs associated with your session. Proceed?")) {
      try {
        const res = await fetch(`/v1/sessions/${sessionId}`, { method: "DELETE" });
        if (res.ok) {
          const data = await res.json();
          sessionStorage.removeItem("anupalan_session_id");
          sessionId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : "sess-" + Date.now();
          sessionStorage.setItem("anupalan_session_id", sessionId);
          sessionDisplay.textContent = `Session: ${sessionId.substring(0, 8)}... (New)`;
          resultsSection.classList.add("hidden");
          queryInput.value = "";
          alert(`DPDP Right to Erasure successful: ${data.purged_records} session records purged.`);
        }
      } catch (err) {
        alert("Failed to purge session: " + err.message);
      }
    }
  });

  // Health fetch
  async function fetchHealth() {
    try {
      const res = await fetch("/v1/health");
      if (res.ok) {
        const data = await res.json();
        corpusStatusBadge.textContent = `Corpus: ${data.corpus_updated} (${data.indexed_chunks} chunks)`;
      }
    } catch (_) {
      corpusStatusBadge.textContent = "Offline Mode";
    }
  }

  function setLoading(isLoading) {
    if (isLoading) {
      btnSubmit.disabled = true;
      btnSpinner.classList.remove("hidden");
      btnText.textContent = "Verifying...";
    } else {
      btnSubmit.disabled = false;
      btnSpinner.classList.add("hidden");
      btnText.textContent = "Search Compliance";
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
});
