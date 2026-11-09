// Convert the Marp deck (slides.md + tradingdev theme) into an editable .pptx.
// Usage: node build_pptx.js slides.md out.pptx
// Layout follows theme.css at 96 px per inch (1280x720 px = 13.333x7.5 in, 1 px = 0.75 pt).
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const [SRC, OUT] = process.argv.slice(2);
const md = fs.readFileSync(SRC, "utf8");

const C = {
  bg: "F8F7F3", ink: "16343C", accent: "087F79", muted: "567076", rule: "C9D4D2", code: "E5EEEA",
  dark: "16343C", darkInk: "F8F7F3", darkAccent: "80D8C4", darkMuted: "B7CFCC",
};
const FONT = "Microsoft JhengHei";
const MONO = "Consolas";
const LANG = "zh-TW";
const px = (v) => v / 96;    // px -> in
const pt = (v) => v * 0.75;  // px -> pt
const SW = 13.333, SH = 7.5;
const LH = 1.45;             // body line height (exact spacing, x font size)
const TLH = 1.3;             // table line height

// ---------- parse ----------
function parseSlides(src) {
  const chunks = src.split(/\n---\n/);
  const slides = [];
  let header = "";
  for (const chunk of chunks) {
    const s = { cls: "", header, footer: "", notes: [], blocks: [] };
    let localHeader = null;
    const body = chunk.replace(/<!--([\s\S]*?)-->/g, (_, c) => {
      const t = c.trim();
      if (/^marp:\s*true/m.test(t)) return "";
      const m = t.match(/^(_?)(class|header|footer|paginate)\s*:\s*(.*)$/);
      if (m && !t.includes("\n")) {
        const val = m[3].trim().replace(/^"(.*)"$/, "$1");
        if (m[2] === "class") s.cls = val;
        if (m[2] === "footer") s.footer = val;
        if (m[2] === "header") { if (m[1]) localHeader = val; else header = val; }
      } else s.notes.push(t);
      return "";
    });
    s.header = localHeader !== null ? localHeader : header;
    s.blocks = parseBlocks(body);
    if (s.blocks.length) slides.push(s);
  }
  return slides;
}

function parseBlocks(body) {
  const lines = body.split("\n");
  const blocks = [];
  const isStart = (l) => /^(#{1,3} |\||- |\d+\. )/.test(l);
  for (let i = 0; i < lines.length; ) {
    const l = lines[i];
    if (!l.trim()) { i++; continue; }
    let m;
    if ((m = l.match(/^(#{1,3}) (.*)$/))) { blocks.push({ t: "h" + m[1].length, text: m[2] }); i++; continue; }
    if (l.startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        if (!/^\|\s*:?-{3,}/.test(lines[i]))
          rows.push(lines[i].trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((x) => x.trim()));
        i++;
      }
      blocks.push({ t: "table", rows });
      continue;
    }
    if (/^(- |\d+\. )/.test(l)) {
      const ordered = /^\d+\. /.test(l);
      const items = [];
      while (i < lines.length && /^(- |\d+\. )/.test(lines[i])) { items.push(lines[i].replace(/^(- |\d+\. )/, "")); i++; }
      blocks.push({ t: ordered ? "ol" : "ul", items });
      continue;
    }
    const para = [];
    while (i < lines.length && lines[i].trim() && !isStart(lines[i])) { para.push(lines[i]); i++; }
    const text = para.join("\n");
    const caption = /^\*[^*][\s\S]*[^*]\*$/.test(text) && !/\*\*/.test(text);
    blocks.push(caption ? { t: "caption", text: text.slice(1, -1) } : { t: "p", text });
  }
  return blocks;
}

// Inline markdown -> styled segments {text, bold, code, italic, link, br}
function inline(s, st = {}) {
  const out = [];
  const re = /`([^`]+)`|\[((?:[^\]`]|`[^`]*`)+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*|\*([^*\n]+)\*/g;
  let last = 0, m;
  const plain = (t) => t.split("\n").forEach((x, k) => { if (k) out.push({ ...st, text: "", br: true }); if (x) out.push({ ...st, text: x }); });
  while ((m = re.exec(s))) {
    plain(s.slice(last, m.index));
    if (m[1] !== undefined) out.push({ ...st, text: m[1], code: true });
    else if (m[2] !== undefined) out.push(...inline(m[2], { ...st, link: m[3] }));
    else if (m[4] !== undefined) out.push(...inline(m[4], { ...st, bold: true }));
    else out.push(...inline(m[5], { ...st, italic: true }));
    last = re.lastIndex;
  }
  plain(s.slice(last));
  return out;
}

// ---------- measure ----------
const isWide = (c) => (c >= 0x2e80 && c <= 0x9fff) || (c >= 0x3000 && c <= 0x303f) || (c >= 0xff00 && c <= 0xffef) || (c >= 0xf900 && c <= 0xfaff);
function charW(ch, mono) {
  const c = ch.codePointAt(0);
  if (isWide(c)) return 1.0;
  if (mono) return 0.55;
  if (ch === " ") return 0.3;
  if (/[iljtf.,:;'|!()\[\]]/.test(ch)) return 0.32;
  if (/[mwMW]/.test(ch)) return 0.88;
  if (/[A-Z0-9#]/.test(ch)) return 0.64;
  return 0.56;
}
// Number of lines a list of segments wraps to inside maxW points.
function countLines(segs, size, maxW) {
  maxW *= 0.95; // safety margin for font substitution
  let lines = 1, w = 0;
  for (const g of segs) {
    if (g.br) { lines++; w = 0; continue; }
    const sz = g.code ? size * 0.85 : size;
    const toks = g.text.match(/[⺀-鿿　-〿＀-￯]|[^\s⺀-鿿　-〿＀-￯]+\s*|\s+/g) || [];
    for (const t of toks) {
      const tw = [...t].reduce((a, ch) => a + charW(ch, g.code) * sz, 0);
      if (w + tw > maxW && w > 0) { lines++; w = tw; } else w += tw;
      while (w > maxW) { lines++; w -= maxW; }
    }
  }
  return lines;
}
const naturalW = (segs, size) => segs.reduce((a, g) => a + [...(g.text || "")].reduce((b, ch) => b + charW(ch, g.code) * (g.code ? size * 0.85 : size), 0), 0);
const minWordW = (segs, size) => Math.max(0, ...segs.flatMap((g) => (g.text.match(/[^\s⺀-鿿　-〿＀-￯]+/g) || []).map((w) => [...w].reduce((b, ch) => b + charW(ch, g.code) * (g.code ? size * 0.85 : size), 0))));

// ---------- render ----------
function runs(segs, ctx, extra = {}) {
  const arr = segs.filter((g) => g.text || g.br).map((g, k) => {
    const o = { fontFace: g.code ? MONO : FONT, fontSize: g.code ? +(ctx.size * 0.85).toFixed(1) : ctx.size, color: ctx.ink, lang: LANG, ...extra };
    if (g.bold) { o.bold = true; o.color = ctx.strong; }
    if (ctx.bold) o.bold = true;
    if (g.italic) o.italic = true;
    if (g.code && !ctx.dark) o.highlight = C.code;
    if (g.link) {
      const im = g.link.match(/^index\.html#(\d+)$/);
      o.hyperlink = im ? { slide: +im[1] } : { url: g.link };
      o.color = ctx.link || o.color;
      o.underline = { style: "sng" };
    }
    if (g.br && k > 0) o.softBreakBefore = true;
    return { text: g.text, options: o };
  });
  return arr.filter((r) => r.text !== "" || r.options.softBreakBefore);
}

function renderSlide(pres, s, idx, report) {
  const dark = ["cover", "chapter", "closing"].includes(s.cls);
  const ink = dark ? C.darkInk : C.ink, strong = dark ? C.darkAccent : C.accent, muted = dark ? C.darkMuted : C.muted;
  const slide = pres.addSlide({ masterName: dark ? "DARK" : "LIGHT", sectionTitle: s.section });
  if (s.notes.length) slide.addNotes(s.notes.join("\n\n"));

  const X = px(80), W = SW - px(160);
  const top = px(dark ? 64 : 82), bottom = SH - px(76);
  const base = s.cls === "compact" ? 27 : s.cls === "references" ? 25 : 30;

  // Build a layout at a given scale, return {items, height}.
  function layout(scale) {
    const items = [];
    let y = 0;
    const f = (v) => +(pt(v) * scale).toFixed(1);
    s.blocks.forEach((b, bi) => {
      const gap = bi === 0 ? 0 : px(14) * scale;
      if (b.t === "h1" || b.t === "h2" || b.t === "h3") {
        let size = b.t === "h1" ? pt(76) : b.t === "h3" ? pt(32) : (s.cls === "chapter" || s.cls === "closing") ? pt(58) : pt(46);
        const maxW = (s.cls === "chapter" || s.cls === "closing") ? px(1000) : W;
        const segs = inline(b.text);
        const lh = size * 1.25;
        const h = countLines(segs, size, maxW * 72) * lh / 72;
        y += gap;
        items.push({ kind: "text", y, h, w: maxW, runs: runs(segs, { size, ink, strong: ink, dark, link: strong, bold: true }), lh });
        y += h + (b.t === "h1" ? px(20) : b.t === "h2" ? px(34) * scale : px(10));
        return;
      }
      if (b.t === "p" || b.t === "caption") {
        let size = b.t === "caption" ? f(21) : (s.cls === "cover" || s.cls === "chapter" || s.cls === "closing") ? f(34) : f(base);
        const maxW = (s.cls === "chapter" || s.cls === "closing") ? px(1030) : W;
        const segs = inline(b.text);
        const lh = size * LH;
        y += b.t === "caption" ? px(20) * scale : gap;
        const h = countLines(segs, size, maxW * 72) * lh / 72;
        items.push({ kind: "text", y, h, w: maxW, runs: runs(segs, { size, ink: b.t === "caption" ? muted : ink, strong, dark, link: strong }), lh });
        y += h;
        return;
      }
      if (b.t === "ul" || b.t === "ol") {
        const size = f(base), lh = size * LH, indent = size * 1.2, after = (s.cls === "references" ? 13 : 10) * 0.75 * scale;
        y += gap;
        let h = 0;
        const all = [];
        b.items.forEach((it, k) => {
          const segs = inline(it);
          h += countLines(segs, size, W * 72 - indent) * lh + (k < b.items.length - 1 ? after : 0);
          const bullet = b.t === "ol" ? { type: "number", indent } : { indent };
          // pptxgenjs starts a new paragraph at every run that carries `bullet`,
          // so paragraph options go on the item's first run only.
          const r = runs(segs, { size, ink, strong, dark, link: strong });
          Object.assign(r[0].options, { bullet, paraSpaceAfter: k < b.items.length - 1 ? after : 0 });
          r[r.length - 1].options.breakLine = k < b.items.length - 1;
          all.push(...r);
        });
        h /= 72;
        items.push({ kind: "text", y, h, w: W, runs: all, lh });
        y += h;
        return;
      }
      if (b.t === "table") {
        const size = s.cls === "compact" ? f(23) : f(25);
        const padV = px(s.cls === "compact" ? 13 : 16) * scale, padH = px(s.cls === "compact" ? 16 : 18);
        const cells = b.rows.map((r) => r.map((c) => inline(c)));
        const ncol = cells[0].length;
        const Wpt = W * 72, padPt = padH * 72 * 2;
        const nat = [...Array(ncol)].map((_, j) => Math.max(...cells.map((r) => naturalW(r[j] || [], size))) + padPt);
        const mn = [...Array(ncol)].map((_, j) => Math.max(size * 3, ...cells.map((r) => minWordW(r[j] || [], size))) + padPt);
        let colW;
        const sumNat = nat.reduce((a, v) => a + v, 0), sumMin = mn.reduce((a, v) => a + v, 0);
        if (sumNat <= Wpt) colW = nat.map((v) => v * Wpt / sumNat);
        else colW = mn.map((v, j) => v + (Wpt - sumMin) * (nat[j] - mn[j]) / (sumNat - sumMin));
        const lh = size * TLH;
        const rowH = cells.map((r) => Math.max(...r.map((c, j) => countLines(c, size, colW[j] - padPt))) * lh / 72 + padV * 2);
        const border = () => [{ type: "none" }, { type: "none" }, { type: "solid", pt: 0.75, color: C.rule }, { type: "none" }];
        const rows = cells.map((r, ri) => r.map((c) => ({
          text: c.length ? runs(c, { size, ink: ri === 0 ? C.accent : ink, strong: ri === 0 ? C.accent : strong, dark, link: strong, bold: ri === 0 }) : "",
          options: { border: border(), valign: "top", margin: [padV, padH, padV, padH], lineSpacing: +lh.toFixed(1), fontFace: FONT, fontSize: size, color: ink },
        })));
        y += gap + px(6) * scale;
        const h = rowH.reduce((a, v) => a + v, 0);
        items.push({ kind: "table", y, h, rows, colW: colW.map((v) => v / 72), rowH });
        y += h + px(6) * scale;
        return;
      }
    });
    return { items, height: y };
  }

  const avail = bottom - top - (s.footer ? px(12) : 0);
  let scale = 1, L = layout(1);
  while (L.height > avail && scale > 0.8) { scale -= 0.025; L = layout(scale); }
  if (scale < 1) report.push(`slide ${idx}: scaled to ${(scale * 100).toFixed(1)}%`);
  if (L.height > avail) report.push(`slide ${idx}: OVERFLOW ${(L.height - avail).toFixed(2)} in`);

  const y0 = dark ? top + Math.max(0, (bottom - top - L.height) / 2) : top;
  for (const it of L.items) {
    if (it.kind === "text") {
      slide.addText(it.runs, {
        x: X, y: y0 + it.y, w: it.w, h: it.h + 0.05, margin: 0, valign: "top", isTextBox: true, fit: "none",
        lineSpacing: +it.lh.toFixed(1), fontFace: FONT, color: ink, objectName: `text-${Math.round(it.y * 100)}`,
      });
    } else {
      slide.addTable(it.rows, { x: X, y: y0 + it.y, w: W, colW: it.colW, rowH: it.rowH, autoPage: false, objectName: "table" });
    }
  }
  if (s.header) slide.addText(s.header, { x: X, y: px(24), w: W, h: 0.3, margin: 0, isTextBox: true, fontFace: FONT, fontSize: pt(18), bold: true, color: muted, charSpacing: 0.5, lang: LANG, objectName: "header" });
  if (s.footer) {
    const segs = inline(s.footer);
    slide.addText(runs(segs, { size: pt(16), ink: muted, strong: muted, dark, link: muted }), {
      x: X, y: SH - px(29) - 0.3, w: SW - px(80) - px(105), h: 0.3, margin: 0, valign: "bottom", isTextBox: true, fontFace: FONT, objectName: "footer",
    });
  }
}

async function main() {
  const slides = parseSlides(md);
  const titleMatch = md.match(/^title:\s*(.*)$/m);
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = titleMatch ? titleMatch[1] : "TradingDev";
  pres.author = "TradingDev";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  const num = (color) => ({ x: SW - px(38) - 0.8, y: SH - px(25) - 0.28, w: 0.8, h: 0.28, align: "right", fontFace: FONT, fontSize: pt(17), color, margin: 0 });
  pres.defineSlideMaster({ title: "LIGHT", background: { color: C.bg }, slideNumber: num(C.muted) });
  pres.defineSlideMaster({ title: "DARK", background: { color: C.dark }, slideNumber: num(C.darkMuted) });

  // Sections: opening, one per chapter, closing.
  let section = "開場";
  slides.forEach((s) => {
    if (s.cls === "chapter") section = s.blocks.find((b) => b.t === "h2").text.replace(/：.*$/, "");
    if (s.cls === "closing") section = "結語";
    s.section = section;
  });
  const declared = new Set();
  const report = [];
  slides.forEach((s, i) => {
    if (!declared.has(s.section)) { pres.addSection({ title: s.section }); declared.add(s.section); }
    renderSlide(pres, s, i + 1, report);
  });
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, {
    name: "TradingDev", headFontFace: FONT, bodyFontFace: FONT,
    colors: { dk1: C.ink, lt1: "FFFFFF", dk2: C.dark, lt2: C.bg, accent1: C.accent, accent2: "D2714A", accent3: C.darkAccent, accent4: C.muted, accent5: C.rule, accent6: "166A65", hlink: C.accent, folHlink: C.accent },
  });
  console.log(`${slides.length} slides -> ${OUT}`);
  console.log(report.length ? report.join("\n") : "all slides fit at 100%");
}
main().catch((e) => { console.error(e); process.exit(1); });
