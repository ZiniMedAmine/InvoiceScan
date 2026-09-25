// Review page: edit the extracted JSON, save it, then export it as files.
(() => {
  const review = document.getElementById("review");
  const csrfToken = review.querySelector("[name=csrfmiddlewaretoken]").value;
  const documents = Array.from(review.querySelectorAll(".document"));
  const exportSection = document.getElementById("export-section");
  const EXPORT_FILENAME = "invoicescan_export.zip";

  const viewerOf = (doc) => doc.querySelector(".document__text");
  const editorOf = (doc) => doc.querySelector(".document__editor");

  function setEditing(editing) {
    documents.forEach((doc) => {
      viewerOf(doc).hidden = editing;
      editorOf(doc).hidden = !editing;
    });
  }

  // Returns an error message, or null when the text is valid JSON.
  // jsonlint (loaded from a CDN) gives more precise messages than JSON.parse.
  function jsonError(text) {
    try {
      (window.jsonlint || JSON).parse(text);
      return null;
    } catch (error) {
      return error.message;
    }
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.message || `Request failed (${response.status}).`);
    }
    return response;
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement("a"), { href: url, download: filename });
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function editData() {
    setEditing(true);
    exportSection.hidden = true;
    editorOf(documents[0])?.focus();
  }

  async function submitData() {
    for (const doc of documents) {
      const error = jsonError(editorOf(doc).value);
      if (error) {
        setEditing(true);
        editorOf(doc).focus();
        alert(`Syntax error:\n${error}`);
        return;
      }
    }

    const payload = documents.map((doc) => ({ id: Number(doc.dataset.id), text: editorOf(doc).value }));
    try {
      await postJson(review.dataset.saveUrl, payload);
    } catch (error) {
      alert(error.message);
      return;
    }

    documents.forEach((doc) => {
      viewerOf(doc).textContent = editorOf(doc).value;
    });
    setEditing(false);
    exportSection.hidden = false;
  }

  async function exportData() {
    const formats = Array.from(exportSection.querySelectorAll("input[name=format]:checked"), (input) => input.value);
    if (formats.length === 0) {
      alert("Please select at least one format to export.");
      return;
    }

    try {
      const response = await postJson(review.dataset.exportUrl, { formats });
      downloadBlob(await response.blob(), EXPORT_FILENAME);
    } catch (error) {
      alert(error.message);
    }
  }

  document.getElementById("edit-button").addEventListener("click", editData);
  document.getElementById("save-button").addEventListener("click", submitData);
  document.getElementById("export-button").addEventListener("click", exportData);
})();
