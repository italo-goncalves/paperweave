import MarkdownIt from "markdown-it";
import katex from "katex";
import type { Work } from "./work";

const md = new MarkdownIt({ html: true, linkify: true, typographer: true });

const escapeHtml = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const KEY = "([A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9])";

function citation(work: Work, key: string, narrative: boolean): string {
  const ref = work.references[key];
  if (!ref) return `<span class="cite cite-missing">@${escapeHtml(key)}</span>`;
  const m = ref.label.match(/^(.*) (\d{4}[a-z]?)$/);
  const shown = narrative && m ? `${m[1]} (${m[2]})` : ref.label;
  return `<span class="cite" title="${escapeHtml(ref.text)}">${escapeHtml(shown)}</span>`;
}

interface Placeholders {
  math: { tex: string; display: boolean }[];
  figures: string[];
}

function preprocess(work: Work, src: string, ph: Placeholders): string {
  let s = src.replace(/\r\n/g, "\n");

  // Math first, so nothing inside it is touched by later steps.
  s = s.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
    ph.math.push({ tex, display: true });
    return `\n\nMATHPH${ph.math.length - 1}X\n\n`;
  });
  s = s.replace(/\$([^$\n]+?)\$/g, (_, tex) => {
    ph.math.push({ tex, display: false });
    return `MATHPH${ph.math.length - 1}X`;
  });

  // Figures on their own line.
  s = s.replace(/^!\[\[([a-z0-9-]+)\]\]\s*$/gm, (_, id) => {
    ph.figures.push(id);
    return `\n\nFIGPH${ph.figures.length - 1}X\n\n`;
  });

  // Inline links.
  s = s.replace(/\[\[([a-z0-9-]+)(?:\|([^\]]*))?\]\]/g, (_, id, text) => {
    const node = work.nodes[id];
    const label = escapeHtml(text ?? node?.title ?? id).replace(/\$([^$\n]+?)\$/g, (_m: string, tex: string) => {
      // Titles may contain math, which was not present when math was extracted above.
      ph.math.push({ tex, display: false });
      return `MATHPH${ph.math.length - 1}X`;
    });
    const cls = node ? "node-link" : "node-link node-link-missing";
    return `<a class="${cls}" data-node="${id}" href="#${id}">${label}</a>`;
  });

  // Parenthetical citations: [@A; @B] or [prefix; @A].
  s = s.replace(/\[([^\[\]]*@[^\[\]]*)\]/g, (whole, inner: string) => {
    const parts = inner.split(";").map((p) => p.trim());
    if (!parts.some((p) => /^@/.test(p))) return whole;
    const rendered = parts.map((p) => {
      const m = p.match(new RegExp(`^@${KEY}$`));
      return m ? citation(work, m[1], false) : escapeHtml(p);
    });
    return `(${rendered.join("; ")})`;
  });

  // Narrative citations: @Key in running text.
  s = s.replace(new RegExp(`(^|[\\s(])@${KEY}`, "g"), (_, pre, key) => pre + citation(work, key, true));

  return s;
}

function renderMath(tex: string, display: boolean): string {
  try {
    return katex.renderToString(tex, { displayMode: display, throwOnError: false, strict: "ignore" });
  } catch {
    return `<code>${escapeHtml(tex)}</code>`;
  }
}

function postprocess(work: Work, html: string, ph: Placeholders): string {
  html = html.replace(/<p>FIGPH(\d+)X<\/p>/g, (_, i) => figureHtml(work, ph.figures[Number(i)]));
  html = html.replace(/<p>MATHPH(\d+)X<\/p>/g, (_, i) => {
    const m = ph.math[Number(i)];
    return `<div class="math-display">${renderMath(m.tex, true)}</div>`;
  });
  html = html.replace(/MATHPH(\d+)X/g, (_, i) => {
    const m = ph.math[Number(i)];
    return renderMath(m.tex, m.display);
  });
  return html;
}

export function figureHtml(work: Work, id: string): string {
  const fig = work.figures[id];
  if (!fig) return `<p class="missing">Missing figure ${escapeHtml(id)}</p>`;
  return `<figure class="figure" data-fig="${id}"><img src="${fig.url}" alt="" loading="lazy" data-fig="${id}"/><figcaption>${renderInline(work, fig.caption)}</figcaption></figure>`;
}

export function renderMarkdown(work: Work, src: string): string {
  const ph: Placeholders = { math: [], figures: [] };
  return postprocess(work, md.render(preprocess(work, src, ph)), ph);
}

export function renderInline(work: Work, src: string): string {
  const ph: Placeholders = { math: [], figures: [] };
  return postprocess(work, md.renderInline(preprocess(work, src, ph)), ph);
}

/** Plain-text version of a title, for places that cannot show HTML (graph labels). */
export function plainTitle(src: string): string {
  const symbols: Record<string, string> = { Sigma: "Σ", sigma: "σ", mu: "μ", Lambda: "Λ", lambda: "λ" };
  return src
    .replace(/\$([^$]*)\$/g, (_, tex: string) =>
      tex.replace(/\\boldsymbol\s*/g, "").replace(/\\([A-Za-z]+)/g, (__, name) => symbols[name] ?? name).replace(/[{}]/g, ""),
    )
    .trim();
}
