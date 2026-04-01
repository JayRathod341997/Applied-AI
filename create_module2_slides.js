const pptxgen = require("pptxgenjs");

// ──────────────────────────────────────────────
// THEME: Colorful Academic
// Navy (1E3A5F) + Teal (0D9488) + Orange (F97316) + Purple (8B5CF6)
// ──────────────────────────────────────────────
const C = {
  navy: "1E3A5F",
  teal: "0D9488",
  orange: "F97316",
  purple: "8B5CF6",
  lightBg: "F8FAFC",
  white: "FFFFFF",
  textDark: "1E293B",
  textMuted: "64748B",
  textLight: "94A3B8",
  borderLight: "E2E8F0",
  green: "059669",
  red: "DC2626",
  cyan: "06B6D4",
};

const FONT_TITLE = "Georgia";
const FONT_BODY = "Calibri";

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Module 2: LangChain Framework";

const makeShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 6,
  offset: 2,
  angle: 135,
  opacity: 0.08,
});

// ──────────────────────────────────────────────
// SLIDE 1 — Title + Agenda (split panel)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();

  // Left dark panel
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.5, h: 5.625,
    fill: { color: C.navy },
  });

  // Teal accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.5, y: 0, w: 0.08, h: 5.625,
    fill: { color: C.teal },
  });

  // Module label
  slide.addText("MODULE 2", {
    x: 0.5, y: 1.2, w: 3.5, h: 0.4,
    fontSize: 12, bold: true, color: C.teal, charSpacing: 4, fontFace: FONT_BODY, margin: 0,
  });

  // Title
  slide.addText("LangChain\nFramework", {
    x: 0.5, y: 1.7, w: 3.5, h: 1.4,
    fontSize: 32, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0,
  });

  // Subtitle
  slide.addText("Building Blocks & Architecture", {
    x: 0.5, y: 3.2, w: 3.5, h: 0.4,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY, margin: 0,
  });

  // Course metadata
  slide.addText([
    { text: "Applied AI Course", options: { breakLine: true, fontSize: 11, color: C.textLight } },
    { text: "Part 1: Foundations", options: { breakLine: true, fontSize: 11, color: C.textLight } },
    { text: "2026", options: { fontSize: 11, color: C.teal } },
  ], {
    x: 0.5, y: 4.0, w: 3.5, h: 1.0,
    fontFace: FONT_BODY, margin: 0,
  });

  // Right panel (light)
  slide.background = { color: C.lightBg };

  // AGENDA header
  slide.addText("AGENDA", {
    x: 5.0, y: 0.8, w: 4.5, h: 0.5,
    fontSize: 14, bold: true, color: C.teal, charSpacing: 4, fontFace: FONT_BODY, margin: 0,
  });

  const agendaItems = [
    { num: "01", text: "LangChain Overview & Architecture", color: C.teal },
    { num: "02", text: "Building Blocks: Chains, Prompts, Parsers", color: C.orange },
    { num: "03", text: "Chat Models & Chains", color: C.purple },
    { num: "04", text: "Memory, Tools & Agents", color: C.navy },
    { num: "05", text: "Patterns & Best Practices", color: C.teal },
    { num: "06", text: "Enterprise Scenario", color: C.orange },
  ];

  agendaItems.forEach((item, i) => {
    slide.addText(item.num, {
      x: 5.0, y: 1.5 + i * 0.62, w: 0.6, h: 0.4,
      fontSize: 20, bold: true, color: item.color, fontFace: FONT_TITLE, margin: 0,
    });
    slide.addText(item.text, {
      x: 5.7, y: 1.55 + i * 0.62, w: 3.8, h: 0.4,
      fontSize: 14, color: C.textDark, fontFace: FONT_BODY, margin: 0,
    });
  });

  slide.addNotes(
    "Welcome to Module 2 of the Applied AI course. This module covers the LangChain framework — an open-source " +
    "framework for building LLM-powered applications. We'll cover the architecture, building blocks (prompts, parsers, chains), " +
    "chat models, memory systems, tools & agents, best practices, and conclude with an enterprise scenario demonstrating " +
    "production-grade LangChain deployment."
  );
}

// ──────────────────────────────────────────────
// SLIDE 2 — What is LangChain? (KPI-style cards)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("What is LangChain?", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  slide.addText("An open-source framework for building applications powered by Large Language Models", {
    x: 0.5, y: 1.0, w: 9, h: 0.4,
    fontSize: 13, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
  });

  const stats = [
    { value: "9", label: "Core Components", desc: "Models, Prompts, Chains, Memory, Agents, Tools, Parsers, Indexes, Callbacks", accent: C.teal },
    { value: "4", label: "Architecture Layers", desc: "Provider, Integration, Orchestration, Application", accent: C.orange },
    { value: "LCEL", label: "Modern Syntax", desc: "Pipe operator (|) for declarative chain composition", accent: C.purple },
    { value: "100+", label: "Integrations", desc: "OpenAI, Anthropic, Google, HuggingFace, vector DBs, tools", accent: C.navy },
  ];

  stats.forEach((stat, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.6;
    const y = 1.6 + row * 1.9;

    // Card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.3, h: 1.7,
      fill: { color: C.white },
      shadow: makeShadow(),
    });

    // Left accent
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: 1.7,
      fill: { color: stat.accent },
    });

    slide.addText(stat.value, {
      x: x + 0.3, y: y + 0.15, w: 1.5, h: 0.6,
      fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
    });

    slide.addText(stat.label, {
      x: x + 1.8, y: y + 0.2, w: 2.3, h: 0.4,
      fontSize: 14, bold: true, color: C.textDark, fontFace: FONT_BODY, margin: 0,
    });

    slide.addText(stat.desc, {
      x: x + 0.3, y: y + 0.9, w: 3.8, h: 0.6,
      fontSize: 11, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
  });

  slide.addNotes(
    "LangChain provides a modular architecture with four layers: Provider Layer (OpenAI, Anthropic, Google), " +
    "Integration Layer (Models, Prompts, Memory, Tools, Vector Stores), Orchestration Layer (Chains, Agents, Graphs), " +
    "and Application Layer (Chatbots, RAG Systems, Agents). It has 9 core components and uses LCEL (LangChain Expression " +
    "Language) with the pipe operator for declarative composition. Over 100 integrations are available."
  );
}

// ──────────────────────────────────────────────
// SLIDE 3 — Architecture Diagram (dark bg, process flow)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.navy };

  slide.addText("LangChain Architecture", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0,
  });

  // Horizontal connector line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 2.5, w: 8.4, h: 0.06,
    fill: { color: C.teal },
  });

  const layers = [
    { num: "1", title: "Application", desc: "Chatbots, Agents, RAG Systems", color: C.teal },
    { num: "2", title: "Orchestration", desc: "Chains, Agents, Graphs, Workflows", color: C.orange },
    { num: "3", title: "Integration", desc: "Models, Prompts, Memory, Tools, Vector Stores", color: C.purple },
    { num: "4", title: "Provider", desc: "OpenAI, Anthropic, Google, HuggingFace", color: C.navy },
  ];

  // Recolor provider to a lighter shade so it's visible on dark bg
  layers[3].color = "3B82F6";

  layers.forEach((layer, i) => {
    const x = 0.8 + i * 2.3;

    // Circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.35, y: 2.1, w: 0.9, h: 0.9,
      fill: { color: layer.color },
    });

    slide.addText(layer.num, {
      x: x + 0.35, y: 2.15, w: 0.9, h: 0.85,
      fontSize: 22, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FONT_TITLE,
    });

    slide.addText(layer.title, {
      x: x - 0.2, y: 3.2, w: 2.0, h: 0.4,
      fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
    });

    slide.addText(layer.desc, {
      x: x - 0.2, y: 3.55, w: 2.0, h: 0.5,
      fontSize: 10, color: C.textLight, align: "center", fontFace: FONT_BODY,
    });
  });

  // Bottom detail cards
  const details = [
    "End-user interfaces",
    "Chain & agent logic",
    "Core abstractions",
    "Model API providers",
  ];

  details.forEach((detail, i) => {
    const x = 0.5 + i * 2.3;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 4.3, w: 2.1, h: 0.8,
      fill: { color: "2D4A6F" },
    });
    slide.addText(detail, {
      x: x + 0.1, y: 4.4, w: 1.9, h: 0.6,
      fontSize: 10, color: C.borderLight, align: "center", valign: "middle", fontFace: FONT_BODY,
    });
  });

  slide.addNotes(
    "LangChain's architecture has four layers. Bottom-up: Provider Layer wraps model APIs (OpenAI, Anthropic, Google, HuggingFace). " +
    "Integration Layer provides core abstractions (Models, Prompts, Memory, Tools, Vector Stores, Output Parsers). " +
    "Orchestration Layer handles workflow logic through Chains, Agents, and Graphs. Application Layer is the end-user " +
    "interface — chatbots, RAG systems, autonomous agents. This layered design enables swapping any component without affecting others."
  );
}

// ──────────────────────────────────────────────
// SLIDE 4 — LCEL: The Pipe Operator (two-column)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("LangChain Expression Language (LCEL)", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 26, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  // Left column — Concept
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "F0FDFA" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.teal },
  });
  slide.addText("CONCEPT", {
    x: 0.5, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "Declarative Composition", options: { bold: true, breakLine: true, fontSize: 13, color: C.textDark } },
    { text: "Use the pipe (|) operator to chain components together in a readable, composable way.", options: { breakLine: true, breakLine: true, fontSize: 12, color: C.textMuted } },
    { text: "Built-in Features", options: { bold: true, breakLine: true, fontSize: 13, color: C.textDark } },
    { text: "Streaming, async/await, parallel execution, fallbacks, retries — all out of the box.", options: { breakLine: true, breakLine: true, fontSize: 12, color: C.textMuted } },
    { text: "Why LCEL?", options: { bold: true, breakLine: true, fontSize: 13, color: C.textDark } },
    { text: "Replaces legacy LLMChain. Better performance, simpler syntax, production-ready.", options: { fontSize: 12, color: C.textMuted } },
  ], {
    x: 0.7, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  // Right column — Code
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "FFF7ED" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.orange },
  });
  slide.addText("CODE", {
    x: 5.2, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "from langchain_core.prompts import ChatPromptTemplate", options: { fontSize: 10, color: C.textDark } },
    { text: "from langchain_openai import ChatOpenAI", options: { fontSize: 10, color: C.textDark } },
    { text: "from langchain_core.output_parsers import StrOutputParser", options: { fontSize: 10, color: C.textDark } },
    { text: "", options: { fontSize: 8 } },
    { text: "prompt = ChatPromptTemplate.from_template(", options: { fontSize: 10, color: C.teal } },
    { text: '    "Tell me a joke about {topic}"', options: { fontSize: 10, color: C.textMuted } },
    { text: ")", options: { fontSize: 10, color: C.teal } },
    { text: "model = ChatOpenAI(model='gpt-4o-mini')", options: { fontSize: 10, color: C.textDark } },
    { text: "parser = StrOutputParser()", options: { fontSize: 10, color: C.textDark } },
    { text: "", options: { fontSize: 8 } },
    { text: "chain = prompt | model | parser", options: { fontSize: 11, bold: true, color: C.orange } },
    { text: 'result = chain.invoke({"topic": "programming"})', options: { fontSize: 10, color: C.textDark } },
  ], {
    x: 5.4, y: 1.9, w: 3.9, h: 3.0,
    fontFace: "Consolas", valign: "top", margin: 0,
  });

  slide.addNotes(
    "LCEL (LangChain Expression Language) is the modern way to compose chains. It uses the pipe operator (|) to connect " +
    "components declaratively. Key benefits: built-in streaming for real-time output, async support with ainvoke()/astream(), " +
    "parallel execution with RunnableParallel, fallbacks with .with_fallbacks(), and retries. This replaces the legacy " +
    "LLMChain class. The syntax chain = prompt | model | parser reads left-to-right like a data pipeline."
  );
}

// ──────────────────────────────────────────────
// SLIDE 5 — Prompt Templates (icon feature grid 2x2)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Prompt Templates", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  const features = [
    { icon: "1", color: C.teal, title: "PromptTemplate", desc: "Simple string template with {variable} placeholders. Used for text completion models." },
    { icon: "2", color: C.orange, title: "ChatPromptTemplate", desc: "Message-based template with system, human, and AI roles. Used for chat models." },
    { icon: "3", color: C.purple, title: "FewShot Prompting", desc: "Provide examples in the prompt to demonstrate expected input-output patterns." },
    { icon: "4", color: C.navy, title: "Dynamic Placeholders", desc: "Use .partial() to fill some variables early, others at invocation time." },
  ];

  features.forEach((f, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.6;
    const y = 1.2 + row * 2.1;

    // Card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.3, h: 1.9,
      fill: { color: C.white },
      shadow: makeShadow(),
    });

    // Icon circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.2, w: 0.55, h: 0.55,
      fill: { color: f.color, transparency: 15 },
    });
    slide.addText(f.icon, {
      x: x + 0.2, y: y + 0.22, w: 0.55, h: 0.55,
      fontSize: 18, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FONT_TITLE,
    });

    // Title
    slide.addText(f.title, {
      x: x + 0.9, y: y + 0.25, w: 3.2, h: 0.4,
      fontSize: 15, bold: true, color: C.navy, fontFace: FONT_BODY, margin: 0,
    });

    // Description
    slide.addText(f.desc, {
      x: x + 0.2, y: y + 0.9, w: 3.9, h: 0.8,
      fontSize: 11, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
  });

  slide.addNotes(
    "Prompt Templates are the input layer of every LangChain chain. PromptTemplate is for simple text completion with " +
    "{variable} placeholders. ChatPromptTemplate uses message roles (system, human, AI) — this is the standard for modern " +
    "chat models like GPT-4 and Claude. Few-shot prompting embeds examples directly in the template. Dynamic placeholders " +
    "with .partial() let you pre-fill some variables and defer others to runtime."
  );
}

// ──────────────────────────────────────────────
// SLIDE 6 — Output Parsers (2-column detail)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Output Parsers", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  slide.addText("Transform raw LLM responses into structured, parseable formats", {
    x: 0.5, y: 0.95, w: 9, h: 0.35,
    fontSize: 13, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
  });

  const parsers = [
    { name: "StrOutputParser", desc: "Strips whitespace from raw text response. Simplest parser for string output.", color: C.teal },
    { name: "JsonOutputParser", desc: "Parses JSON from model output. Supports Pydantic schema validation.", color: C.orange },
    { name: "PydanticOutputParser", desc: "Returns typed Pydantic model instances with validation and autocomplete.", color: C.purple },
    { name: "ListOutputParser", desc: "Parses comma-separated values into a Python list.", color: "3B82F6" },
  ];

  parsers.forEach((p, i) => {
    const y = 1.5 + i * 0.95;

    // Accent bar
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y + 0.08, w: 0.08, h: 0.6,
      fill: { color: p.color },
    });

    slide.addText(p.name, {
      x: 0.8, y: y, w: 3.5, h: 0.4,
      fontSize: 14, bold: true, color: C.navy, fontFace: "Consolas", margin: 0,
    });

    slide.addText(p.desc, {
      x: 0.8, y: y + 0.38, w: 8.5, h: 0.4,
      fontSize: 12, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
  });

  // Example box
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.5, w: 4.3, h: 3.5,
    fill: { color: C.white },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.5, w: 4.3, h: 0.45,
    fill: { color: C.orange },
  });
  slide.addText("PYDANTIC EXAMPLE", {
    x: 5.2, y: 1.55, w: 4.3, h: 0.4,
    fontSize: 12, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "class PersonInfo(BaseModel):", options: { fontSize: 10, bold: true, color: C.teal } },
    { text: "    name: str  # Person's full name", options: { fontSize: 10, color: C.textMuted } },
    { text: "    age: int   # Person's age", options: { fontSize: 10, color: C.textMuted } },
    { text: "    occupation: str", options: { fontSize: 10, color: C.textMuted } },
    { text: "", options: { fontSize: 6 } },
    { text: "parser = JsonOutputParser(", options: { fontSize: 10, color: C.textDark } },
    { text: "    pydantic_object=PersonInfo", options: { fontSize: 10, color: C.textDark } },
    { text: ")", options: { fontSize: 10, color: C.textDark } },
    { text: "", options: { fontSize: 6 } },
    { text: "chain = prompt | model | parser", options: { fontSize: 10, bold: true, color: C.orange } },
    { text: "", options: { fontSize: 6 } },
    { text: "# Output:", options: { fontSize: 10, color: C.textMuted } },
    { text: '# {"name":"John","age":32,', options: { fontSize: 10, color: C.green } },
    { text: '#  "occupation":"engineer"}', options: { fontSize: 10, color: C.green } },
  ], {
    x: 5.4, y: 2.1, w: 3.9, h: 2.7,
    fontFace: "Consolas", valign: "top", margin: 0,
  });

  slide.addNotes(
    "Output parsers transform raw LLM text into structured formats. StrOutputParser is the simplest — just strips whitespace. " +
    "JsonOutputParser extracts JSON and optionally validates against a Pydantic schema. PydanticOutputParser returns typed " +
    "Pydantic model instances with full validation and IDE autocomplete. ListOutputParser handles comma-separated values. " +
    "For production, always use PydanticOutputParser or with_structured_output() for reliable, type-safe extraction."
  );
}

// ──────────────────────────────────────────────
// SLIDE 7 — Chains: From Legacy to LCEL
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Chains: Legacy vs. Modern LCEL", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 26, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  // Legacy column
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "FEF2F2" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.red },
  });
  slide.addText("LEGACY (Avoid)", {
    x: 0.5, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "LLMChain", options: { fontSize: 13, bold: true, color: C.red } },
    { text: "from langchain.chains import LLMChain", options: { fontSize: 10, color: C.textMuted } },
    { text: "chain = LLMChain(llm=model, prompt=prompt)", options: { fontSize: 10, color: C.textMuted } },
    { text: "", options: { fontSize: 6 } },
    { text: "SequentialChain", options: { fontSize: 13, bold: true, color: C.red } },
    { text: "Requires explicit input/output key mapping.", options: { fontSize: 10, color: C.textMuted } },
    { text: "Harder to debug, less composable.", options: { fontSize: 10, color: C.textMuted } },
    { text: "", options: { fontSize: 6 } },
    { text: "ConversationChain", options: { fontSize: 13, bold: true, color: C.red } },
    { text: "Deprecated — use LCEL with memory instead.", options: { fontSize: 10, color: C.textMuted } },
  ], {
    x: 0.7, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  // Modern column
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "F0FDFA" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.teal },
  });
  slide.addText("MODERN LCEL (Recommended)", {
    x: 5.2, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "Simple Chain", options: { fontSize: 13, bold: true, color: C.teal } },
    { text: "chain = prompt | model | parser", options: { fontSize: 10, color: C.textMuted } },
    { text: "", options: { fontSize: 6 } },
    { text: "Sequential", options: { fontSize: 13, bold: true, color: C.teal } },
    { text: 'full_chain = {"outline": outline} | essay', options: { fontSize: 10, color: C.textMuted } },
    { text: "", options: { fontSize: 6 } },
    { text: "Parallel", options: { fontSize: 13, bold: true, color: C.teal } },
    { text: "RunnableParallel({summary, keywords})", options: { fontSize: 10, color: C.textMuted } },
    { text: "", options: { fontSize: 6 } },
    { text: "Built-in: streaming, async, fallbacks", options: { fontSize: 10, bold: true, color: C.green } },
  ], {
    x: 5.4, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  slide.addNotes(
    "LangChain chains have evolved. Legacy classes (LLMChain, SequentialChain, ConversationChain) are deprecated. " +
    "Modern LCEL provides: simple chains with the pipe operator, sequential chains using dict-based routing, " +
    "parallel execution with RunnableParallel. LCEL chains have built-in streaming, async support, fallbacks, and retries. " +
    "Always use LCEL for new projects — it's cleaner, more composable, and production-ready."
  );
}

// ──────────────────────────────────────────────
// SLIDE 8 — Chat Models & Streaming (stats layout)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Chat Models & Streaming", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  const capabilities = [
    { value: "3", label: "Message Types", desc: "SystemMessage, HumanMessage, AIMessage — structured conversation roles", accent: C.teal },
    { value: "∞", label: "Streaming", desc: "Real-time token output with .stream() for responsive UX", accent: C.orange },
    { value: "async", label: "Async Support", desc: "ainvoke(), astream() — concurrent calls with asyncio.gather()", accent: C.purple },
    { value: "7+", label: "Parameters", desc: "temperature, max_tokens, top_p, seed, timeout, retries, and more", accent: "3B82F6" },
  ];

  capabilities.forEach((cap, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.6;
    const y = 1.3 + row * 2.0;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.3, h: 1.8,
      fill: { color: C.white },
      shadow: makeShadow(),
    });

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: 1.8,
      fill: { color: cap.accent },
    });

    slide.addText(cap.value, {
      x: x + 0.3, y: y + 0.15, w: 1.5, h: 0.6,
      fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
    });

    slide.addText(cap.label, {
      x: x + 1.8, y: y + 0.2, w: 2.3, h: 0.4,
      fontSize: 14, bold: true, color: C.textDark, fontFace: FONT_BODY, margin: 0,
    });

    slide.addText(cap.desc, {
      x: x + 0.3, y: y + 0.9, w: 3.8, h: 0.7,
      fontSize: 11, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
  });

  slide.addNotes(
    "Chat models in LangChain use structured messages (System, Human, AI) instead of raw text. Streaming with .stream() " +
    "enables real-time token-by-token output for responsive UIs. Async support with ainvoke()/astream() allows concurrent " +
    "model calls using asyncio.gather(). Key parameters: temperature (0-1 creativity), max_tokens (output limit), " +
    "top_p (nucleus sampling), seed (reproducibility), timeout, max_retries. Multi-model chains can route different tasks " +
    "to different providers (OpenAI for factual, Anthropic for creative, Google for code)."
  );
}

// ──────────────────────────────────────────────
// SLIDE 9 — Section Divider: Memory, Tools & Agents
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.purple };

  slide.addText("Section 2.4", {
    x: 0, y: 2.2, w: 10, h: 0.5,
    fontSize: 18, color: "D8B4FE", align: "center", fontFace: FONT_BODY, margin: 0,
  });
  slide.addText("Memory, Tools & Agents", {
    x: 0, y: 2.7, w: 10, h: 1.0,
    fontSize: 42, bold: true, color: C.white, align: "center", fontFace: FONT_TITLE, margin: 0,
  });
  slide.addText("Adding state, actions, and autonomy to LLM applications", {
    x: 0, y: 3.8, w: 10, h: 0.5,
    fontSize: 16, color: "D8B4FE", align: "center", fontFace: FONT_BODY, margin: 0,
  });

  slide.addNotes(
    "This section covers three critical capabilities that elevate LLM apps from simple text-in/text-out to intelligent systems. " +
    "Memory provides conversation continuity. Tools give the LLM access to external functions. Agents combine reasoning " +
    "with tool use to autonomously solve complex tasks."
  );
}

// ──────────────────────────────────────────────
// SLIDE 10 — Memory Types (icon grid)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Memory Types", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  const memTypes = [
    { icon: "B", color: C.teal, title: "Buffer Memory", desc: "Stores complete conversation history. Simple but token-heavy for long chats." },
    { icon: "W", color: C.orange, title: "Window Memory", desc: "Keeps only the last N exchanges. Balances context with token efficiency." },
    { icon: "S", color: C.purple, title: "Summary Memory", desc: "Maintains a running summary via LLM. Compresses long conversations." },
    { icon: "V", color: "3B82F6", title: "Vector Memory", desc: "Semantic search over past conversations. Retrieves relevant context on demand." },
  ];

  memTypes.forEach((m, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.6;
    const y = 1.2 + row * 2.1;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.3, h: 1.9,
      fill: { color: C.white },
      shadow: makeShadow(),
    });

    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.2, w: 0.55, h: 0.55,
      fill: { color: m.color, transparency: 15 },
    });
    slide.addText(m.icon, {
      x: x + 0.2, y: y + 0.22, w: 0.55, h: 0.55,
      fontSize: 18, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FONT_TITLE,
    });

    slide.addText(m.title, {
      x: x + 0.9, y: y + 0.25, w: 3.2, h: 0.4,
      fontSize: 15, bold: true, color: C.navy, fontFace: FONT_BODY, margin: 0,
    });

    slide.addText(m.desc, {
      x: x + 0.2, y: y + 0.9, w: 3.9, h: 0.8,
      fontSize: 11, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
  });

  slide.addNotes(
    "Memory types trade off between completeness and efficiency. ConversationBufferMemory stores everything — simple but " +
    "expensive for long conversations. ConversationBufferWindowMemory keeps a sliding window of the last N turns. " +
    "ConversationSummaryMemory uses an LLM to maintain a running summary, compressing history. " +
    "ConversationSummaryBufferMemory combines both — summarizes old messages, keeps recent ones in full. " +
    "VectorStoreRetrieverMemory uses semantic search to retrieve only relevant past exchanges. " +
    "Choose based on your use case: window for short chats, summary for long conversations, vector for knowledge-heavy apps."
  );
}

// ──────────────────────────────────────────────
// SLIDE 11 — Tools & Agents (two-column)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Tools & Agents", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  // Left: Tools
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "F0FDFA" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.teal },
  });
  slide.addText("TOOLS", {
    x: 0.5, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "Functions an agent can invoke", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "", options: { fontSize: 4 } },
    { text: "@tool decorator defines tools", options: { fontSize: 11, color: C.textMuted } },
    { text: "Docstring becomes tool description", options: { fontSize: 11, color: C.textMuted } },
    { text: "Type hints define parameters", options: { fontSize: 11, color: C.textMuted } },
    { text: "", options: { fontSize: 4 } },
    { text: "Examples:", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "calculator(), search_weather()", options: { fontSize: 11, color: C.teal } },
    { text: "get_current_time(), db_query()", options: { fontSize: 11, color: C.teal } },
    { text: "web_search(), file_reader()", options: { fontSize: 11, color: C.teal } },
  ], {
    x: 0.7, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  // Right: Agents
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "FFF7ED" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.orange },
  });
  slide.addText("AGENTS", {
    x: 5.2, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "LLMs that decide which tools to use", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "", options: { fontSize: 4 } },
    { text: "Thought → Action → Observation loop", options: { fontSize: 11, color: C.textMuted } },
    { text: "create_tool_calling_agent()", options: { fontSize: 11, color: C.textMuted } },
    { text: "AgentExecutor runs the loop", options: { fontSize: 11, color: C.textMuted } },
    { text: "", options: { fontSize: 4 } },
    { text: "Agent Types:", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "Tool Calling — native function calls", options: { fontSize: 11, color: C.orange } },
    { text: "ReAct — reasoning + acting loop", options: { fontSize: 11, color: C.orange } },
    { text: "Plan-and-Execute — strategy first", options: { fontSize: 11, color: C.orange } },
  ], {
    x: 5.4, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  slide.addNotes(
    "Tools are functions decorated with @tool that agents can invoke. The docstring becomes the tool description the LLM sees, " +
    "and type hints define the parameters. Agents use an LLM to decide which tools to call and in what order — the classic " +
    "Thought → Action → Observation loop. AgentExecutor runs this loop with error handling. Agent types: Tool Calling Agent " +
    "uses native function calling (modern LLMs), ReAct Agent for complex reasoning, Plan-and-Execute for strategic tasks, " +
    "Self-Ask for multi-hop reasoning. Agents with memory maintain conversation state across interactions."
  );
}

// ──────────────────────────────────────────────
// SLIDE 12 — Agent Types Comparison (table-style)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Agent Types Comparison", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  // Table headers
  const headers = ["Agent Type", "Mechanism", "Best For"];
  const colX = [0.5, 3.2, 6.8];
  const colW = [2.5, 3.4, 2.8];

  headers.forEach((h, i) => {
    slide.addText(h, {
      x: colX[i], y: 1.2, w: colW[i], h: 0.4,
      fontSize: 13, bold: true, color: C.teal, fontFace: FONT_BODY, margin: 0,
    });
  });

  // Divider line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.6, w: 9.0, h: 0.02,
    fill: { color: C.borderLight },
  });

  const agents = [
    { type: "Tool Calling", mechanism: "Native function calling API", best: "Modern LLMs with tool support", color: C.teal },
    { type: "ReAct", mechanism: "Thought → Action → Observation loop", best: "Complex multi-step reasoning", color: C.orange },
    { type: "Plan-and-Execute", mechanism: "Plans strategy first, then executes", best: "Tasks requiring forethought", color: C.purple },
    { type: "Self-Ask", mechanism: "Decomposes into sub-questions", best: "Multi-hop reasoning chains", color: "3B82F6" },
  ];

  agents.forEach((a, i) => {
    const y = 1.8 + i * 0.85;

    // Accent bar
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: y + 0.1, w: 0.08, h: 0.5,
      fill: { color: a.color },
    });

    slide.addText(a.type, {
      x: colX[0], y, w: colW[0], h: 0.4,
      fontSize: 13, bold: true, color: C.navy, fontFace: FONT_BODY, margin: 0,
    });
    slide.addText(a.mechanism, {
      x: colX[1], y, w: colW[1], h: 0.4,
      fontSize: 12, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
    slide.addText(a.best, {
      x: colX[2], y, w: colW[2], h: 0.4,
      fontSize: 12, color: C.textDark, fontFace: FONT_BODY, margin: 0,
    });
  });

  // Bottom insight box
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.0, w: 9.0, h: 1.2,
    fill: { color: C.white },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.0, w: 0.08, h: 1.2,
    fill: { color: C.teal },
  });
  slide.addText("Production Tip", {
    x: 0.8, y: 4.1, w: 8.5, h: 0.35,
    fontSize: 13, bold: true, color: C.navy, fontFace: FONT_BODY, margin: 0,
  });
  slide.addText("Start with Tool Calling Agent for most use cases — it leverages native function calling and is the most " +
    "reliable. Add memory with ConversationBufferMemory. Use AgentExecutor with handle_parsing_errors=True and verbose=True for debugging.", {
    x: 0.8, y: 4.45, w: 8.5, h: 0.6,
    fontSize: 11, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
  });

  slide.addNotes(
    "Four main agent types in LangChain. Tool Calling Agent uses native function calling APIs (recommended for GPT-4, Claude). " +
    "ReAct Agent implements the Thought-Action-Observation loop for complex reasoning. Plan-and-Execute creates a strategy " +
    "before acting. Self-Ask decomposes questions into sub-questions. For production: start with Tool Calling Agent, " +
    "add memory for conversation state, enable error handling with handle_parsing_errors=True, and use verbose=True during development."
  );
}

// ──────────────────────────────────────────────
// SLIDE 13 — Section Divider: Best Practices
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.navy };

  slide.addText("Section 2.5", {
    x: 0, y: 2.2, w: 10, h: 0.5,
    fontSize: 18, color: C.teal, align: "center", fontFace: FONT_BODY, margin: 0,
  });
  slide.addText("Patterns & Best Practices", {
    x: 0, y: 2.7, w: 10, h: 1.0,
    fontSize: 42, bold: true, color: C.white, align: "center", fontFace: FONT_TITLE, margin: 0,
  });
  slide.addText("Production-ready patterns for reliable, scalable LangChain applications", {
    x: 0, y: 3.8, w: 10, h: 0.5,
    fontSize: 16, color: C.textLight, align: "center", fontFace: FONT_BODY, margin: 0,
  });

  slide.addNotes(
    "This section covers 10 best practices for production LangChain applications: LCEL over legacy chains, error handling, " +
    "fallbacks, retries, token optimization, structured output, callbacks, parallel execution, caching, and security."
  );
}

// ──────────────────────────────────────────────
// SLIDE 14 — Best Practices Grid (3x3 minus 1)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Top Best Practices", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  const practices = [
    { num: "1", title: "Use LCEL", desc: "Pipe operator over legacy LLMChain. Streaming, async, composable.", color: C.teal },
    { num: "2", title: "Error Handling", desc: "Wrap parsers in try/except. Return graceful fallbacks.", color: C.orange },
    { num: "3", title: "Fallbacks", desc: ".with_fallbacks() for model redundancy and reliability.", color: C.purple },
    { num: "4", title: "Retries", desc: "tenacity library with exponential backoff for transient errors.", color: "3B82F6" },
    { num: "5", title: "Token Optimization", desc: "Chunk documents, summarize history, limit context windows.", color: C.teal },
    { num: "6", title: "Structured Output", desc: "with_structured_output() for type-safe Pydantic extraction.", color: C.orange },
    { num: "7", title: "Callbacks", desc: "Custom handlers for logging, token counting, monitoring.", color: C.purple },
    { num: "8", title: "Parallel Execution", desc: "RunnableParallel for concurrent chain branches.", color: "3B82F6" },
  ];

  practices.forEach((p, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.3 + col * 2.35;
    const y = 1.2 + row * 2.1;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.15, h: 1.9,
      fill: { color: C.white },
      shadow: makeShadow(),
    });

    // Number badge
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.15, y: y + 0.15, w: 0.4, h: 0.4,
      fill: { color: p.color },
    });
    slide.addText(p.num, {
      x: x + 0.15, y: y + 0.17, w: 0.4, h: 0.4,
      fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FONT_TITLE,
    });

    slide.addText(p.title, {
      x: x + 0.65, y: y + 0.2, w: 1.35, h: 0.35,
      fontSize: 13, bold: true, color: C.navy, fontFace: FONT_BODY, margin: 0,
    });

    slide.addText(p.desc, {
      x: x + 0.15, y: y + 0.75, w: 1.85, h: 1.0,
      fontSize: 10, color: C.textMuted, fontFace: FONT_BODY, margin: 0,
    });
  });

  slide.addNotes(
    "Eight essential best practices. 1. Always use LCEL (pipe operator) instead of legacy LLMChain. 2. Wrap parsers in " +
    "try/except for error handling. 3. Use .with_fallbacks() for model redundancy. 4. Implement retries with exponential " +
    "backoff using tenacity. 5. Optimize tokens with chunking and summarization. 6. Use with_structured_output() for " +
    "type-safe extraction. 7. Add callbacks for monitoring and logging. 8. Use RunnableParallel for concurrent execution."
  );
}

// ──────────────────────────────────────────────
// SLIDE 15 — Security & Caching (two-column)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Security & Performance", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  // Left: Security
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "FEF2F2" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.red },
  });
  slide.addText("SECURITY", {
    x: 0.5, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "Never hardcode API keys", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "Use environment variables or .env files", options: { fontSize: 11, color: C.textMuted } },
    { text: "", options: { fontSize: 4 } },
    { text: "Sanitize user inputs", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "Strip prompt injection patterns", options: { fontSize: 11, color: C.textMuted } },
    { text: "Limit input length", options: { fontSize: 11, color: C.textMuted } },
    { text: "", options: { fontSize: 4 } },
    { text: "Validate LLM outputs", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "Pydantic schemas enforce types", options: { fontSize: 11, color: C.textMuted } },
    { text: "Never execute unvalidated code", options: { fontSize: 11, color: C.textMuted } },
  ], {
    x: 0.7, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  // Right: Performance
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 4.0,
    fill: { color: "F0FDFA" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 0.5,
    fill: { color: C.teal },
  });
  slide.addText("PERFORMANCE", {
    x: 5.2, y: 1.25, w: 4.3, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });

  slide.addText([
    { text: "Caching", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "InMemoryCache for speed, SQLiteCache for persistence", options: { fontSize: 11, color: C.textMuted } },
    { text: "", options: { fontSize: 4 } },
    { text: "Parallel Execution", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "RunnableParallel runs branches concurrently", options: { fontSize: 11, color: C.textMuted } },
    { text: "", options: { fontSize: 4 } },
    { text: "Token Optimization", options: { fontSize: 12, bold: true, color: C.textDark } },
    { text: "RecursiveCharacterTextSplitter for chunking", options: { fontSize: 11, color: C.textMuted } },
    { text: "Summarize instead of passing full history", options: { fontSize: 11, color: C.textMuted } },
  ], {
    x: 5.4, y: 1.9, w: 3.9, h: 3.0,
    fontFace: FONT_BODY, valign: "top", margin: 0,
  });

  slide.addNotes(
    "Security: Never hardcode API keys — use os.getenv() or python-dotenv. Sanitize user inputs to prevent prompt injection. " +
    "Validate all LLM outputs with Pydantic schemas before using them. Never execute unvalidated code from LLM outputs. " +
    "Performance: Use caching (InMemoryCache for speed, SQLiteCache for persistence) — identical prompts return cached results. " +
    "Run parallel chains with RunnableParallel for concurrent execution. Optimize tokens by chunking documents with " +
    "RecursiveCharacterTextSplitter and summarizing conversation history instead of passing full logs."
  );
}

// ──────────────────────────────────────────────
// SLIDE 16 — Mini-Projects Overview (timeline)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.navy };

  slide.addText("Mini-Projects in This Module", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0,
  });

  // Connector line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 2.5, w: 8.4, h: 0.06,
    fill: { color: C.teal },
  });

  const projects = [
    { num: "1", title: "Chatbot", desc: "Memory + personality", color: C.teal },
    { num: "2", title: "Summarizer", desc: "Map-Reduce pattern", color: C.orange },
    { num: "3", title: "Doc Q&A", desc: "RAG with FAISS", color: C.purple },
    { num: "4", title: "Waiter Bot", desc: "Tool-calling agent", color: "3B82F6" },
    { num: "5", title: "Travel Planner", desc: "Multi-tool agent", color: C.teal },
  ];

  projects.forEach((proj, i) => {
    const x = 0.5 + i * 1.9;

    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: 2.1, w: 0.9, h: 0.9,
      fill: { color: proj.color },
    });

    slide.addText(proj.num, {
      x: x + 0.2, y: 2.15, w: 0.9, h: 0.85,
      fontSize: 22, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FONT_TITLE,
    });

    slide.addText(proj.title, {
      x: x - 0.2, y: 3.2, w: 1.8, h: 0.4,
      fontSize: 13, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
    });

    slide.addText(proj.desc, {
      x: x - 0.2, y: 3.55, w: 1.8, h: 0.4,
      fontSize: 10, color: C.textLight, align: "center", fontFace: FONT_BODY,
    });

    // Detail card
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x - 0.1, y: 4.2, w: 1.6, h: 0.9,
      fill: { color: "2D4A6F" },
    });

    const details = [
      "BufferMemory, ChatPrompt",
      "Chunking, Map-Reduce",
      "FAISS, retriever chain",
      "@tool, AgentExecutor",
      "4 tools, cost estimator",
    ];

    slide.addText(details[i], {
      x: x, y: 4.3, w: 1.4, h: 0.7,
      fontSize: 9, color: C.borderLight, align: "center", valign: "middle", fontFace: FONT_BODY,
    });
  });

  slide.addNotes(
    "Five hands-on mini-projects progressively build skills. Project 1: Conversational chatbot with BufferMemory and " +
    "personality system prompt. Project 2: Text summarizer using map-reduce pattern for long documents. Project 3: " +
    "Document Q&A system with FAISS vector store and retriever chain (proto-RAG). Project 4: Restaurant waiter bot " +
    "with @tool decorator and AgentExecutor. Project 5: Travel planner with 4 custom tools (destination info, cost " +
    "estimation, itinerary generation, travel tips). Each project reinforces specific LangChain concepts."
  );
}

// ──────────────────────────────────────────────
// SLIDE 17 — Enterprise Scenario Title
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.orange };

  slide.addText("ENTERPRISE SCENARIO", {
    x: 0, y: 2.0, w: 10, h: 0.5,
    fontSize: 14, color: "FED7AA", charSpacing: 4, align: "center", fontFace: FONT_BODY, margin: 0,
  });
  slide.addText("AI-Powered Financial\nDocument Analyzer", {
    x: 0, y: 2.5, w: 10, h: 1.4,
    fontSize: 40, bold: true, color: C.white, align: "center", fontFace: FONT_TITLE, margin: 0,
  });
  slide.addText("Meridian Capital — Automating quarterly earnings analysis with LangChain agents", {
    x: 0, y: 4.1, w: 10, h: 0.5,
    fontSize: 15, color: "FED7AA", align: "center", fontFace: FONT_BODY, margin: 0,
  });

  slide.addNotes(
    "Let's apply everything we've learned to a real enterprise scenario. Meridian Capital, a mid-size investment firm, " +
    "needs to automate their quarterly earnings analysis workflow. Analysts spend 15+ hours per week reading 10-K/10-Q " +
    "filings, extracting financial metrics, comparing across quarters, and writing summary reports. We'll build a LangChain-based " +
    "system that handles document ingestion, structured extraction, cross-period comparison, and report generation."
  );
}

// ──────────────────────────────────────────────
// SLIDE 18 — Enterprise Scenario Details (KPI + architecture)
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Meridian Capital — Solution Architecture", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 26, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  // Problem card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 2.8, h: 2.0,
    fill: { color: "FEF2F2" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 2.8, h: 0.45,
    fill: { color: C.red },
  });
  slide.addText("PROBLEM", {
    x: 0.5, y: 1.25, w: 2.8, h: 0.4,
    fontSize: 12, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });
  slide.addText([
    { text: "15+ hrs/week per analyst", options: { fontSize: 10, color: C.textMuted, breakLine: true } },
    { text: "50+ filings per quarter", options: { fontSize: 10, color: C.textMuted, breakLine: true } },
    { text: "Manual extraction errors", options: { fontSize: 10, color: C.textMuted, breakLine: true } },
    { text: "Inconsistent formats", options: { fontSize: 10, color: C.textMuted } },
  ], { x: 0.7, y: 1.8, w: 2.4, h: 1.2, fontFace: FONT_BODY, valign: "top", margin: 0 });

  // Solution card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.6, y: 1.2, w: 2.8, h: 2.0,
    fill: { color: "F0FDFA" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.6, y: 1.2, w: 2.8, h: 0.45,
    fill: { color: C.teal },
  });
  slide.addText("LANGCHAIN STACK", {
    x: 3.6, y: 1.25, w: 2.8, h: 0.4,
    fontSize: 12, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });
  slide.addText([
    { text: "DocumentLoaders (PDF/HTML)", options: { fontSize: 10, color: C.textMuted, breakLine: true } },
    { text: "TextSplitter for chunking", options: { fontSize: 10, color: C.textMuted, breakLine: true } },
    { text: "Pydantic structured output", options: { fontSize: 10, color: C.textMuted, breakLine: true } },
    { text: "Sequential chains for reports", options: { fontSize: 10, color: C.textMuted } },
  ], { x: 3.8, y: 1.8, w: 2.4, h: 1.2, fontFace: FONT_BODY, valign: "top", margin: 0 });

  // Results card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.7, y: 1.2, w: 2.8, h: 2.0,
    fill: { color: "F0FDFA" },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.7, y: 1.2, w: 2.8, h: 0.45,
    fill: { color: C.green },
  });
  slide.addText("RESULTS", {
    x: 6.7, y: 1.25, w: 2.8, h: 0.4,
    fontSize: 12, bold: true, color: C.white, align: "center", fontFace: FONT_BODY,
  });
  slide.addText([
    { text: "85% time reduction", options: { fontSize: 10, color: C.green, bold: true, breakLine: true } },
    { text: "99.2% extraction accuracy", options: { fontSize: 10, color: C.green, bold: true, breakLine: true } },
    { text: "$420K annual savings", options: { fontSize: 10, color: C.green, bold: true, breakLine: true } },
    { text: "Same-day report turnaround", options: { fontSize: 10, color: C.green, bold: true } },
  ], { x: 6.9, y: 1.8, w: 2.4, h: 1.2, fontFace: FONT_BODY, valign: "top", margin: 0 });

  // Bottom KPI row
  const kpis = [
    { value: "2.3s", label: "Per Filing Analysis", accent: C.teal },
    { value: "50+", label: "Filings / Quarter", accent: C.orange },
    { value: "0", label: "Manual Extractions", accent: C.purple },
    { value: "24/7", label: "Availability", accent: "3B82F6" },
  ];

  kpis.forEach((kpi, i) => {
    const x = 0.5 + i * 2.35;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.5, w: 2.15, h: 1.6,
      fill: { color: C.white },
      shadow: makeShadow(),
    });

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.5, w: 0.08, h: 1.6,
      fill: { color: kpi.accent },
    });

    slide.addText(kpi.value, {
      x: x + 0.25, y: 3.65, w: 1.7, h: 0.6,
      fontSize: 26, bold: true, color: C.navy, fontFace: FONT_TITLE, align: "center", margin: 0,
    });

    slide.addText(kpi.label, {
      x: x + 0.25, y: 4.35, w: 1.7, h: 0.5,
      fontSize: 11, color: C.textMuted, fontFace: FONT_BODY, align: "center", margin: 0,
    });
  });

  slide.addNotes(
    "Meridian Capital's solution uses a LangChain pipeline: PyPDFLoader reads 10-K/10-Q filings, " +
    "RecursiveCharacterTextSplitter chunks them, a PydanticOutputParser extracts structured financial metrics " +
    "(revenue, EPS, margins, guidance), sequential chains compare across quarters, and a final chain generates " +
    "the analyst report. Results: 85% time reduction (15hrs → 2hrs), 99.2% extraction accuracy, $420K annual savings, " +
    "same-day turnaround. The system processes each filing in 2.3 seconds and runs 24/7."
  );
}

// ──────────────────────────────────────────────
// SLIDE 19 — Key Takeaways
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText("Key Takeaways", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0,
  });

  const takeaways = [
    { num: "1", text: "LangChain provides a modular 4-layer architecture: Provider, Integration, Orchestration, Application", color: C.teal },
    { num: "2", text: "LCEL (pipe operator) is the modern standard — replaces legacy LLMChain with streaming, async, and fallbacks", color: C.orange },
    { num: "3", text: "Output parsers (especially Pydantic) enable type-safe, structured extraction from LLM outputs", color: C.purple },
    { num: "4", text: "Memory types trade off between completeness and token efficiency — choose based on use case", color: "3B82F6" },
    { num: "5", text: "Agents + Tools create autonomous systems — start with Tool Calling Agent, add memory, handle errors", color: C.teal },
    { num: "6", text: "Production demands: caching, fallbacks, retries, parallel execution, security, and monitoring", color: C.orange },
  ];

  takeaways.forEach((t, i) => {
    const y = 1.2 + i * 0.7;

    slide.addShape(pres.shapes.OVAL, {
      x: 0.5, y: y + 0.05, w: 0.45, h: 0.45,
      fill: { color: t.color },
    });
    slide.addText(t.num, {
      x: 0.5, y: y + 0.07, w: 0.45, h: 0.45,
      fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FONT_TITLE,
    });

    slide.addText(t.text, {
      x: 1.2, y: y + 0.05, w: 8.3, h: 0.45,
      fontSize: 13, color: C.textDark, fontFace: FONT_BODY, valign: "middle", margin: 0,
    });
  });

  slide.addNotes(
    "Six key takeaways from Module 2. 1. LangChain's modular architecture enables swapping any component. " +
    "2. LCEL is the modern standard — always use pipe operator chains. 3. Pydantic output parsers ensure type-safe extraction. " +
    "4. Choose memory type based on conversation length and token budget. 5. Agents + Tools create autonomous systems — " +
    "start simple with Tool Calling Agent. 6. Production systems need caching, fallbacks, retries, and monitoring. " +
    "These foundations prepare you for Module 3 (RAG & Vector Databases) and Module 4 (Agentic Systems)."
  );
}

// ──────────────────────────────────────────────
// SLIDE 20 — Thank You / Q&A
// ──────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.navy };

  // Top accent
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3, y: 2.2, w: 4, h: 0.04,
    fill: { color: C.teal },
  });

  slide.addText("Thank You", {
    x: 0, y: 2.5, w: 10, h: 0.9,
    fontSize: 42, bold: true, color: C.white, align: "center", fontFace: FONT_TITLE, margin: 0,
  });

  slide.addText("Questions & Discussion", {
    x: 0, y: 3.4, w: 10, h: 0.5,
    fontSize: 20, color: C.teal, align: "center", fontFace: FONT_BODY, margin: 0,
  });

  // Bottom accent
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3, y: 4.1, w: 4, h: 0.04,
    fill: { color: C.teal },
  });

  slide.addText("Next: Module 3 — RAG & Vector Databases", {
    x: 0, y: 4.4, w: 10, h: 0.4,
    fontSize: 14, color: C.textLight, align: "center", fontFace: FONT_BODY, margin: 0,
  });

  slide.addText("Applied AI Course  |  Part 1: Foundations", {
    x: 0, y: 4.8, w: 10, h: 0.4,
    fontSize: 12, color: C.textLight, align: "center", fontFace: FONT_BODY, margin: 0,
  });

  slide.addNotes(
    "This concludes Module 2. Students should review the concepts, interview questions (28 questions from beginner to advanced), " +
    "and take the quiz (20 questions). The mini-projects provide hands-on practice. Next module covers RAG (Retrieval-Augmented " +
    "Generation) and Vector Databases — building on the chains, memory, and tool foundations from this module."
  );
}

// ──────────────────────────────────────────────
// SAVE
// ──────────────────────────────────────────────
const outputPath = "D:\\Jay Rathod\\Tutorials\\Applied AI\\course-content\\part-1-foundations\\module-2-langchain\\Module-2-LangChain-Framework.pptx";
pres.writeFile({ fileName: outputPath }).then(() => {
  console.log("Presentation saved to: " + outputPath);
});
