#!/usr/bin/env python3
"""
AI Release Notes Generator - Command Line Interface

Generate professional release notes from GitHub Pull Request URLs using AI.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient
from ai_client import get_ai_client, RELEASE_NOTE_STYLES
from jira_client import JiraClient


def show_demo_output(args):
    """Show demo output for testing purposes."""
    print("\n" + "="*80)
    print("🚀 RELEASE NOTES - PR #1234 (DEMO MODE)")
    print("="*80)
    print("Repository: example/awesome-project")
    print("PR Title: Add dark mode toggle and improve UI accessibility")
    print("Author: Jane Developer (@jane-dev)")
    print("Status: MERGED")
    print(f"Style: {args.style} | Provider: {args.provider}")
    print("="*80)
    print()
    
    # Different demo content based on style
    if args.style == "brief":
        demo_content = """• Added dark mode toggle in settings
• Improved keyboard navigation support
• Fixed color contrast issues for accessibility
• Updated button styles and hover states
• Added theme persistence in localStorage"""

    elif args.style == "marketing":
        demo_content = """## 🌙 Introducing Dark Mode!

Your users can now enjoy a sleek, eye-friendly dark interface that's perfect for late-night coding sessions.

**What's New:**
- **Dark Mode Toggle** - Switch between light and dark themes instantly
- **Enhanced Accessibility** - Better keyboard navigation and improved color contrast
- **Persistent Preferences** - Your theme choice is remembered across sessions
- **Polished UI** - Updated button styles and smooth hover animations

**User Impact:**
This update makes your application more accessible and comfortable to use, especially in low-light environments. Perfect for developers who code at night!"""

    elif args.style == "technical":
        demo_content = """## Technical Changes

### Frontend Components
- **ThemeProvider**: Added React context for theme management
- **DarkModeToggle**: New component with CSS-in-JS styling
- **Button**: Updated with theme-aware hover states and focus indicators

### Accessibility Improvements
- Added ARIA labels for screen readers
- Implemented keyboard navigation with Tab/Enter support
- Color contrast ratios now meet WCAG 2.1 AA standards

### State Management
- Theme preference stored in localStorage with fallback to system preference
- Added custom hook `useTheme()` for component consumption

### Browser Support
- CSS custom properties for dynamic theming
- Fallback support for older browsers using PostCSS"""

    elif args.style == "changelog":
        demo_content = """### Added
- Dark mode toggle in user preferences
- Keyboard navigation support for all interactive elements
- ARIA labels for improved screen reader compatibility
- Theme persistence using localStorage

### Changed
- Button component styling updated for better accessibility
- Color palette expanded to support both light and dark themes
- Focus indicators enhanced with better contrast ratios

### Fixed
- Color contrast issues that failed WCAG guidelines
- Tab navigation order in settings panel
- Theme flicker on page load"""

    else:  # standard
        demo_content = """## What's New

### 🌙 Dark Mode Support
Added a comprehensive dark mode theme that users can toggle from the settings panel. The dark theme provides a comfortable viewing experience in low-light environments while maintaining excellent readability.

### ♿ Enhanced Accessibility
Significantly improved the application's accessibility with better keyboard navigation, ARIA labels, and color contrast ratios that meet WCAG 2.1 AA standards.

## Impact

**For End Users:**
- More comfortable viewing experience with dark mode option
- Better accessibility for users with visual impairments or motor difficulties
- Reduced eye strain during extended usage periods

**For Developers:**
- Consistent theming system that can be easily extended
- Improved component reusability with theme-aware styling

## Technical Details

- Implemented React Context API for theme state management
- Added CSS custom properties for dynamic theme switching
- Enhanced Button component with improved focus states and hover animations
- Theme preferences persist across browser sessions using localStorage

## Breaking Changes

None - this update is fully backward compatible."""

    print(demo_content)
    print()
    print("="*80)
    print("✨ This is demo output. To generate real release notes, set up your API keys and remove --demo flag.")


def main():
    """Main CLI function."""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Generate AI-powered release notes from GitHub PR URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://github.com/owner/repo/pull/123
  python main.py https://github.com/owner/repo/pull/123 --style brief
  python main.py https://github.com/owner/repo/pull/123 --verbose
  python main.py https://github.com/owner/repo/pull/123 --jira-server https://company.atlassian.net
  
Available styles: """ + ", ".join(RELEASE_NOTE_STYLES.keys())
    )
    
    parser.add_argument(
        'pr_url',
        help='GitHub Pull Request URL'
    )
    
    parser.add_argument(
        '--style',
        choices=list(RELEASE_NOTE_STYLES.keys()),
        default='standard',
        help='Release notes style (default: standard)'
    )
    
    parser.add_argument(
        '--provider',
        choices=['gemini'],
        default='gemini',
        help='AI provider to use (only Gemini supported)'
    )
    
    parser.add_argument(
        '--github-token',
        help='GitHub API token (overrides GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--api-key',
        help='AI API key (overrides GEMINI_API_KEY env var)'
    )
    
    parser.add_argument(
        '--jira-server',
        help='JIRA server URL (e.g., https://yourcompany.atlassian.net)'
    )
    
    parser.add_argument(
        '--jira-username',
        help='JIRA username/email'
    )
    
    parser.add_argument(
        '--jira-token',
        help='JIRA API token'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress information'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Demo mode - show sample output without requiring API keys'
    )
    
    args = parser.parse_args()
    
    try:
        # Demo mode - show sample output
        if args.demo:
            show_demo_output(args)
            return
        
        # Initialize clients
        if args.verbose:
            print("🔧 Initializing GitHub client...")
        
        github_client = GitHubClient(token=args.github_token)
        
        if args.verbose:
            print(f"🤖 Initializing AI client ({args.provider})...")
        
        # Set API key if provided
        if args.api_key:
            os.environ['GEMINI_API_KEY'] = args.api_key
        
        # Initialize JIRA client (optional)
        jira_client = None
        if args.jira_server or os.getenv('JIRA_SERVER'):
            if args.verbose:
                print("🔧 Initializing JIRA client...")
            jira_client = JiraClient(
                server=args.jira_server,
                username=args.jira_username, 
                api_token=args.jira_token
            )
            if jira_client.is_configured():
                if args.verbose:
                    print("✅ JIRA client configured successfully")
            else:
                if args.verbose:
                    print("⚠️  JIRA client not fully configured (optional)")
        
        # Initialize Gemini AI client
        ai_client = get_ai_client(args.provider)
        if args.verbose:
            print(f"✅ Using Gemini AI client")
        
        # Fetch PR data
        if args.verbose:
            print(f"📥 Fetching PR data from: {args.pr_url}")
        
        pr_data = github_client.get_pr_from_url(args.pr_url)
        
        # Enrich with JIRA data if available
        if jira_client and jira_client.is_configured():
            if args.verbose:
                print("🎯 Enriching PR data with JIRA ticket information...")
            pr_data = jira_client.enrich_pr_data_with_jira(pr_data)
            
            jira_tickets = pr_data.get('jira_tickets', [])
            if jira_tickets and args.verbose:
                print(f"✅ Found {len(jira_tickets)} JIRA ticket(s): {', '.join([t['key'] for t in jira_tickets])}")
            elif args.verbose:
                print("ℹ️  No JIRA tickets found in PR")
        
        if args.verbose:
            print(f"✅ Found PR #{pr_data['number']}: {pr_data['title']}")
            print(f"📊 Stats: {pr_data['stats']['changed_files']} files, "
                  f"{pr_data['stats']['additions']} additions, "
                  f"{pr_data['stats']['deletions']} deletions")
            print(f"🎯 Generating release notes in '{args.style}' style...")
        
        # Generate release notes
        release_notes = ai_client.generate_release_notes(pr_data, args.style)
        
        # Output results
        print("\n" + "="*80)
        print(f"🚀 RELEASE NOTES - PR #{pr_data['number']}")
        print("="*80)
        print(f"Repository: {pr_data['repo']['full_name']}")
        print(f"PR Title: {pr_data['title']}")
        print(f"Author: {pr_data['author']['name']} (@{pr_data['author']['login']})")
        print(f"Status: {pr_data['state'].upper()}" + (" (MERGED)" if pr_data['merged'] else ""))
        print(f"Style: {args.style} | Provider: Gemini")
        print("="*80)
        print()
        print(release_notes)
        print()
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        
        if args.verbose:
            import traceback
            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()
