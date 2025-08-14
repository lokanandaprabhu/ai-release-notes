#!/usr/bin/env python3
"""
Interactive AI Release Notes Generator
User-friendly script that prompts for PR URLs and generates release notes.
"""

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient
from ai_client import get_ai_client
from jira_client import JiraClient


def get_user_input():
    """Get PR URLs and options from user input."""
    
    print("\n🚀 Interactive AI Release Notes Generator")
    print("=" * 50)
    
    # Get PR URLs
    print("\n📝 Enter PR URL(s):")
    print("• Single PR: https://github.com/owner/repo/pull/123")
    print("• Multiple PRs: separate with commas")
    
    while True:
        try:
            pr_input = input("\n🔗 PR URL(s): ").strip()
            if pr_input:
                break
            print("❌ Please enter at least one PR URL")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    # Parse URLs
    pr_urls = [url.strip() for url in pr_input.split(',') if url.strip()]
    
    # Style selection
    styles = ['standard', 'brief', 'marketing', 'technical', 'changelog']
    print(f"\n🎨 Available styles: {', '.join(styles)}")
    style = input("📋 Select style (default: standard): ").strip().lower() or 'standard'
    if style not in styles:
        print(f"⚠️  Unknown style '{style}', using 'standard'")
        style = 'standard'
    
    # Combined or individual (only for multiple PRs)
    combined = True
    if len(pr_urls) > 1:
        print("\n📄 Output Format:")
        print("1. Combined release notes (all PRs together)")
        print("2. Individual release notes (separate for each PR)")
        
        while True:
            try:
                format_choice = input("\nEnter choice (1-2, default: 1): ").strip() or '1'
                if format_choice in ['1', '2']:
                    break
                print("❌ Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
        
        combined = format_choice == '1'
    
    # Verbose output
    verbose_input = input("\n🔍 Show detailed processing info? (y/n, default: n): ").strip().lower()
    verbose = verbose_input in ['y', 'yes']
    
    return pr_urls, style, combined, verbose


def process_single_pr(github_client, jira_client, pr_url, style, verbose=False):
    """Process a single PR and generate release notes."""
    
    try:
        print(f"\n📥 Fetching PR data from: {pr_url}")
        
        # Parse PR URL and get data
        pr_data = github_client.get_pr_data_from_url(pr_url)
        
        print(f"✅ Found PR #{pr_data['number']}: {pr_data['title']}")
        
        # Show stats
        stats = pr_data.get('stats', {})
        files_count = stats.get('changed_files', 0)
        additions = stats.get('additions', 0)
        deletions = stats.get('deletions', 0)
        print(f"📊 Stats: {files_count} files, {additions} additions, {deletions} deletions")
        
        # Enrich with JIRA data if available
        if jira_client and jira_client.is_configured():
            print("🎯 Enriching PR data with JIRA ticket information...")
            jira_client.enrich_pr_data_with_jira(pr_data)
            
            jira_tickets = pr_data.get('jira_tickets', [])
            if jira_tickets:
                ticket_keys = [ticket['key'] for ticket in jira_tickets]
                print(f"✅ Found {len(jira_tickets)} JIRA ticket(s): {', '.join(ticket_keys)}")
        
        return pr_data
        
    except Exception as e:
        print(f"❌ Error processing {pr_url}: {str(e)}")
        return None


def generate_combined_release_notes(ai_client, prs_data, style, verbose=False):
    """Generate combined release notes for multiple PRs."""
    
    if not prs_data:
        return None
    
    if len(prs_data) == 1:
        # Single PR - use normal generation
        return ai_client.generate_release_notes(prs_data[0], style=style)
    
    print(f"\n🎯 Generating combined release notes for {len(prs_data)} PRs...")
    
    # Create combined PR data
    combined_stats = {'files': 0, 'additions': 0, 'deletions': 0}
    all_jira_tickets = []
    pr_summaries = []
    
    for pr_data in prs_data:
        # Add PR summary
        pr_summaries.append(f"**{pr_data['title']}** (#{pr_data['number']})")
        
        # Aggregate stats
        stats = pr_data.get('stats', {})
        combined_stats['files'] += stats.get('changed_files', 0)
        combined_stats['additions'] += stats.get('additions', 0)
        combined_stats['deletions'] += stats.get('deletions', 0)
        
        # Collect JIRA tickets
        jira_tickets = pr_data.get('jira_tickets', [])
        all_jira_tickets.extend(jira_tickets)
    
    # Create combined data structure
    combined_pr_data = {
        'title': f"Combined Release Notes - {len(prs_data)} PRs",
        'body': f"""
Combined release notes for {len(prs_data)} pull requests.

Included PRs:
{chr(10).join(pr_summaries)}

Total Changes: {combined_stats['files']} files, +{combined_stats['additions']} -{combined_stats['deletions']}
""",
        'repo': prs_data[0]['repo'],
        'author': {'name': 'Combined Release', 'login': 'combined'},
        'stats': {
            'changed_files': combined_stats['files'],
            'additions': combined_stats['additions'],
            'deletions': combined_stats['deletions']
        },
        'commits': [],
        'files_changed': [],
        'labels': [],
        'reviews': [],
        'comments': [],
        'jira_tickets': all_jira_tickets
    }
    
    # Aggregate some data from all PRs (limited to avoid overwhelming AI)
    all_commits = []
    all_files = []
    
    for pr_data in prs_data:
        commits = pr_data.get('commits', [])
        all_commits.extend(commits[:2])  # Max 2 commits per PR
        
        files = pr_data.get('files_changed', [])
        all_files.extend(files[:3])  # Max 3 files per PR
    
    combined_pr_data['commits'] = all_commits[:10]  # Max 10 total commits
    combined_pr_data['files_changed'] = all_files[:20]  # Max 20 total files
    
    # Generate release notes
    return ai_client.generate_release_notes(combined_pr_data, style=style)


def display_release_notes(pr_data, release_notes, style):
    """Display formatted release notes for a single PR."""
    
    print("\n" + "="*80)
    print(f"🚀 RELEASE NOTES - PR #{pr_data['number']}")
    print("="*80)
    print(f"Repository: {pr_data['repo']['full_name']}")
    print(f"PR Title: {pr_data['title']}")
    print(f"Author: {pr_data['author']['name']} (@{pr_data['author']['login']})")
    print(f"Status: {pr_data['state'].upper()}")
    print(f"Style: {style}")
    
    # Show JIRA tickets if available
    jira_tickets = pr_data.get('jira_tickets', [])
    if jira_tickets:
        ticket_keys = [ticket['key'] for ticket in jira_tickets]
        print(f"JIRA Tickets: {', '.join(ticket_keys)}")
    
    print("="*80)
    print(release_notes)


def display_combined_release_notes(prs_data, release_notes, style):
    """Display formatted combined release notes."""
    
    # Calculate combined stats
    total_files = sum(pr.get('stats', {}).get('changed_files', 0) for pr in prs_data)
    total_additions = sum(pr.get('stats', {}).get('additions', 0) for pr in prs_data)
    total_deletions = sum(pr.get('stats', {}).get('deletions', 0) for pr in prs_data)
    
    # Get all repositories
    repos = list(set(pr['repo']['full_name'] for pr in prs_data))
    
    print("\n" + "="*80)
    print(f"🚀 COMBINED RELEASE NOTES - {len(prs_data)} PRs")
    print("="*80)
    print(f"Repositories: {', '.join(repos)}")
    print(f"PRs Included: {len(prs_data)}")
    print(f"Total Changes: {total_files} files, +{total_additions} -{total_deletions}")
    print(f"Style: {style}")
    print("="*80)
    print(release_notes)


def main():
    """Main function."""
    load_dotenv()
    
    try:
        # Get user input
        pr_urls, style, combined, verbose = get_user_input()
        
        # Initialize clients
        github_client = GitHubClient()
        ai_client = get_ai_client()
        
        # Initialize JIRA client if configured
        jira_client = None
        if all(os.getenv(key) for key in ['JIRA_SERVER', 'JIRA_USERNAME', 'JIRA_API_TOKEN']):
            jira_client = JiraClient()
            if not jira_client.is_configured():
                jira_client = None
        
        # Process all PRs
        prs_data = []
        for i, pr_url in enumerate(pr_urls, 1):
            print(f"\n📝 Processing PR {i}/{len(pr_urls)}: {pr_url}")
            
            pr_data = process_single_pr(github_client, jira_client, pr_url, style, verbose)
            if pr_data:
                prs_data.append(pr_data)
                
                # For individual mode, generate and display immediately
                if not combined:
                    print(f"\n🎯 Generating release notes for PR #{pr_data['number']}...")
                    release_notes = ai_client.generate_release_notes(pr_data, style=style)
                    display_release_notes(pr_data, release_notes, style)
                    
                    if i < len(pr_urls):
                        print("\n" + "-"*80)
        
        if not prs_data:
            print("\n❌ No PRs could be processed successfully")
            return
        
        # For combined mode, generate notes for all PRs together
        if combined:
            release_notes = generate_combined_release_notes(ai_client, prs_data, style, verbose)
            if release_notes:
                display_combined_release_notes(prs_data, release_notes, style)
            else:
                print("\n❌ Failed to generate combined release notes")
        
        print(f"\n✅ Successfully processed {len(prs_data)}/{len(pr_urls)} PRs")
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
