"""AI client for generating release notes from PR data using Google Gemini."""

import os
from typing import Dict, Optional


class GeminiClient:
    """Google Gemini client for generating release notes."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            api_key = api_key or os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass --api-key")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except ImportError:
            raise ImportError("Google Generative AI library not installed. Run: pip install google-generativeai")
    
    def generate_release_notes(self, pr_data: Dict, style: str = "standard") -> str:
        """Generate release notes using Google Gemini."""
        prompt = self._create_prompt(pr_data, style)
        
        try:
            # Add system instruction to the prompt
            full_prompt = "You are a technical writer specializing in creating clear, concise release notes for software projects.\n\n" + prompt
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 1500,
                }
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Error generating release notes with Gemini: {str(e)}")
    
    def _create_prompt(self, pr_data: Dict, style: str) -> str:
        """Create prompt for AI based on PR data and style."""
        
        # Extract key information
        title = pr_data.get('title', '')
        body = pr_data.get('body', '')
        files_changed = pr_data.get('files_changed', [])
        commits = pr_data.get('commits', [])
        labels = pr_data.get('labels', [])
        stats = pr_data.get('stats', {})
        
        # Create file summary with better organization for large PRs
        file_summary = []
        total_files = len(files_changed)
        
        if total_files <= 15:
            # Show all files for small PRs
            for file in files_changed:
                file_summary.append(f"- {file['filename']} (+{file['additions']}/-{file['deletions']})")
        else:
            # For large PRs, categorize and show more strategically
            # Group by directory/component
            file_groups = {}
            for file in files_changed:
                # Extract component/directory
                parts = file['filename'].split('/')
                if len(parts) > 3:
                    component = '/'.join(parts[:3])
                else:
                    component = parts[0] if parts else 'root'
                
                if component not in file_groups:
                    file_groups[component] = []
                file_groups[component].append(file)
            
            # Show top components and their key files
            for component, files in list(file_groups.items())[:8]:  # Top 8 components
                file_summary.append(f"- **{component}/**:")
                for file in files[:3]:  # Show first 3 files per component
                    file_summary.append(f"  - {file['filename'].split('/')[-1]} (+{file['additions']}/-{file['deletions']})")
                if len(files) > 3:
                    file_summary.append(f"  - ... and {len(files) - 3} more files in this component")
            
            if len(file_groups) > 8:
                file_summary.append(f"- ... and {len(file_groups) - 8} more components")
        
        # Create commit summary
        commit_messages = [commit['message'].split('\n')[0] for commit in commits[:5]]
        
        # Add JIRA ticket information if available
        jira_info = ""
        jira_tickets = pr_data.get('jira_tickets', [])
        if jira_tickets:
            jira_info = "\n**JIRA Tickets:**\n"
            for ticket in jira_tickets:
                jira_info += f"- **{ticket['key']}** ({ticket['issue_type']}): {ticket['summary']}\n"
                if ticket['description']:
                    # Truncate description to first 200 chars
                    desc = ticket['description'][:200] + "..." if len(ticket['description']) > 200 else ticket['description']
                    jira_info += f"  Description: {desc}\n"
                jira_info += f"  Status: {ticket['status']} | Priority: {ticket['priority']}\n"
                if ticket['components']:
                    jira_info += f"  Components: {', '.join(ticket['components'])}\n"
        
        prompt = f"""
Based on the following pull request information, generate professional release notes.

**PR Title:** {title}

**PR Description:**
{body}

**Labels:** {', '.join(labels) if labels else 'None'}

**Statistics:**
- Files changed: {stats.get('changed_files', 0)}
- Additions: {stats.get('additions', 0)}
- Deletions: {stats.get('deletions', 0)}
- Commits: {stats.get('commits', 0)}

**Key Files Changed:**
{chr(10).join(file_summary) if file_summary else 'No files listed'}

**Recent Commits:**
{chr(10).join(f"- {msg}" for msg in commit_messages) if commit_messages else 'No commits listed'}
{jira_info}
**Style Guide: {style}**

Please generate release notes that include:
1. **What's New/Changed** - Main features or changes introduced
2. **Impact** - How this affects users or the system
3. **Technical Details** - Brief technical summary (if applicable)
4. **Breaking Changes** - Any backwards incompatible changes (if any)

Keep the tone professional but accessible. Focus on user-facing impact rather than implementation details.
Format the output in clean markdown.
"""
        
        return prompt


def get_ai_client(provider: str = "gemini") -> GeminiClient:
    """Factory function to get Gemini AI client."""
    if provider.lower() != "gemini":
        raise ValueError(f"Only Gemini provider is supported. Got: {provider}")
    return GeminiClient()


# Release note style templates
RELEASE_NOTE_STYLES = {
    "standard": "Professional and comprehensive release notes",
    "brief": "Concise bullet-point format",
    "marketing": "User-focused with emphasis on benefits",
    "technical": "Developer-focused with technical details",
    "changelog": "Traditional changelog format"
}