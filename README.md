<img width="176" height="150" alt="agentic_pmbok_architecture" src="https://github.com/user-attachments/assets/78330d3b-8123-40c5-9479-92ce95a67934" />
# Agentic PMBOK Toolkit

An AI agent that reads your GitHub repository and keeps your project management documentation up to date — automatically.

Every six hours (or on every push), it scans your commits, pull requests, and open issues, identifies risks your team hasn't logged yet, and writes them to a structured risk register. It updates sprint velocity summaries, flags blockers, and pushes tickets to your Kanban board — all without anyone filling out a form.

---

## What it does

The agent acts as a background Scrum Master. It watches for patterns that experienced engineers recognize as warning signs: a module being reverted three times in a week, a PR sitting open with no reviewers, a senior developer who has gone quiet. When it spots something, it creates a PMBOK-formatted risk entry with an impact score, a mitigation strategy, and a direct link to the commit or PR that triggered it.

The output is a set of JSON files — `risk_register.json`, `velocity_log.json`, `stakeholder_map.json` — that stay current as long as the pipeline runs. A FastAPI server exposes these as REST endpoints. A React dashboard reads from those endpoints and refreshes every 30 seconds.

---
![Uploadi<svg width="100%" viewBox="0 0 680 580" role="img" style="" xmlns="http://www.w3.org/2000/svg">
  <title style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">Agentic PMBOK Toolkit architecture diagram</title>
  <desc style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">Four-layer architecture showing GitHub feeding into the Python extraction layer, then into the n8n AI Agent backed by an LLM, then outputs flowing to PMBOK artifacts, a Kanban board, and the FastAPI dashboard.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  <mask id="imagine-text-gaps-7e6bfe" maskUnits="userSpaceOnUse"><rect x="0" y="0" width="680" height="580" fill="white"/><rect x="7.5546875" y="88" width="49.04994201660156" height="19" fill="black" rx="2"/><rect x="7.0390625" y="218" width="50.893951416015625" height="19" fill="black" rx="2"/><rect x="7.109375" y="348" width="50.60795593261719" height="19" fill="black" rx="2"/><rect x="6.265625" y="484" width="51.437957763671875" height="19" fill="black" rx="2"/><rect x="143.9296875" y="72" width="91.91293334960938" height="22" fill="black" rx="2"/><rect x="122.84375" y="91.5" width="134.13980102539062" height="19" fill="black" rx="2"/><rect x="418.0859375" y="72" width="143.6988525390625" height="22" fill="black" rx="2"/><rect x="430.921875" y="91.5" width="118.98382568359375" height="19" fill="black" rx="2"/><rect x="112.1015625" y="182" width="115.65689086914062" height="22" fill="black" rx="2"/><rect x="104.5078125" y="201.5" width="130.94981384277344" height="19" fill="black" rx="2"/><rect x="448.78125" y="182" width="123.1558837890625" height="22" fill="black" rx="2"/><rect x="460.15625" y="201.5" width="99.5198974609375" height="19" fill="black" rx="2"/><rect x="299.65625" y="318.5" width="81.65591430664062" height="19" fill="black" rx="2"/><rect x="98.03125" y="349" width="127.8018798828125" height="22" fill="black" rx="2"/><rect x="107.7578125" y="368.5" width="108.52383422851562" height="19" fill="black" rx="2"/><rect x="321.25" y="349" width="38.225982666015625" height="22" fill="black" rx="2"/><rect x="290.3203125" y="368.5" width="99.36788940429688" height="19" fill="black" rx="2"/><rect x="444.8359375" y="349" width="146.18389892578125" height="22" fill="black" rx="2"/><rect x="459.234375" y="368.5" width="117.577880859375" height="19" fill="black" rx="2"/><rect x="83.734375" y="466" width="121.25187683105469" height="22" fill="black" rx="2"/><rect x="92.0234375" y="485.5" width="104.78182983398438" height="19" fill="black" rx="2"/><rect x="289.609375" y="466" width="101.013916015625" height="22" fill="black" rx="2"/><rect x="305.328125" y="485.5" width="69.77587890625" height="19" fill="black" rx="2"/><rect x="463.2421875" y="466" width="145.7508544921875" height="22" fill="black" rx="2"/><rect x="478.03125" y="485.5" width="115.913818359375" height="19" fill="black" rx="2"/></mask></defs>

  <!-- ── Layer labels ── -->
  <text x="32" y="102" text-anchor="middle" transform="rotate(-90,32,102)" style="fill:rgb(61, 61, 58);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">Trigger</text>
  <text x="32" y="232" text-anchor="middle" transform="rotate(-90,32,232)" style="fill:rgb(61, 61, 58);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">Extract</text>
  <text x="32" y="362" text-anchor="middle" transform="rotate(-90,32,362)" style="fill:rgb(61, 61, 58);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">Reason</text>
  <text x="32" y="498" text-anchor="middle" transform="rotate(-90,32,498)" style="fill:rgb(61, 61, 58);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">Output</text>

  <!-- dividers -->
  <line x1="54" y1="150" x2="646" y2="150" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="3 4" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.15);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-dasharray:3px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="54" y1="292" x2="646" y2="292" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="3 4" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.15);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-dasharray:3px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="54" y1="434" x2="646" y2="434" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="3 4" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.15);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-dasharray:3px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- ══════════════ LAYER 1: TRIGGERS ══════════════ -->
  <!-- GitHub -->
  <g onclick="sendPrompt('How does the GitHub API connect to the PMBOK toolkit?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="120" y="58" width="140" height="60" rx="8" stroke-width="0.5" style="fill:rgb(241, 239, 232);stroke:rgb(95, 94, 90);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="190" y="83" text-anchor="middle" dominant-baseline="central" style="fill:rgb(68, 68, 65);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">GitHub repo</text>
    <text x="190" y="101" text-anchor="middle" dominant-baseline="central" style="fill:rgb(95, 94, 90);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Commits · PRs · Issues</text>
  </g>

  <!-- Cron / Webhook -->
  <g onclick="sendPrompt('How does the cron trigger and webhook trigger work in n8n?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="420" y="58" width="140" height="60" rx="8" stroke-width="0.5" style="fill:rgb(241, 239, 232);stroke:rgb(95, 94, 90);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="490" y="83" text-anchor="middle" dominant-baseline="central" style="fill:rgb(68, 68, 65);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">Schedule / webhook</text>
    <text x="490" y="101" text-anchor="middle" dominant-baseline="central" style="fill:rgb(95, 94, 90);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Every 6h or on push</text>
  </g>

  <!-- ══════════════ LAYER 2: EXTRACTION ══════════════ -->
  <!-- git_extractor.py -->
  <g onclick="sendPrompt('What does git_extractor.py do and what does its output look like?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="80" y="168" width="180" height="60" rx="8" stroke-width="0.5" style="fill:rgb(225, 245, 238);stroke:rgb(15, 110, 86);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="170" y="193" text-anchor="middle" dominant-baseline="central" style="fill:rgb(8, 80, 65);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">git_extractor.py</text>
    <text x="170" y="211" text-anchor="middle" dominant-baseline="central" style="fill:rgb(15, 110, 86);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Snapshot → plain text</text>
  </g>

  <!-- PMBOK schemas -->
  <g onclick="sendPrompt('What PMBOK JSON schemas are used and what do they enforce?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="420" y="168" width="180" height="60" rx="8" stroke-width="0.5" style="fill:rgb(225, 245, 238);stroke:rgb(15, 110, 86);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="510" y="193" text-anchor="middle" dominant-baseline="central" style="fill:rgb(8, 80, 65);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">PMBOK schemas</text>
    <text x="510" y="211" text-anchor="middle" dominant-baseline="central" style="fill:rgb(15, 110, 86);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">JSON contracts</text>
  </g>

  <!-- ══════════════ LAYER 3: REASONING ══════════════ -->
  <!-- n8n agent container -->
  <rect x="68" y="308" width="544" height="110" rx="12" fill="var(--color-background-secondary)" stroke="var(--color-border-secondary)" stroke-width="0.5" style="fill:rgb(245, 244, 237);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <text x="340" y="328" text-anchor="middle" dominant-baseline="central" style="fill:rgb(61, 61, 58);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">n8n AI Agent</text>

  <!-- agent_pipeline.py -->
  <g onclick="sendPrompt('What does agent_pipeline.py do — how does the reasoning loop work?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="86" y="335" width="152" height="68" rx="8" stroke-width="0.5" style="fill:rgb(238, 237, 254);stroke:rgb(83, 74, 183);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="162" y="360" text-anchor="middle" dominant-baseline="central" style="fill:rgb(60, 52, 137);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">agent_pipeline.py</text>
    <text x="162" y="378" text-anchor="middle" dominant-baseline="central" style="fill:rgb(83, 74, 183);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Classify · validate</text>
  </g>

  <!-- LLM -->
  <g onclick="sendPrompt('Which LLMs are supported and how does the llm_client adapter work?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="264" y="335" width="152" height="68" rx="8" stroke-width="0.5" style="fill:rgb(238, 237, 254);stroke:rgb(83, 74, 183);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="340" y="360" text-anchor="middle" dominant-baseline="central" style="fill:rgb(60, 52, 137);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">LLM</text>
    <text x="340" y="378" text-anchor="middle" dominant-baseline="central" style="fill:rgb(83, 74, 183);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Claude · GPT-4o</text>
  </g>

  <!-- schema_validator -->
  <g onclick="sendPrompt('How does schema_validator.py stop the LLM writing bad JSON?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="442" y="335" width="152" height="68" rx="8" stroke-width="0.5" style="fill:rgb(238, 237, 254);stroke:rgb(83, 74, 183);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="518" y="360" text-anchor="middle" dominant-baseline="central" style="fill:rgb(60, 52, 137);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">schema_validator.py</text>
    <text x="518" y="378" text-anchor="middle" dominant-baseline="central" style="fill:rgb(83, 74, 183);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Guard before write</text>
  </g>

  <!-- ══════════════ LAYER 4: OUTPUTS ══════════════ -->
  <!-- PMBOK artifacts -->
  <g onclick="sendPrompt('What PMBOK artifact files does the agent write and where are they stored?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="68" y="452" width="152" height="68" rx="8" stroke-width="0.5" style="fill:rgb(250, 236, 231);stroke:rgb(153, 60, 29);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="144" y="477" text-anchor="middle" dominant-baseline="central" style="fill:rgb(113, 43, 19);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">PMBOK artifacts</text>
    <text x="144" y="495" text-anchor="middle" dominant-baseline="central" style="fill:rgb(153, 60, 29);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">risk_register.json</text>
  </g>

  <!-- Kanban -->
  <g onclick="sendPrompt('How does kanban_connector.py push tickets to Trello or Jira?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="264" y="452" width="152" height="68" rx="8" stroke-width="0.5" style="fill:rgb(250, 236, 231);stroke:rgb(153, 60, 29);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="340" y="477" text-anchor="middle" dominant-baseline="central" style="fill:rgb(113, 43, 19);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">Kanban board</text>
    <text x="340" y="495" text-anchor="middle" dominant-baseline="central" style="fill:rgb(153, 60, 29);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Trello · Jira</text>
  </g>

  <!-- FastAPI + Dashboard -->
  <g onclick="sendPrompt('How does the FastAPI server connect to the React dashboard?')" style="fill:rgb(0, 0, 0);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="460" y="452" width="152" height="68" rx="8" stroke-width="0.5" style="fill:rgb(250, 236, 231);stroke:rgb(153, 60, 29);color:rgb(0, 0, 0);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="536" y="477" text-anchor="middle" dominant-baseline="central" style="fill:rgb(113, 43, 19);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">FastAPI + dashboard</text>
    <text x="536" y="495" text-anchor="middle" dominant-baseline="central" style="fill:rgb(153, 60, 29);stroke:none;color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">api/main.py · React</text>
  </g>

  <!-- ══════════════ CONNECTORS ══════════════ -->

  <!-- GitHub → git_extractor -->
  <line x1="190" y1="118" x2="170" y2="168" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- Cron → agent (into n8n box top) -->
  <line x1="490" y1="118" x2="490" y2="168" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- git_extractor → agent_pipeline -->
  <line x1="170" y1="228" x2="162" y2="335" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- PMBOK schemas → schema_validator -->
  <line x1="510" y1="228" x2="518" y2="335" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- Cron node → pipeline (horizontal into n8n) -->
  <path d="M490 228 L490 270 L162 270 L162 335" fill="none" stroke="var(--color-border-tertiary)" stroke-width="0.8" stroke-dasharray="4 3" marker-end="url(#arrow)" style="fill:none;stroke:rgba(31, 30, 29, 0.15);color:rgb(0, 0, 0);stroke-width:0.8px;stroke-dasharray:4px, 3px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- agent_pipeline ↔ LLM -->
  <line x1="238" y1="369" x2="264" y2="369" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="264" y1="379" x2="238" y2="379" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- LLM → schema_validator -->
  <line x1="416" y1="369" x2="442" y2="369" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- agent_pipeline → PMBOK artifacts -->
  <line x1="144" y1="403" x2="144" y2="452" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:rgb(0, 0, 0);stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- agent_pipeline → Kanban -->
  <path d="M238 390 L340 390 L340 452" fill="none" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" style="fill:none;stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- PMBOK artifacts → FastAPI -->
  <path d="M220 486 L460 486" fill="none" stroke="var(--color-border-secondary)" stroke-width="1" marker-end="url(#arrow)" mask="url(#imagine-text-gaps-7e6bfe)" style="fill:none;stroke:rgba(31, 30, 29, 0.3);color:rgb(0, 0, 0);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

</svg>ng agentic_pmbok_architecture.svg…]()
---

## Project structure

```
agentic-pmbok/
├── src/
│   ├── git_extractor.py      # pulls commits, PRs, issues from GitHub
│   ├── kanban_connector.py   # creates/updates Trello or Jira tickets
│   ├── schema_validator.py   # validates AI output before writing to disk
│   ├── llm_client.py         # Anthropic/OpenAI adapter with retry logic
│   ├── agent_pipeline.py     # end-to-end orchestration loop
│   ├── test_phase1.py        # 21 tests — extractors and connectors
│   ├── test_phase2.py        # 36 tests — schemas, workflow, prompt
│   ├── test_phase3.py        # 52 tests — pipeline with mocked LLM
│   └── test_api.py           # 52 tests — all API endpoints
├── api/
│   └── main.py               # FastAPI server (12 endpoints)
├── schemas/
│   ├── risk_register.schema.json
│   ├── charter.schema.json
│   ├── stakeholder_map.schema.json
│   └── velocity_log.schema.json
├── artifacts/                # live output — updated by the agent
│   ├── risk_register.json
│   └── velocity_log.json
├── prompts/
│   └── agent_system_prompt.md  # agent persona and detection rules
├── n8n/
│   └── workflow.json           # importable n8n workflow
├── dashboard/
│   └── pmbok_dashboard.jsx     # React dashboard
├── logs/                       # runtime logs, created automatically
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/yourname/agentic-pmbok-toolkit.git
cd agentic-pmbok-toolkit
cp .env.example .env
```

Fill in `.env` at minimum:

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=owner/your-repo
ANTHROPIC_API_KEY=sk-ant-your_key_here
KANBAN_PROVIDER=trello
TRELLO_API_KEY=...
TRELLO_TOKEN=...
TRELLO_BOARD_ID=...
TRELLO_LIST_ID=...
CURRENT_SPRINT=SP-01
SPRINT_START_DATE=2026-01-01
SPRINT_END_DATE=2026-01-14
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the tests

```bash
pytest src/test_phase1.py src/test_phase2.py src/test_phase3.py src/test_api.py -v
```

Expected: 161 passed. No API keys needed — all LLM calls are mocked.

### 4. Start the API server

```bash
uvicorn api.main:app --reload --port 8000
```

Check it's working:

```
http://localhost:8000/api/health      → { "status": "ok" }
http://localhost:8000/api/risks       → seed risk data
http://localhost:8000/api/dashboard   → full dashboard payload
http://localhost:8000/docs            → interactive API docs
```

### 5. Test the extractor (needs GitHub token)

```bash
python src/git_extractor.py --repo owner/your-repo --commits 20 --days 7
```

This prints the structured snapshot the agent will analyse. No LLM involved yet.

### 6. Run a dry-run pipeline call (needs LLM key)

```bash
python src/agent_pipeline.py \
  --repo owner/your-repo \
  --sprint SP-01 \
  --start 2026-01-01 \
  --end 2026-01-14 \
  --dry-run \
  --output text
```

`--dry-run` calls the LLM and shows you what it would write, without touching any files or Kanban boards.

### 7. Run a live pipeline call

Remove `--dry-run`. The agent will write to `artifacts/risk_register.json` and, if a risk is found, push a ticket to your Kanban board.

```bash
python src/agent_pipeline.py \
  --repo owner/your-repo \
  --sprint SP-01 \
  --start 2026-01-01 \
  --end 2026-01-14
```

### 8. Start the dashboard

```bash
cd dashboard
npm create vite@latest . -- --template react
# select "Ignore files and continue" when prompted
npm install recharts
```

Copy `pmbok_dashboard.jsx` into `dashboard/src/`, then replace `dashboard/src/App.jsx` with:

```jsx
import ProjectDashboard from './pmbok_dashboard'
export default function App() { return <ProjectDashboard /> }
```

```bash
npm run dev
# open http://localhost:5173
```

---

## Running with Docker

Both the API server and n8n run as Docker services:

```bash
docker compose up -d

# API   → http://localhost:8000
# n8n   → http://localhost:5678
```

---

## n8n workflow

The `n8n/workflow.json` file is a ready-to-import n8n workflow that runs the full pipeline on a 6-hour schedule (or on GitHub webhook push). After importing:

1. Add your OpenAI or Anthropic credential under **Settings → Credentials**
2. Connect the LLM sub-node to the AI Agent node's language model input
3. Confirm file paths match your setup (Docker vs local)
4. Run manually once to verify before activating the schedule

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server and artifact file status |
| GET | `/api/risks` | All risks (filterable by status, category, impact) |
| GET | `/api/risks/summary` | KPI aggregations |
| GET | `/api/risks/{risk_id}` | Single risk entry |
| GET | `/api/velocity` | Full sprint velocity log |
| GET | `/api/velocity/current` | Active sprint |
| GET | `/api/velocity/{sprint_id}` | Single sprint |
| GET | `/api/stakeholders` | Stakeholder map |
| GET | `/api/pipeline/runs` | Pipeline audit log |
| GET | `/api/pipeline/stats` | Aggregated run statistics |
| POST | `/api/pipeline/trigger` | Trigger a pipeline run manually |
| GET | `/api/dashboard` | Single payload for the dashboard |

Interactive docs at `http://localhost:8000/docs`.

---

## How the agent decides what to flag

The system prompt in `prompts/agent_system_prompt.md` defines six detection rules:

- **Repetition** — three or more commits touching the same module with words like `revert`, `hotfix`, or `workaround` → Technical risk
- **Revert** — any explicit git revert → automatic impact score of 7 or higher
- **Blocker labels** — issues tagged `blocker` or `p0` open for more than 3 days → Schedule risk
- **Stale PRs** — a PR open for 5+ days with no review comments → Resource risk
- **Contributor silence** — a developer who normally commits 5+ times per sprint goes quiet → Resource risk
- **Confidence threshold** — risks need at least two independent signals to be created; a single data point goes in a watch list instead

The agent outputs strict JSON matching the schemas in `schemas/`. If the output doesn't validate, nothing is written.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | Personal access token (scopes: repo, issues) |
| `GITHUB_REPO` | Yes | `owner/repo-name` |
| `ANTHROPIC_API_KEY` | One of these | Claude API key |
| `OPENAI_API_KEY` | One of these | OpenAI API key |
| `KANBAN_PROVIDER` | Yes | `trello` or `jira` |
| `TRELLO_API_KEY` | Trello | Developer key from trello.com/app-key |
| `TRELLO_TOKEN` | Trello | OAuth token |
| `TRELLO_BOARD_ID` | Trello | Board ID from board URL |
| `TRELLO_LIST_ID` | Trello | Column ID for the Risks list |
| `JIRA_BASE_URL` | Jira | `https://yourorg.atlassian.net` |
| `JIRA_USER_EMAIL` | Jira | Atlassian account email |
| `JIRA_API_TOKEN` | Jira | Atlassian API token |
| `JIRA_PROJECT_KEY` | Jira | e.g. `PROJ` |
| `CURRENT_SPRINT` | Yes | e.g. `SP-03` |
| `SPRINT_START_DATE` | Yes | `YYYY-MM-DD` |
| `SPRINT_END_DATE` | Yes | `YYYY-MM-DD` |
| `SLACK_CHANNEL_ID` | Optional | For Slack notifications from n8n |

---

## Test coverage

| Phase | Scope | Tests |
|-------|-------|-------|
| Phase 1 | GitHub extractor, Kanban connector | 21 |
| Phase 2 | PMBOK schemas, n8n workflow, system prompt | 36 |
| Phase 3 | LLM pipeline end-to-end (mocked) | 52 |
| API | All FastAPI endpoints | 52 |
| **Total** | | **161** |

---

## Deployment checklist

- [ ] All 161 tests passing locally
- [ ] `.env` filled in with real tokens
- [ ] `python src/agent_pipeline.py --dry-run` produces valid JSON
- [ ] `http://localhost:8000/api/health` returns `{ "status": "ok" }`
- [ ] Dashboard loading at `http://localhost:5173`
- [ ] n8n workflow imported and manually triggered once successfully
- [ ] n8n workflow activated (enables the 6-hour schedule)

---

## License

MIT
