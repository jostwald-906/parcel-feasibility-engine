/**
 * Download utilities for file downloads
 */

/**
 * Triggers a browser download for a PDF blob
 * @param blob - The PDF blob to download
 * @param filename - The desired filename (e.g., "feasibility-report.pdf")
 */
export function downloadPDF(blob: Blob, filename: string): void {
  // Create a temporary URL for the blob
  const url = URL.createObjectURL(blob);

  // Create a temporary anchor element
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  // Append to document, trigger click, and clean up
  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Generates a filename for the PDF export
 * @param apn - The parcel APN
 * @returns Formatted filename with timestamp
 */
export function generatePDFFilename(apn: string): string {
  // Clean APN (remove special characters)
  const cleanAPN = apn.replace(/[^a-zA-Z0-9]/g, '-');

  // Get current date in YYYY-MM-DD format
  const date = new Date().toISOString().split('T')[0];

  return `feasibility-report_${cleanAPN}_${date}.pdf`;
}
