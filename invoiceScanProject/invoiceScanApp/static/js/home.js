// Home page: client-side checks of the upload form and scan progress feedback.
(() => {
  const form = document.getElementById("upload-form");
  const inputs = form.querySelectorAll(".upload__input");
  const selection = document.getElementById("upload-selection");
  const submitButton = document.getElementById("upload-submit");

  const selectedFiles = () => Array.from(inputs).flatMap((input) => Array.from(input.files));

  inputs.forEach((input) =>
    input.addEventListener("change", () => {
      const count = selectedFiles().length;
      selection.textContent = count ? `${count} image${count > 1 ? "s" : ""} selected` : "";
    })
  );

  form.addEventListener("submit", (event) => {
    const files = selectedFiles();
    if (files.length === 0) {
      event.preventDefault();
      alert("Please upload at least one image.");
      return;
    }

    const invalid = files.filter((file) => !file.type.startsWith("image/"));
    if (invalid.length > 0) {
      event.preventDefault();
      alert(`These files are not images: ${invalid.map((file) => file.name).join(", ")}`);
      return;
    }

    // OCR + AI extraction can take a while: prevent double submissions.
    submitButton.disabled = true;
    submitButton.textContent = "Scanning…";
  });

  // Re-enable the button when the page is restored with the browser's back button.
  window.addEventListener("pageshow", () => {
    submitButton.disabled = false;
    submitButton.textContent = "Submit";
  });
})();
