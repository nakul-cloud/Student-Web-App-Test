/**
 * Ingest API — maps to backend `app/routes/ingest_routes.py` (/api/v1/ingest/*)
 */
(function (global) {
  global.IngestApi = {
    uploadPdfFile(file, category = "GIFT City Compliance PDF") {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("category", category);
      return global.HttpClient.request("/api/v1/ingest/pdf-file", {
        method: "POST",
        body: formData,
      });
    },

    ingestPdfUrl(url, category = "GIFT City Circular", filename = "guideline.pdf") {
      return global.HttpClient.request("/api/v1/ingest/pdf-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, category, filename }),
      });
    },
  };
})(window);
