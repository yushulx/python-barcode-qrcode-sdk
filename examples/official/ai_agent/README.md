# AI Agent Coding Test: Dynamsoft Barcode Reader SDK

A comprehensive experiment testing multiple AI coding agents' ability to generate accurate, up-to-date code for the Dynamsoft Barcode Reader Python SDK.

## Project Overview

This project documents an experiment comparing five major AI coding agents using a single prompt:

> **"Create a command line barcode scanner in Python using the Dynamsoft Barcode Reader SDK"**

### Tested AI Agents

1. **Claude Sonnet 4**
2. **Claude Sonnet 4.5** ✅ (Only agent with correct code initially)
3. **Gemini 2.5 Pro**
4. **GPT-5**
5. **Grok Code**

## Key Findings

### The Problem

Out of five AI agents tested, only **Claude Sonnet 4.5** generated code using the **latest version** of the Dynamsoft Barcode Reader SDK. The other four agents produced code based on the outdated `dbr` package instead of the current `dynamsoft-barcode-reader-bundle`.

### The Solution

By creating a **custom agent definition** in `.github/agents/python-barcode-scanner.agent.md`, we achieved:

- **100% success rate** across all AI agents
- All agents now fetch latest documentation before coding
- Consistent, accurate code generation
- Up-to-date API usage

## Results Comparison

### Before Custom Agent

| AI Agent | Package Used | Result |
|----------|--------------|--------|
| Claude Sonnet 4 | `dbr` (outdated) | ❌ Failed |
| Claude Sonnet 4.5 | `dynamsoft-barcode-reader-bundle` | ✅ Success |
| Gemini 2.5 Pro | `dbr` (outdated) | ❌ Failed |
| GPT-5 | `dbr` (outdated) | ❌ Failed |
| Grok Code | `dbr` (outdated) | ❌ Failed |

### After Custom Agent

| AI Agent | Package Used | Result |
|----------|--------------|--------|
| All Agents | `dynamsoft-barcode-reader-bundle` | ✅ Success |

**Achievement: 100% success rate!**

## The Custom Agent Solution

The custom agent definition includes:

### Key Components

1. **Tool Specifications**: Forces agents to use `fetch`, `githubRepo`, `search`, and `edit` tools
2. **Golden Rules**: Explicit instructions to:
   - Always use the latest package (`dynamsoft-barcode-reader-bundle`)
   - Fetch documentation before generating code
   - Trust documentation over training data
   - Create actual code files, not just snippets

3. **Documentation URLs**: Direct links to:
   - Official Python SDK documentation
   - User guide and API reference
   - GitHub sample repositories

### Example Custom Agent Structure

```markdown
---
description: 'Python helper for Dynamsoft Barcode Reader that always checks the latest docs'
tools:
  - fetch       # read web pages for latest docs
  - githubRepo  # search Dynamsoft sample repos
  - search      # workspace/code search
  - edit        # edit files in the workspace
---

# Role
You are an expert Python assistant for the Dynamsoft Barcode Reader SDK.

## Golden rules
1. **Always use latest Python package**: `dynamsoft-barcode-reader-bundle`
2. **Always check documentation first**: Use fetch tool before coding
3. **Trust the docs**: If docs conflict with training data, follow docs
4. **Create actual files**: Generate complete, runnable scripts

```

## Blog
[Solving the AI Knowledge Gap: Testing AI Agents with Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/codepool/claude-gemini-grok-gpt-barcode-coding.html)

