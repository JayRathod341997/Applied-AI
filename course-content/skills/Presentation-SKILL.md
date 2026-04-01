---
name: pptx
description: "Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill — Professional Format Guide

## Three Ways to Work with PPTX

| Task | Method |
|------|--------|
| Read/analyze an existing `.pptx` | `python -m markitdown presentation.pptx` |
| Edit or modify a template | Use the editing workflow (unpack → edit → pack) — see [editing.md](editing.md) |
| Create from scratch | Use PptxGenJS (Node.js) — see [pptxgenjs.md](pptxgenjs.md) |

---

## Setup

```bash
npm install -g pptxgenjs react-icons react react-dom sharp
pip install "markitdown[pptx]" Pillow --break-system-packages
```

---

## Basic Structure (PptxGenJS)

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';   // 10" × 5.625"
pres.title = 'My Presentation';

let slide = pres.addSlide();
slide.addText("Hello!", { x: 0.5, y: 0.5, fontSize: 36, bold: true, color: "1E2761" });

pres.writeFile({ fileName: "output.pptx" });
```

---

## Professional Color Palettes

Pick a theme that fits your topic — never default to plain blue:

| Theme | Primary | Secondary | Accent | Use Case |
|-------|---------|-----------|--------|----------|
| **Colorful Academic** | `1E3A5F` (navy) | `0D9488` (teal) | `F97316` / `8B5CF6` (orange/purple) | Research, education |
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) | Corporate, formal |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) | Tech, modern |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) | Marketing, impact |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) | Healthcare, wellness |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) | Creative, organic |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) | Environmental, nature |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) | Startups, energetic |

**Rule:** One color dominates (60–70%), one supports, one accents. Never equal weight.

---

## Typography Standards

| Element | Size | Style |
|---------|------|-------|
| Slide title | 36–44pt | Bold |
| Section header | 20–24pt | Bold |
| Body text | 14–16pt | Regular |
| Captions | 10–12pt | Muted |

**Best font pairings:** `Georgia + Calibri`, `Arial Black + Arial`, `Cambria + Calibri`, `Trebuchet MS + Calibri`

---

## 6 Professional Slide Layouts

### Colorful & Modern Academic Style
Navy (`1E3A5F`) + Teal (`0D9488`) + Orange (`F97316`) + Purple (`8B5CF6`)

---

### 01 — Title + Agenda Slide

Split dark panel with colored accent bar, research metadata, and numbered agenda list.

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

let slide = pres.addSlide();

// Left panel (dark navy)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 4.5, h: 5.625,
  fill: { color: "1E3A5F" }
});

// Accent bar (teal)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 4.5, y: 0, w: 0.08, h: 5.625,
  fill: { color: "0D9488" }
});

// Title on dark panel
slide.addText("Research Title Here", {
  x: 0.5, y: 1.5, w: 3.5, h: 1.2,
  fontSize: 28, bold: true, color: "FFFFFF", fontFace: "Georgia"
});

// Metadata
slide.addText([
  { text: "Dr. Jane Smith", options: { breakLine: true } },
  { text: "Department of Research", options: { breakLine: true } },
  { text: "University Name • 2024", options: {} }
], {
  x: 0.5, y: 3.2, w: 3.5, h: 1.5,
  fontSize: 12, color: "94A3B8", fontFace: "Calibri"
});

// Right panel (light)
slide.background = { color: "F8FAFC" };

// Agenda header
slide.addText("AGENDA", {
  x: 5, y: 0.8, w: 4.5, h: 0.5,
  fontSize: 14, bold: true, color: "0D9488", charSpacing: 4, fontFace: "Calibri"
});

// Agenda items with colored numbers
const agendaItems = [
  { num: "01", text: "Introduction & Background", color: "0D9488" },
  { num: "02", text: "Methodology Overview", color: "F97316" },
  { num: "03", text: "Key Findings", color: "8B5CF6" },
  { num: "04", text: "Conclusions & Next Steps", color: "1E3A5F" }
];

agendaItems.forEach((item, i) => {
  slide.addText(item.num, {
    x: 5, y: 1.5 + (i * 0.9), w: 0.6, h: 0.5,
    fontSize: 24, bold: true, color: item.color, fontFace: "Georgia"
  });
  slide.addText(item.text, {
    x: 5.7, y: 1.55 + (i * 0.9), w: 3.8, h: 0.5,
    fontSize: 16, color: "334155", fontFace: "Calibri"
  });
});

pres.writeFile({ fileName: "01_title_agenda.pptx" });
```

---

### 02 — Stats / KPI Callouts

4-card grid with colored left-border accents, large stat numbers, and delta indicators.

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

let slide = pres.addSlide();
slide.background = { color: "F8FAFC" };

// Title
slide.addText("Key Performance Indicators", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 28, bold: true, color: "1E3A5F", fontFace: "Georgia", margin: 0
});

const makeShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.08 });

const stats = [
  { value: "2,847", label: "Total Participants", delta: "+12.5%", deltaColor: "059669", accent: "0D9488" },
  { value: "94.2%", label: "Completion Rate", delta: "+3.8%", deltaColor: "059669", accent: "F97316" },
  { value: "4.7/5", label: "Satisfaction Score", delta: "+0.4", deltaColor: "059669", accent: "8B5CF6" },
  { value: "$1.2M", label: "Total Investment", delta: "-2.1%", deltaColor: "DC2626", accent: "1E3A5F" }
];

stats.forEach((stat, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.5 + (col * 4.6);
  const y = 1.3 + (row * 2);

  // Card background
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 4.3, h: 1.8,
    fill: { color: "FFFFFF" },
    shadow: makeShadow()
  });

  // Left accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 0.08, h: 1.8,
    fill: { color: stat.accent }
  });

  // Stat value
  slide.addText(stat.value, {
    x: x + 0.3, y: y + 0.25, w: 2.5, h: 0.8,
    fontSize: 36, bold: true, color: "1E3A5F", fontFace: "Georgia", margin: 0
  });

  // Delta indicator
  slide.addText(stat.delta, {
    x: x + 2.8, y: y + 0.4, w: 1.2, h: 0.4,
    fontSize: 14, bold: true, color: stat.deltaColor, align: "right", fontFace: "Calibri", margin: 0
  });

  // Label
  slide.addText(stat.label, {
    x: x + 0.3, y: y + 1.1, w: 3.7, h: 0.5,
    fontSize: 14, color: "64748B", fontFace: "Calibri", margin: 0
  });
});

pres.writeFile({ fileName: "02_stats_kpi.pptx" });
```

---

### 03 — Two-Column Content

Hypothesis vs. Results layout with distinct colored backgrounds per column.

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

let slide = pres.addSlide();
slide.background = { color: "F8FAFC" };

// Title
slide.addText("Hypothesis vs. Results", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 28, bold: true, color: "1E3A5F", fontFace: "Georgia", margin: 0
});

const makeShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.08 });

// Left column - Hypothesis (teal tint)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 4,
  fill: { color: "F0FDFA" },
  shadow: makeShadow()
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: "0D9488" }
});
slide.addText("HYPOTHESIS", {
  x: 0.5, y: 1.25, w: 4.3, h: 0.5,
  fontSize: 14, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri"
});

slide.addText([
  { text: "Primary Assumption", options: { bold: true, breakLine: true } },
  { text: "We hypothesized that intervention X would lead to a 20% improvement in outcome Y.", options: { breakLine: true, breakLine: true } },
  { text: "Secondary Factors", options: { bold: true, breakLine: true } },
  { text: "Environmental conditions and participant demographics were expected to influence results.", options: {} }
], {
  x: 0.7, y: 1.9, w: 3.9, h: 3,
  fontSize: 13, color: "334155", fontFace: "Calibri", valign: "top"
});

// Right column - Results (orange tint)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 4,
  fill: { color: "FFF7ED" },
  shadow: makeShadow()
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: "F97316" }
});
slide.addText("RESULTS", {
  x: 5.2, y: 1.25, w: 4.3, h: 0.5,
  fontSize: 14, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri"
});

slide.addText([
  { text: "Key Finding", options: { bold: true, breakLine: true } },
  { text: "Intervention X achieved a 27% improvement, exceeding initial expectations.", options: { breakLine: true, breakLine: true } },
  { text: "Statistical Significance", options: { bold: true, breakLine: true } },
  { text: "Results were significant at p < 0.001 with 95% confidence interval of 24-30%.", options: {} }
], {
  x: 5.4, y: 1.9, w: 3.9, h: 3,
  fontSize: 13, color: "334155", fontFace: "Calibri", valign: "top"
});

pres.writeFile({ fileName: "03_two_column.pptx" });
```

---

### 04 — Timeline / Process

Dark background with horizontal gradient connector and numbered phase circles.

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

let slide = pres.addSlide();
slide.background = { color: "1E3A5F" };

// Title
slide.addText("Research Timeline", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 28, bold: true, color: "FFFFFF", fontFace: "Georgia", margin: 0
});

// Connector line
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1.2, y: 2.5, w: 7.6, h: 0.06,
  fill: { color: "0D9488" }
});

const phases = [
  { num: "1", title: "Planning", desc: "Q1 2024", color: "0D9488" },
  { num: "2", title: "Data Collection", desc: "Q2 2024", color: "14B8A6" },
  { num: "3", title: "Analysis", desc: "Q3 2024", color: "F97316" },
  { num: "4", title: "Publication", desc: "Q4 2024", color: "8B5CF6" }
];

phases.forEach((phase, i) => {
  const x = 1.2 + (i * 2.3);
  
  // Circle background
  slide.addShape(pres.shapes.OVAL, {
    x: x, y: 2.1, w: 0.9, h: 0.9,
    fill: { color: phase.color }
  });
  
  // Phase number
  slide.addText(phase.num, {
    x: x, y: 2.15, w: 0.9, h: 0.85,
    fontSize: 24, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: "Georgia"
  });
  
  // Title
  slide.addText(phase.title, {
    x: x - 0.5, y: 3.2, w: 2, h: 0.5,
    fontSize: 14, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri"
  });
  
  // Description
  slide.addText(phase.desc, {
    x: x - 0.5, y: 3.6, w: 2, h: 0.4,
    fontSize: 12, color: "94A3B8", align: "center", fontFace: "Calibri"
  });
});

// Bottom detail cards
const details = [
  "Define scope and objectives",
  "Recruit 500+ participants",
  "Statistical modeling",
  "Peer review submission"
];

details.forEach((detail, i) => {
  const x = 0.8 + (i * 2.3);
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 4.3, w: 2.1, h: 0.9,
    fill: { color: "2D4A6F" }
  });
  slide.addText(detail, {
    x: x + 0.15, y: 4.4, w: 1.8, h: 0.7,
    fontSize: 11, color: "E2E8F0", align: "center", valign: "middle", fontFace: "Calibri"
  });
});

pres.writeFile({ fileName: "04_timeline.pptx" });
```

---

### 05 — Charts & Data

Grouped bar chart by category with 3-phase color legend and labeled axes.

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

let slide = pres.addSlide();
slide.background = { color: "F8FAFC" };

// Title
slide.addText("Participant Distribution by Age Group", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 28, bold: true, color: "1E3A5F", fontFace: "Georgia", margin: 0
});

// Chart data
const chartData = [
  { name: "Phase 1", labels: ["18-25", "26-35", "36-45", "46-55", "55+"], values: [120, 245, 310, 180, 95] },
  { name: "Phase 2", labels: ["18-25", "26-35", "36-45", "46-55", "55+"], values: [145, 290, 340, 210, 120] },
  { name: "Phase 3", labels: ["18-25", "26-35", "36-45", "46-55", "55+"], values: [180, 320, 380, 245, 150] }
];

slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1.1, w: 7, h: 4, barDir: "col", barGrouping: "clustered",
  chartColors: ["0D9488", "F97316", "8B5CF6"],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
  catAxisLabelColor: "64748B",
  valAxisLabelColor: "64748B",
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },
  showValue: false,
  showLegend: true,
  legendPos: "r"
});

// Legend explanation
const legendItems = [
  { color: "0D9488", label: "Phase 1: Initial Recruitment" },
  { color: "F97316", label: "Phase 2: Mid-Study Addition" },
  { color: "8B5CF6", label: "Phase 3: Final Cohort" }
];

legendItems.forEach((item, i) => {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.8, y: 1.3 + (i * 0.6), w: 0.25, h: 0.25,
    fill: { color: item.color }
  });
  slide.addText(item.label, {
    x: 8.15, y: 1.25 + (i * 0.6), w: 1.8, h: 0.35,
    fontSize: 10, color: "475569", fontFace: "Calibri", margin: 0
  });
});

pres.writeFile({ fileName: "05_charts.pptx" });
```

---

### 06 — Icon Feature Grid

6-card grid with icon circles, bold headings, and short descriptive text.

```javascript
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaFlask, FaChartLine, FaUsers, FaCogs, FaShieldAlt, FaLightbulb } = require("react-icons/fa");

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

async function createSlide() {
  let pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';

  let slide = pres.addSlide();
  slide.background = { color: "F8FAFC" };

  // Title
  slide.addText("Methodology & Contributions", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: "1E3A5F", fontFace: "Georgia", margin: 0
  });

  const makeShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.06 });

  const features = [
    { icon: FaFlask, color: "0D9488", title: "Novel Approach", desc: "First-of-its-kind methodology combining ML with traditional analysis" },
    { icon: FaChartLine, color: "F97316", title: "Data-Driven", desc: "Analyzed 2.8M data points across 5 years of longitudinal data" },
    { icon: FaUsers, color: "8B5CF6", title: "Diverse Sample", desc: "Recruited from 12 countries representing varied demographics" },
    { icon: FaCogs, color: "1E3A5F", title: "Reproducible", desc: "Open-source tools and documented processes for replication" },
    { icon: FaShieldAlt, color: "0D9488", title: "Validated", desc: "Cross-validated with 3 independent datasets achieving 95% accuracy" },
    { icon: FaLightbulb, color: "F97316", title: "Impactful", desc: "Findings inform policy recommendations for 8 institutions" }
  ];

  for (let i = 0; i < features.length; i++) {
    const feature = features[i];
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + (col * 3.1);
    const y = 1.2 + (row * 2.1);

    // Card background
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 2.9, h: 1.9,
      fill: { color: "FFFFFF" },
      shadow: makeShadow()
    });

    // Icon circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.2, w: 0.6, h: 0.6,
      fill: { color: feature.color, transparency: 15 }
    });

    // Icon
    const iconData = await iconToBase64Png(feature.icon, "#" + feature.color, 256);
    slide.addImage({
      data: iconData,
      x: x + 0.32, y: y + 0.32, w: 0.36, h: 0.36
    });

    // Title
    slide.addText(feature.title, {
      x: x + 0.95, y: y + 0.3, w: 1.8, h: 0.4,
      fontSize: 14, bold: true, color: "1E3A5F", fontFace: "Calibri", margin: 0
    });

    // Description
    slide.addText(feature.desc, {
      x: x + 0.2, y: y + 0.95, w: 2.5, h: 0.8,
      fontSize: 11, color: "64748B", fontFace: "Calibri", margin: 0
    });
  }

  await pres.writeFile({ fileName: "06_icon_grid.pptx" });
}

createSlide();
```

---

## Key Elements Reference

### Shapes & Backgrounds

```javascript
slide.background = { color: "1E2761" };                          // Dark title slide

slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 0.08, h: 5.625,
  fill: { color: "CADCFC" }                                      // Accent left bar
});

// With shadow (use factory function to avoid mutation issues)
const makeShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 });
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: makeShadow()
});
```

### Charts (Modern Style)

```javascript
slide.addChart(pres.charts.BAR, data, {
  chartColors: ["028090", "00A896"],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
  catGridLine: { style: "none" },
  valGridLine: { color: "E2E8F0", size: 0.5 },
  showValue: true,
  dataLabelPosition: "outEnd"
});
```

### Icons via react-icons

```javascript
const { FaChartLine } = require("react-icons/fa");
const iconData = await iconToBase64Png(FaChartLine, "#028090", 256);
slide.addImage({ data: iconData, x: 0.5, y: 1, w: 0.5, h: 0.5 });
```

---

## Critical Rules (Avoid These Mistakes)

| ❌ NEVER | ✅ INSTEAD |
|----------|-----------|
| Use `#` in hex colors | `"FF0000"` not `"#FF0000"` — corrupts file |
| Use 8-char hex for opacity | Use `opacity: 0.15` separately |
| Use unicode `•` for bullets | Use `bullet: true` property |
| Reuse shadow/option objects | Use a factory function `() => ({...})` |
| Add accent lines under titles | Use whitespace — hallmark of AI slides |
| Create text-only slides | Every slide needs at least one visual element |
| Skip visual QA | Always convert to images and inspect |
| Use same layout repeatedly | Vary columns, cards, and callouts |

---

## QA Workflow (Required Before Delivery)

```bash
# 1. Check text content
python -m markitdown output.pptx

# 2. Check for leftover placeholders
python -m markitdown output.pptx | grep -iE "\bx{3,}\b|lorem|TODO|\[insert"

# 3. Convert to images for visual inspection
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg && pdftoppm -jpeg -r 150 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

### Visual QA Checklist

Look for:
- Overlapping elements (text through shapes, lines through words)
- Text overflow or cut off at edges/box boundaries
- Elements too close (< 0.3" gaps) or nearly touching
- Insufficient margin from slide edges (< 0.5")
- Low-contrast text or icons
- Leftover placeholder content
- Unaligned columns or similar elements

---

## Layout Best Practices

- **Dark title + conclusion slides, light content slides** ("sandwich" structure)
- **Vary layouts per slide:** two-column, icon-row, 2×2 grid, half-bleed image
- **Minimum 0.5" margins** from edges; 0.3–0.5" between content blocks
- **Left-align body text**; center only slide titles
- **Set `margin: 0`** on text boxes when aligning with shapes or icons

---

## Layout Dimensions

| Layout | Width | Height |
|--------|-------|--------|
| `LAYOUT_16x9` | 10" | 5.625" |
| `LAYOUT_16x10` | 10" | 6.25" |
| `LAYOUT_4x3` | 10" | 7.5" |
| `LAYOUT_WIDE` | 13.3" | 7.5" |

---

## Dependencies

- `npm install -g pptxgenjs react-icons react react-dom sharp` — creation from scratch
- `pip install "markitdown[pptx]"` — text extraction
- `pip install Pillow` — thumbnail grids
- LibreOffice (`soffice`) — PDF conversion (auto-configured via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) — PDF to images
