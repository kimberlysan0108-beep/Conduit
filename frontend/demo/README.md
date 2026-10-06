# Conduit — Interactive Demo

A personal-project support-resolution simulation with editable transaction amounts, policy checks, approval levels, a case queue and an execution history.

## Publish the exact demo on GitHub Pages

1. Create a public GitHub repository, for example `conduit-demo`.
2. Select **Add file → Upload files**. Upload `index.html` and this `README.md` directly into the repository. Do not upload the ZIP or put these files inside another folder. Commit the upload to `main`.
3. Open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**, then **main** and **/(root)**. Click **Save**.
5. After deployment finishes, the Pages screen shows your website URL. It will normally look like `https://YOUR-USERNAME.github.io/conduit-demo/`.

No npm installation, build command, Docker, Stripe account or API key is needed for this demo. The exported page loads its UI helper assets from public CDNs, so an internet connection is needed for those assets.

## Try it

- Enter a transaction value, then press **Run investigation** or Enter.
- Use **Edit test case** to change a pending case and recalculate its policy and approval requirements.
- $25.00 or less: eligible financial actions execute automatically.
- $25.01–$250.00: customer confirmation is required.
- Above $250.00: operator approval is required.
- Ineligible actions stay blocked regardless of value.
- Switch customer/operator view, inspect the trajectory, and verify a refund after a simulated timeout.
- Editing an already completed case starts a separate test case; it does not alter the completed action.

## Scope

This package contains the exact browser-based interactive demo, not the separate Python/PostgreSQL backend repository. Payments, evidence and customer records are simulated. The investigation follows deterministic scenario rules; it is not a live LLM call. No real money moves. Case changes are held in memory and reset when the page reloads. A role selector is a demo control, not production authentication.

The full Python backend requires separate hosting because GitHub Pages serves static HTML/CSS/JavaScript. Uploading this package does not deploy the backend or activate Stripe. The earlier full-project ZIP remains a separate backend/research prototype.

## Fix included

Investigation no longer depends on native form submission. An explicit button handler and keyboard handler support the restricted embedded preview and the exported page. This also corrects the Run investigation / Save & recheck behavior.

## GitHub documentation

- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Navigation fix

The sidebar and queue filters now switch the heading, visible cases and selected case together. Changing a filter clears an old search and closes the case editor so the chosen view is immediately visible. Evidence and Trajectory have explicit click handlers; decision notes survive switching between them. Cases move out of Needs review and into Resolved after successful approval.

Validation: 15 browser checks passed in the exported sandboxed page, covering both sets of filters, search, detail tabs, draft notes, creation, editing, approvals, reconciliation, and mobile layout. No JavaScript page errors were recorded during these checks.
