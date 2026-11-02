# STILLWELL — Web CTF Write-up

**CTF:** HI Cyber Con 2026  
**Category:** Web Exploitation  
**Challenge:** STILLWELL  
**Vulnerability:** Path Traversal / Arbitrary File Read  
**Flag Format:** `hiCTF{...}`

## 1. Challenge Description

STILLWELL is a boutique real estate brokerage with an agent portal that accepts compressed partner exports and previews property listings before publication.

The objective was to locate a restricted closing ledger accidentally left accessible during an acquisition and recover the authorization token stored inside it.

## 2. Reconnaissance

Opening the challenge website revealed a real estate platform with a separate agent portal at:

`/agency`

Inspecting the frontend JavaScript at `/assets/app.js` revealed an interesting API endpoint:

`POST /api/agency/import/preview`

The application accepted brokerage exports in Brotli-compressed JSON format (`.br`).

It also provided a sample export at:

`/assets/sample-export.br`

After downloading and decompressing the sample, we obtained:

```json
{
  "format": "stillwell.agency-export/1",
  "properties": [
    {
      "title": "Meadow House",
      "neighborhood": "Greenpoint",
      "price": 990000,
      "document": "welcome.txt"
    },
    {
      "title": "Moorland Loft",
      "neighborhood": "Williamsburg",
      "price": 1275000
    }
  ]
}
```

The `document` parameter was particularly interesting because it referenced a filename rather than containing the document itself.

## 3. Discovering the File Reader

We submitted the original sample export to the preview endpoint using:

```http
POST /api/agency/import/preview
Content-Type: application/json
Content-Encoding: br
```

The server returned a successful response containing:

```json
{
  "status": "preview_ready",
  "count": 2,
  "sample": [
    {
      "title": "Meadow House",
      "document": {
        "name": "welcome.txt",
        "excerpt": "STILLWELL PARTNER DOCUMENT LIBRARY..."
      }
    }
  ]
}
```

This revealed important behavior: **the backend reads documents from its filesystem and returns their contents through the preview response.**

The welcome document also explained that each imported property could reference a supporting document by filename.

This made the `document` field the main attack surface.

## 4. Exploitation — Path Traversal

The weakness involved user-controlled document filenames being passed to a server-side file reader.

If the application does not properly restrict the resolved file path to its intended document directory, relative paths containing `../` can potentially escape that directory.

For example, a modified export could contain:

```json
{
  "format": "stillwell.agency-export/1",
  "properties": [
    {
      "title": "Test Property",
      "neighborhood": "Greenpoint",
      "price": 990000,
      "document": "../restricted/closing-ledger.txt"
    }
  ]
}
```

*The path shown here is an illustrative candidate; the exact successful path was not retained in the available logs.*

The modified JSON must be Brotli-compressed before submission.

We tested document paths through the existing preview API and inspected the returned document objects, especially their `excerpt` and `error` fields.

The relevant exploitation technique was to manipulate the document filename so that the backend would attempt to resolve a file outside the intended partner document library.

## 5. Reading the Restricted Ledger

The target was the restricted closing ledger mentioned in the challenge description.

The attack used the preview functionality rather than a dedicated file-download endpoint. When a document could be read, its contents were exposed in the JSON response under:

`sample[0].document.excerpt`

This created a file-disclosure channel through an otherwise legitimate listing-preview feature.

The final objective was to identify the authorization token within the ledger and submit it in the required `hiCTF{...}` format.

**Flag:** Not recorded in the retained logs.

## 6. Root Cause

The security issue was the trust placed in an attacker-controlled document reference.

The application accepted document names from externally supplied partner exports and used them for server-side file access.

If such references are not safely normalized and restricted, an attacker can potentially traverse outside the intended document directory and read sensitive files.

The important distinction is that Brotli compression was only the transport format. The vulnerability was in how the application handled document paths after decompression.

## 7. Remediation

To prevent this class of vulnerability, the application should:

- Resolve document paths against a fixed, trusted base directory and verify they remain inside it.
- Reject absolute paths and directory traversal sequences.
- Prefer server-generated document identifiers over client-supplied filesystem paths.
- Run the preview service with minimal filesystem permissions.
- Avoid returning sensitive file contents in detailed preview or error responses.

## 8. Conclusion

STILLWELL demonstrated how a legitimate document-preview feature can become a file-disclosure vulnerability when untrusted filenames are used for filesystem access.

The key observation was that the `document` field caused the backend to read files and return their contents in the API response.

**Key takeaway:** File access based on user-controlled paths must be restricted to an explicitly authorized directory, regardless of whether the input arrives through JSON, a compressed export, or another format.
