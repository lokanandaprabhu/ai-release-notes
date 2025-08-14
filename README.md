# AI Release Notes Generator

Generate professional release notes from GitHub Pull Request URLs using Google Gemini AI.

## Quick Start (Demo Mode)

Want to see it in action? Try the demo mode without any setup:

```bash
# Clone and run demo
git clone <your-repo-url>
cd ai-release-notes
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# See sample output in different styles
./venv/bin/python main.py https://github.com/example/repo/pull/123 --demo
./venv/bin/python main.py https://github.com/example/repo/pull/123 --demo --style brief
./venv/bin/python main.py https://github.com/example/repo/pull/123 --demo --style marketing
```

## Setup

1. **Create and activate virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

4. **Configure API keys:**
   - **GitHub Token:** Required for accessing GitHub API (get from [GitHub Settings](https://github.com/settings/tokens))
   - **Gemini API Key:** Required for AI-powered release notes generation
   - **JIRA Integration (required for sprint/ticket features):** Enriches release notes with JIRA ticket details
     - JIRA Server URL (e.g., https://issues.redhat.com or https://yourcompany.atlassian.net)
     - JIRA Username/Email
     - JIRA API Token

## Usage

### Interactive Mode (Recommended)

The easiest way to use the tool is with the interactive interface:

```bash
# Start interactive mode - prompts for PR URLs and options
./interactive_notes.sh
```

**Features:**

- ✅ User-friendly prompts for PR URLs (single or multiple, comma-separated)
- ✅ Style selection menu
- ✅ Option to combine multiple PRs into one release note
- ✅ Verbose output control
- ✅ Input validation and error handling

### Branch Release Notes

Generate release notes for all PRs merged to a specific branch within a date range:

```bash
# Generate release notes for a branch and time period
./branch_notes.sh
```

**Perfect for:**

- 🚀 **Release Notes**: Generate notes for all PRs in a release branch (e.g., release-4.15)
- 📅 **Sprint Summaries**: Get all changes for a specific time period
- 🌿 **Branch Analysis**: See what changed in any branch over time
- 📊 **Periodic Reports**: Weekly/monthly development summaries

**Features:**

- ✅ Search by repository, branch, and date range
- ✅ Automatic PR discovery using GitHub's search API
- ✅ JIRA integration for enhanced context
- ✅ Combined release notes for all found PRs
- ✅ Detailed PR statistics and summaries

**Example Use Cases:**

- All PRs merged to `release-4.15` branch in last 30 days
- Changes in `main` branch between 2024-01-01 and 2024-01-31
- Sprint summary for `main` branch in the last 2 weeks

### Sprint Release Notes

Generate release notes for all PRs associated with a specific sprint:

```bash
# Generate release notes for a sprint
./sprint_notes.sh
```

**Search Methods:**

- 🎫 **Sprint Name**: Search by JIRA sprint name like `ODC Sprint 3278`
- 🔢 **Sprint Number**: Search by JIRA sprint ID like `74447` (from Red Hat JIRA URLs)

**Perfect for:**

- 📊 **Sprint Reviews**: Complete overview of sprint deliverables
- 🔄 **Retrospectives**: Detailed analysis of sprint work
- 📈 **Team Reports**: Progress summaries for stakeholders
- 🎯 **Goal Tracking**: Verify sprint objectives completion

**Features:**

- ✅ JIRA sprint name and ID search methods
- ✅ Combined or individual release notes
- ✅ PR state filtering (merged, open, closed, all)
- ✅ JIRA integration for enhanced context
- ✅ Team collaboration insights

**Example Sprint Searches:**

- **JIRA Sprint Name**: `ODC Sprint 3278`
- **JIRA Sprint ID**: `74447` (extracted from [Red Hat JIRA URLs](https://issues.redhat.com/secure/RapidBoard.jspa?rapidView=5480&sprint=74447))

### JIRA Ticket Release Notes

Generate release notes from specific JIRA ticket(s) with optional GitHub PR enhancement:

```bash
# Generate release notes for JIRA tickets
./jira_ticket_notes.sh
```

**Input Options:**

- 🎫 **Single ticket**: `ODC-7806`
- 🎫 **Multiple tickets**: `ODC-7806, SRVKP-8210, OCPBUGS-59564`

**Perfect for:**

- 📋 **Feature Documentation**: Document specific implemented tickets
- 🎯 **Targeted Updates**: Generate notes for particular JIRA items
- 📊 **Status Reports**: Show progress on specific tickets
- 🔗 **Mixed Scenarios**: Tickets with or without GitHub PRs

**Features:**

- ✅ **Smart PR Detection**: Automatically finds GitHub PRs linked to JIRA tickets
- ✅ **Enhanced Release Notes**: Combines JIRA context with PR technical details
- ✅ **JIRA-Only Fallback**: Generates notes from JIRA data when no PR is linked
- ✅ **Combined or Individual**: Choose output format for multiple tickets
- ✅ **Auto-validation**: Validates JIRA ticket ID format

**How It Works:**

1. **Fetches JIRA ticket data** (summary, description, status, priority)
2. **Searches for GitHub PR links** in JIRA ticket (comments, description, remote links)
3. **Enhances with PR data** if found (files changed, commits, stats)
4. **Generates comprehensive release notes** using both JIRA and PR context
5. **Falls back to JIRA-only** if no GitHub PR is linked

**Example Use Cases:**

- Document `ODC-7806` (has PR) + `SOME-TICKET` (no PR) together
- Generate release notes for tickets assigned to you
- Create feature documentation from JIRA ticket requirements

### Basic Usage

**Single PR Release Notes:**

```bash
# Simple one-liner (automatically uses virtual environment)
./generate_release_notes.sh https://github.com/owner/repo/pull/123
```

**Basic Release Notes (simplified):**

```bash
# Generate basic release notes without advanced features
./basic_notes.sh
```

**Show PR Files:**

```bash
# List all files changed in a PR
./show_files.sh
```

### With Options

```bash
# Use different style
./generate_release_notes.sh https://github.com/owner/repo/pull/123 --style brief

# Verbose output for debugging
./generate_release_notes.sh https://github.com/owner/repo/pull/123 --verbose

# With JIRA integration for richer context
./generate_release_notes.sh https://github.com/owner/repo/pull/123 --jira-server https://company.atlassian.net

# Override API keys (useful for testing)
./generate_release_notes.sh https://github.com/owner/repo/pull/123 --api-key your_key_here

# Demo mode (no API keys required)
./generate_release_notes.sh https://github.com/example/repo/pull/123 --demo
```

## Available Scripts

| Script                        | Purpose                                         |
| ----------------------------- | ----------------------------------------------- |
| `./interactive_notes.sh`      | **Recommended** - Interactive mode with prompts |
| `./jira_ticket_notes.sh`      | **🆕 JIRA tickets** - Enhanced with PR data     |
| `./sprint_notes.sh`           | Sprint-based release notes                      |
| `./branch_notes.sh`           | Branch + date range release notes               |
| `./generate_release_notes.sh` | Single PR with full options                     |
| `./basic_notes.sh`            | Simple release notes (minimal setup)            |
| `./show_files.sh`             | Show all files changed in a PR                  |

## Available Styles

- **standard** - Professional and comprehensive release notes (default)
- **brief** - Concise bullet-point format
- **marketing** - User-focused with emphasis on benefits
- **technical** - Developer-focused with technical details
- **changelog** - Traditional changelog format

## JIRA Integration

JIRA integration is **required** for sprint and ticket-based features, and **optional** for individual PR release notes:

### **When JIRA is Required:**

- ✅ **Sprint Release Notes** (`./sprint_notes.sh`) - Queries JIRA for sprint tickets
- ✅ **JIRA Ticket Notes** (`./jira_ticket_notes.sh`) - Processes JIRA tickets directly
- ✅ **Branch Notes** (when JIRA enrichment is desired)

### **When JIRA is Optional:**

- ⚪ **Interactive Notes** (`./interactive_notes.sh`) - Enhances PR data if available
- ⚪ **Single PR Notes** (`./generate_release_notes.sh`) - Adds JIRA context if found
- ⚪ **Basic Notes** (`./basic_notes.sh`) - Works with or without JIRA

The tool can automatically detect and fetch JIRA ticket information to create richer release notes:

### **Automatic Detection:**

- Scans PR title, description, and commit messages for JIRA ticket IDs (e.g., SRVKP-8209, ODC-7806)
- Fetches detailed ticket information from JIRA API
- Enriches release notes with:
  - Ticket summary and description
  - Status and priority
  - Issue type (Bug, Story, Task, etc.)
  - Components and fix versions

### **Setup JIRA Integration:**

```bash
# Add to .env file
JIRA_SERVER=https://issues.redhat.com
JIRA_USERNAME=your.email@redhat.com
JIRA_API_TOKEN=your_jira_api_token

# Or pass as command line arguments
./generate_release_notes.sh PR_URL --jira-server https://issues.redhat.com --jira-username email@redhat.com --jira-token token
```

### **JIRA API Token Setup:**

**For Red Hat JIRA (issues.redhat.com):**

1. Log into https://issues.redhat.com
2. Go to Profile → Personal Access Tokens
3. Create a new token with appropriate permissions
4. Copy the generated token
5. Add to your `.env` file or pass as `--jira-token`

**For Atlassian Cloud JIRA:**

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the generated token
4. Add to your `.env` file or pass as `--jira-token`

## Examples

### Standard Output

```bash
$ python main.py https://github.com/microsoft/vscode/pull/12345

================================================================================
🚀 RELEASE NOTES - PR #12345
================================================================================
Repository: microsoft/vscode
PR Title: Add new file explorer features
Author: John Doe (@johndoe)
Status: MERGED
Style: standard | Provider: openai
================================================================================

## What's New

- Enhanced file explorer with new sorting options
- Added drag-and-drop functionality for better file management
- Improved performance for large directory structures

## Impact

Users can now organize their workspace more efficiently with improved file management capabilities...
```

### Brief Style

```bash
$ python main.py https://github.com/owner/repo/pull/123 --style brief

• Added file sorting options
• Implemented drag-and-drop
• Fixed performance issues
• Updated UI components
```

## Requirements

- Python 3.8+
- GitHub API token
- Google Gemini API key
- JIRA API credentials (optional, for enhanced release notes)

## Error Handling

The tool provides clear error messages for common issues:

- Invalid GitHub URLs
- Missing API keys
- Network connectivity problems
- API rate limits

Use `--verbose` flag for detailed error information and debugging.

## What This Tool Does

1. **Fetches PR Data** - Connects to GitHub API to gather comprehensive pull request information including:

   - Title, description, and labels
   - File changes and statistics
   - Commit messages and author info
   - Review comments and status

2. **AI-Powered Analysis** - Uses Google Gemini AI to:

   - Analyze code changes and their impact
   - Generate user-focused release notes
   - Adapt tone and style based on your preferences
   - Focus on user-facing changes rather than implementation details

3. **Professional Output** - Produces clean, formatted release notes that include:
   - Clear descriptions of new features and changes
   - User impact explanations
   - Technical details when relevant
   - Breaking changes if any

Perfect for automating release note generation in your CI/CD pipeline or for quickly creating professional documentation for your GitHub releases!
