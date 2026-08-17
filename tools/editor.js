(() => {
  const content = document.querySelector('main#content');
  if (!content) return;

  const pageHead = document.head.innerHTML;
  const pageScripts = [...document.querySelectorAll('body > script:not([src])')]
    .map(script => `<script>${script.textContent}<\/script>`).join('\n');
  const panel = document.getElementById('panel');
  const panelHtml = panel ? panel.outerHTML : '';
  const localIndexPaths = new Set(
    [...document.querySelectorAll('a[data-remembrancer-local]')]
      .map(link => link.getAttribute('href'))
  );
  const graphics = new Map();

  const clean = value => value.replace(/\s+/g, ' ').trim();
  const escapeHtml = value => value
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

  function inlineToMarkdown(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent.replace(/\s+/g, ' ');
    if (node.nodeType !== Node.ELEMENT_NODE) return '';
    const text = [...node.childNodes].map(inlineToMarkdown).join('');
    const tag = node.tagName.toLowerCase();
    if (tag === 'strong' || tag === 'b') return `**${text.trim()}**`;
    if (tag === 'em' || tag === 'i') return `*${text.trim()}*`;
    if (tag === 'a') return `[${text.trim()}](${node.getAttribute('href') || ''})`;
    if (tag === 'br') return '  \n';
    if (node.classList.contains('model')) return node.outerHTML;
    return text;
  }

  function tableToMarkdown(table) {
    const rows = [...table.rows].map(row => [...row.cells].map(cell => clean(cell.textContent)));
    if (!rows.length) return '';
    const width = Math.max(...rows.map(row => row.length));
    rows.forEach(row => { while (row.length < width) row.push(''); });
    const line = row => `| ${row.map(value => value.replaceAll('|', '\\|')).join(' | ')} |`;
    return [line(rows[0]), line(Array(width).fill('---')), ...rows.slice(1).map(line)].join('\n');
  }

  function childrenToMarkdown(element) {
    return [...element.children].map(blockToMarkdown).filter(Boolean).join('\n\n');
  }

  function contentToMarkdown(element) {
    const hasBlocks = [...element.children].some(child =>
      /^(DIV|P|H1|H2|H3|H4|H5|H6|UL|OL|PRE|TABLE)$/.test(child.tagName));
    return hasBlocks ? childrenToMarkdown(element) : inlineToMarkdown(element).trim();
  }

  function figureToMarkdown(figure, index) {
    const id = figure.dataset.remembrancerAsset || `figure-${index + 1}`;
    figure.dataset.remembrancerAsset = id;
    const blocks = [];
    [...figure.children].forEach(child => {
      if (child.tagName.toLowerCase() === 'svg') {
        graphics.set(id, child.outerHTML);
        blocks.push(`{{graphic:${id}}}`);
      } else if (child.classList.contains('zoom')) {
        blocks.push(`::: explanation ${child.id}\n${contentToMarkdown(child)}\n:::`);
      } else {
        blocks.push(blockToMarkdown(child));
      }
    });
    return `::: figure ${id}\n${blocks.filter(Boolean).join('\n\n')}\n:::`;
  }

  function blockToMarkdown(node, index = 0) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return '';
    const tag = node.tagName.toLowerCase();
    const inline = () => inlineToMarkdown(node).trim();
    if (/^h[1-6]$/.test(tag)) return `${'#'.repeat(Number(tag[1]))} ${inline()}`;
    if (tag === 'a') return `[${inline()}](${node.getAttribute('href') || ''})`;
    if (tag === 'p') {
      const prefix = node.classList.contains('lead') || node.classList.contains('sub') ? 'Lead: '
        : node.classList.contains('small') ? 'Small: '
        : node.classList.contains('src') ? 'Source: ' : '';
      const value = prefix === 'Source: ' ? inline().replace(/^Source:\s*/i, '') : inline();
      return prefix + value;
    }
    if (tag === 'div' && (node.classList.contains('tag') || node.classList.contains('label'))) return `Label: ${inline()}`;
    if (tag === 'div' && node.classList.contains('note')) return `::: note\n${contentToMarkdown(node)}\n:::`;
    if (tag === 'div' && node.classList.contains('figbox')) return figureToMarkdown(node, index);
    if (tag === 'div' && node.classList.contains('panel-note')) {
      return `::: side-note ${node.id}\n${contentToMarkdown(node)}\n:::`;
    }
    if (tag === 'pre') return `\`\`\`text\n${node.textContent.trim()}\n\`\`\``;
    if (tag === 'ul' || tag === 'ol') {
      return [...node.children].map((item, itemIndex) =>
        `${tag === 'ol' ? `${itemIndex + 1}.` : '-'} ${inlineToMarkdown(item).trim()}`).join('\n');
    }
    if (tag === 'table') return tableToMarkdown(node);
    if (node.classList.contains('tblwrap') || node.classList.contains('table-wrap')) {
      const table = node.querySelector('table');
      return table ? tableToMarkdown(table) : childrenToMarkdown(node);
    }
    if (tag === 'img') return `![${node.getAttribute('alt') || ''}](${node.getAttribute('src') || ''})`;
    if (tag === 'nav') {
      const links = [...node.querySelectorAll(':scope > a')];
      return `::: links\n${links.map(link => inlineToMarkdown(link)).join('\n')}\n:::`;
    }
    if (tag === 'article' && node.classList.contains('source')) {
      return `::: source ${node.id || ''}\n${childrenToMarkdown(node)}\n:::`;
    }
    if (tag === 'hr') return '***';
    return childrenToMarkdown(node) || inline();
  }

  function pageToMarkdown() {
    [...content.querySelectorAll('.figbox')].forEach((figure, index) => {
      if (!figure.dataset.remembrancerAsset) {
        figure.dataset.remembrancerAsset = `figure-${index + 1}`;
      }
    });
    const entries = [...content.querySelectorAll(':scope > .entry')];
    const sections = entries.length ? entries : [content];
    const markdown = sections.map(section => {
      const inner = section.classList.contains('entry') ? section.querySelector('.inner') : section;
      return [...inner.children].map((node, index) => blockToMarkdown(node, index)).filter(Boolean).join('\n\n');
    });
    const extras = [...content.querySelectorAll(':scope > .panel-note')].map(blockToMarkdown);
    if (extras.length) markdown[markdown.length - 1] += `\n\n${extras.join('\n\n')}`;
    return markdown.join('\n\n---\n\n');
  }

  function renderInline(value) {
    const raw = [];
    value = value.replace(/<span\b[^>]*class=["'][^"']*model[^"']*["'][^>]*>.*?<\/span>/gi, match => {
      raw.push(match);
      return `@@RAW${raw.length - 1}@@`;
    });
    value = escapeHtml(value);
    value = value.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">');
    value = value.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    value = value.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    value = value.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    value = value.replace(/  $/, '<br>');
    raw.forEach((html, index) => { value = value.replace(`@@RAW${index}@@`, html); });
    return value;
  }

  const isSpecial = line => /^(#{1,6} |```|[-*] |\d+\. |\| |::: |\{\{graphic:|Label: |Lead: |Small: |Source: |!\[|\*\*\*$)/.test(line);

  function renderBlocks(source) {
    const lines = source.replace(/\r/g, '').split('\n');
    const output = [];
    for (let i = 0; i < lines.length;) {
      const line = lines[i].trimEnd();
      if (!line.trim()) { i += 1; continue; }
      if (line.startsWith('```')) {
        const body = [];
        i += 1;
        while (i < lines.length && !lines[i].startsWith('```')) body.push(lines[i++]);
        i += 1;
        output.push(`<pre>${escapeHtml(body.join('\n'))}</pre>`);
        continue;
      }
      const directive = line.match(/^::: (note|figure|explanation|side-note|links|source)(?:\s+(.+))?$/);
      if (directive) {
        const body = [];
        i += 1;
        let depth = 1;
        while (i < lines.length && depth) {
          if (/^::: (note|figure|explanation|side-note|links|source)/.test(lines[i])) depth += 1;
          if (lines[i].trim() === ':::') depth -= 1;
          if (depth) body.push(lines[i]);
          i += 1;
        }
        const html = renderBlocks(body.join('\n'));
        const id = directive[2] || '';
        if (directive[1] === 'note') output.push(`<div class="note">${html}</div>`);
        if (directive[1] === 'figure') output.push(`<div class="figbox" data-remembrancer-asset="${escapeHtml(id)}">${html}</div>`);
        if (directive[1] === 'explanation') output.push(`<div class="zoom" id="${escapeHtml(id)}">${html}</div>`);
        if (directive[1] === 'side-note') output.push(`<div class="panel-note" id="${escapeHtml(id)}">${html}</div>`);
        if (directive[1] === 'source') output.push(`<article class="source" id="${escapeHtml(id)}">${html}</article>`);
        if (directive[1] === 'links') {
          const links = body.filter(item => item.trim()).map(item => `<a>${renderInline(item.trim())}</a>`.replace('<a><a ', '<a ').replace('</a></a>', '</a>'));
          output.push(`<nav>${links.join('')}</nav>`);
        }
        continue;
      }
      const graphic = line.match(/^\{\{graphic:([^}]+)}}$/);
      if (graphic) { output.push(graphics.get(graphic[1]) || ''); i += 1; continue; }
      const heading = line.match(/^(#{1,6})\s+(.+)$/);
      if (heading) { const level = heading[1].length; output.push(`<h${level}>${renderInline(heading[2])}</h${level}>`); i += 1; continue; }
      const labelled = line.match(/^(Label|Lead|Small|Source):\s*(.*)$/);
      if (labelled) {
        const classes = {Label:'tag', Lead:'lead', Small:'small', Source:'src'};
        const visiblePrefix = labelled[1] === 'Source' ? 'Source: ' : '';
        output.push(`<p class="${classes[labelled[1]]}">${visiblePrefix}${renderInline(labelled[2])}</p>`);
        i += 1; continue;
      }
      if (line === '***') { output.push('<hr>'); i += 1; continue; }
      if (/^[-*] /.test(line) || /^\d+\. /.test(line)) {
        const ordered = /^\d+\. /.test(line);
        const items = [];
        while (i < lines.length && (ordered ? /^\d+\. /.test(lines[i]) : /^[-*] /.test(lines[i]))) {
          items.push(lines[i].replace(ordered ? /^\d+\. / : /^[-*] /, ''));
          i += 1;
        }
        output.push(`<${ordered ? 'ol' : 'ul'}>${items.map(item => `<li>${renderInline(item)}</li>`).join('')}</${ordered ? 'ol' : 'ul'}>`);
        continue;
      }
      if (line.startsWith('| ') && i + 1 < lines.length && /^\|\s*[-:| ]+\|?$/.test(lines[i + 1])) {
        const rows = [];
        while (i < lines.length && lines[i].trim().startsWith('|')) rows.push(lines[i++]);
        rows.splice(1, 1);
        const cells = row => row.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
        const head = cells(rows[0]);
        output.push(`<div class="table-wrap"><table><thead><tr>${head.map(cell => `<th>${renderInline(cell)}</th>`).join('')}</tr></thead><tbody>${rows.slice(1).map(row => `<tr>${cells(row).map(cell => `<td>${renderInline(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`);
        continue;
      }
      const paragraph = [line.trim()];
      i += 1;
      while (i < lines.length && lines[i].trim() && !isSpecial(lines[i].trimEnd())) paragraph.push(lines[i++].trim());
      output.push(`<p>${renderInline(paragraph.join(' '))}</p>`);
    }
    return output.join('\n');
  }

  function renderContent(markdown) {
    return markdown.split(/\n\s*---\s*\n/).filter(section => section.trim()).map(section =>
      `<section class="entry"><div class="inner">${renderBlocks(section.trim())}</div></section>`
    ).join('\n');
  }

  function contentForSave(markdown) {
    const holder = document.createElement('div');
    holder.innerHTML = renderContent(markdown);
    holder.querySelectorAll('nav a').forEach(link => {
      if (localIndexPaths.has(link.getAttribute('href'))) link.remove();
    });
    return holder.innerHTML;
  }

  function previewDocument(contentHtml) {
    return `<!doctype html><html><head><base href="${location.href}">${pageHead}</head><body><main id="content">${contentHtml}</main>${panelHtml}${pageScripts}</body></html>`;
  }

  const style = document.createElement('style');
  style.textContent = `
    .remembrancer-edit-button { position:fixed; right:12px; bottom:12px; z-index:1000; padding:7px 14px; border:1px solid #000; border-radius:0; background:#fff; color:#000; font:14px Arial,sans-serif; cursor:pointer }
    .remembrancer-shell { position:fixed; inset:0; z-index:9999; display:none; grid-template-rows:43px 1fr; background:#fff; color:#000; font:14px Arial,sans-serif }
    .remembrancer-shell.on { display:grid }
    .remembrancer-bar { display:flex; justify-content:flex-end; align-items:center; padding:5px 8px; border-bottom:1px solid #000 }
    .remembrancer-bar button { padding:6px 14px; border:1px solid #000; border-radius:0; background:#fff; color:#000; font:14px Arial,sans-serif; cursor:pointer }
    .remembrancer-workspace { min-height:0; display:grid; grid-template-columns:1fr 1fr }
    .remembrancer-source { width:100%; height:100%; resize:none; border:0; border-right:1px solid #000; border-radius:0; outline:0; padding:20px; background:#fff; color:#000; font:15px/1.55 ui-monospace,Menlo,monospace; tab-size:2 }
    .remembrancer-preview { width:100%; height:100%; border:0; background:#fff }
    @media(max-width:800px){ .remembrancer-workspace{grid-template-columns:1fr;grid-template-rows:1fr 1fr}.remembrancer-source{border-right:0;border-bottom:1px solid #000} }
  `;
  document.head.appendChild(style);

  const edit = document.createElement('button');
  edit.className = 'remembrancer-edit-button';
  edit.textContent = 'Edit';
  edit.type = 'button';

  const shell = document.createElement('div');
  shell.className = 'remembrancer-shell';
  shell.innerHTML = '<div class="remembrancer-bar"><button type="button">Save</button></div><div class="remembrancer-workspace"><textarea class="remembrancer-source" spellcheck="true" aria-label="Markdown"></textarea><iframe class="remembrancer-preview" title="Preview"></iframe></div>';
  const source = shell.querySelector('textarea');
  const preview = shell.querySelector('iframe');
  const save = shell.querySelector('button');
  let timer;

  function updatePreview() {
    const rendered = renderContent(source.value);
    const frameDocument = preview.contentDocument;
    const frameContent = frameDocument && frameDocument.querySelector('main#content');
    if (!frameContent) {
      preview.srcdoc = previewDocument(rendered);
      return;
    }
    const scroller = frameDocument.scrollingElement;
    const oldRange = Math.max(1, scroller.scrollHeight - scroller.clientHeight);
    const position = scroller.scrollTop / oldRange;
    frameContent.innerHTML = rendered;
    const newRange = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
    scroller.scrollTop = position * newRange;
  }
  source.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(updatePreview, 180);
  });
  edit.addEventListener('click', () => {
    source.value = pageToMarkdown();
    source.setSelectionRange(0, 0);
    source.scrollTop = 0;
    shell.classList.add('on');
    updatePreview();
    source.focus();
    source.scrollTop = 0;
  });
  save.addEventListener('click', async () => {
    save.disabled = true;
    try {
      const response = await fetch('/__remembrancer/save', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({path:location.pathname, content:contentForSave(source.value)})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      location.reload();
    } catch (error) {
      save.disabled = false;
      alert(`Save failed: ${error.message}`);
    }
  });

  document.body.append(edit, shell);
})();
