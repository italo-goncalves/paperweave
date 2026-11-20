/**
 * PaperWeave's author-year reference style (ADR 0004).
 *
 * References are stored as fields in references.yaml; this module derives the citation
 * label and the formatted text. latex/paperweave.bst produces the same text in the
 * Linear version, and scripts/test_references.py checks that the two agree.
 *
 *   Damianou A C, Lawrence N D (2013) Deep Gaussian processes. In: Proceedings of …, pp 207–215. https://doi.org/…
 *
 * Self-contained so Node can run it without a bundler.
 */

export interface ReferenceFields {
  type: "article" | "inproceedings" | "incollection" | "book" | "thesis" | "report" | "misc";
  /** "Family, Given" per person, in order; an organisation has no comma. */
  author: string[];
  editor?: string[];
  year: number | string;
  title: string;
  journal?: string;
  booktitle?: string;
  volume?: string | number;
  number?: string | number;
  pages?: string | number;
  edition?: string;
  publisher?: string;
  address?: string;
  school?: string;
  institution?: string;
  /** Thesis or report kind, e.g. "PhD thesis" or "Technical report". */
  kind?: string;
  note?: string;
  /** Bare DOI, such as 10.1007/s11004-025-10187-4. */
  doi?: string;
  url?: string;
}

export interface FormattedReference {
  label: string;
  text: string;
}

function splitName(name: string): { family: string; given: string } {
  const i = name.indexOf(",");
  return i < 0 ? { family: name.trim(), given: "" } : { family: name.slice(0, i).trim(), given: name.slice(i + 1).trim() };
}

/** "Andreas C." → "A C"; "Jean-Paul" → "J P", as BibTeX gives with a tie between initials. */
function initials(given: string): string {
  return given
    .split(/[\s-]+/)
    .filter(Boolean)
    .map((p) => [...p][0])
    .join(" ");
}

function formatName(name: string): string {
  const { family, given } = splitName(name);
  return given ? `${family} ${initials(given)}` : family;
}

const names = (list: string[]) => list.map(formatName).join(", ");

function labelAuthors(list: string[]): string {
  const fam = list.map((n) => splitName(n).family);
  if (fam.length === 0) return "Anonymous";
  if (fam.length === 1) return fam[0];
  if (fam.length === 2) return `${fam[0]} and ${fam[1]}`;
  return `${fam[0]} et al.`;
}

const endWithStop = (s: string) => (/[.?!]$/.test(s) ? s : `${s}.`);
const str = (v: unknown) => (v === undefined || v === null || v === "" ? "" : String(v));

function venue(r: ReferenceFields): string {
  const vol = str(r.volume);
  const num = str(r.number);
  const pages = str(r.pages);
  const at = (parts: string[]) => parts.filter(Boolean).join(", ");
  switch (r.type) {
    case "article": {
      let s = str(r.journal);
      if (vol) s += ` ${vol}`;
      if (num) s += `(${num})`;
      if (pages) s += vol || num ? `:${pages}` : ` ${pages}`;
      return s.trim();
    }
    case "inproceedings":
    case "incollection": {
      const eds = r.editor?.length ? `${names(r.editor)} (${r.editor.length > 1 ? "eds" : "ed"}) ` : "";
      const book = str(r.booktitle) && `In: ${eds}${r.booktitle}`;
      return at([book, vol && `vol ${vol}`, str(r.publisher), str(r.address), pages && `pp ${pages}`]);
    }
    case "book":
      return at([str(r.edition) && `${r.edition} edn`, str(r.publisher), str(r.address)]);
    case "thesis":
      return at([str(r.kind) || "PhD thesis", str(r.school), str(r.address)]);
    case "report":
      return at([(str(r.kind) || "Tech. rep.") + (num ? ` ${num}` : ""), str(r.institution), str(r.address)]);
    default:
      return at([str(r.publisher), str(r.address)]);
  }
}

function link(r: ReferenceFields): string {
  if (r.doi) return `https://doi.org/${r.doi}`;
  return str(r.url);
}

/**
 * For sorting the same way as BibTeX's `purify$` then lowercase: hyphens, ties and white
 * space become spaces, other ASCII symbols go, letters beyond ASCII stay as they are.
 */
export function purify(s: string): string {
  return s
    .replace(/[-~\s]/g, " ")
    .replace(/[\x00-\x1f\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7f]/g, "")
    .replace(/[A-Z]/g, (c) => c.toLowerCase());
}

/** Labels and texts for every reference of a Work, with a/b suffixes for equal labels. */
export function formatReferences(refs: Record<string, ReferenceFields>): Record<string, FormattedReference> {
  const groups = new Map<string, string[]>();
  for (const [key, r] of Object.entries(refs)) {
    const base = `${labelAuthors(r.author ?? [])} ${str(r.year)}`;
    groups.set(base, [...(groups.get(base) ?? []), key]);
  }
  const suffix: Record<string, string> = {};
  for (const keys of groups.values()) {
    if (keys.length < 2) continue;
    const sortKey = (k: string) => `${purify(str(refs[k].title))}    ${k}`;
    keys.sort((a, b) => (sortKey(a) < sortKey(b) ? -1 : 1)).forEach((k, i) => (suffix[k] = String.fromCharCode(97 + i)));
  }

  const out: Record<string, FormattedReference> = {};
  for (const [key, r] of Object.entries(refs)) {
    const year = `${str(r.year)}${suffix[key] ?? ""}`;
    const head = `${names(r.author ?? [])} (${year}) ${endWithStop(str(r.title))}`;
    const v = venue(r);
    const parts = [head, v && endWithStop(v), str(r.note) && endWithStop(str(r.note)), link(r)].filter(Boolean);
    out[key] = { label: `${labelAuthors(r.author ?? [])} ${year}`, text: parts.join(" ") };
  }
  return out;
}
