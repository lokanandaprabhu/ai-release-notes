#!/usr/bin/env python3
"""
Branch Release Notes Generator
Generate release notes for all PRs merged to a specific branch within a date range.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient
from ai_client import get_ai_client
from jira_client import JiraClient
from github import Github


def get_branch_input():
    """Get branch search parameters from user input."""
    
    print("\n🌿 Branch Release Notes Generator")
    print("=" * 50)
    
    # Repository
    repo_input = input("\n📦 Enter repository (owner/repo, e.g., openshift/console): ").strip()
    if not repo_input or '/' not in repo_input:
        print("❌ Invalid repository format")
        return get_branch_input()
    
    owner, repo = repo_input.split('/', 1)
    owner = owner.strip()
    repo = repo.strip()
    
    # Branch
    branch = input("\n🌿 Enter branch name (e.g., main, release-4.15, develop): ").strip()
    if not branch:
        print("❌ Branch name cannot be empty")
        return get_branch_input()
    
    # Date range options
    print("\n📅 Date Range Configuration")
    print("Choose an option:")
    print("1. Last N days")
    print("2. Specific date range")
    print("3. Since specific date")
    
    while True:
        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("❌ Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    # Get date parameters
    start_date = None
    end_date = None
    
    if choice == '1':
        # Last N days
        while True:
            try:
                days = int(input("Enter number of days (e.g., 7, 30): ").strip())
                if days > 0:
                    break
                print("❌ Please enter a positive number")
            except (ValueError, KeyboardInterrupt):
                if isinstance(sys.exc_info()[1], KeyboardInterrupt):
                    print("\n\n👋 Goodbye!")
                    sys.exit(0)
                print("❌ Please enter a valid number")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
    elif choice == '2':
        # Specific date range
        while True:
            try:
                start_input = input("Enter start date (YYYY-MM-DD): ").strip()
                start_date = datetime.strptime(start_input, '%Y-%m-%d')
                break
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
        
        while True:
            try:
                end_input = input("Enter end date (YYYY-MM-DD): ").strip()
                end_date = datetime.strptime(end_input, '%Y-%m-%d')
                break
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
        
    else:  # choice == '3'
        # Since specific date
        while True:
            try:
                start_input = input("Enter start date (YYYY-MM-DD): ").strip()
                start_date = datetime.strptime(start_input, '%Y-%m-%d')
                break
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
        
        end_date = datetime.now()
    
    # Style selection
    styles = ['standard', 'brief', 'marketing', 'technical', 'changelog']
    print(f"\n🎨 Available styles: {', '.join(styles)}")
    style = input("📋 Select style (default: standard): ").strip().lower() or 'standard'
    if style not in styles:
        print(f"⚠️  Unknown style '{style}', using 'standard'")
        style = 'standard'
    
    # Combined or individual
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
    
    return owner, repo, branch, start_date, end_date, style, combined, verbose


def search_merged_prs(github_client, owner, repo, branch, start_date, end_date, verbose=False):
    """Search for merged PRs in the specified branch and date range."""
    
    print(f"\n🔍 Searching for merged PRs in {owner}/{repo} ({branch} branch)...")
    if verbose:
        print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        github = Github(github_client.token)
        
        # Build search query
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        search_query = f'repo:{owner}/{repo} is:pr is:merged base:{branch} merged:{start_str}..{end_str}'
        
        if verbose:
            print(f"   Search query: {search_query}")
        
        issues = github.search_issues(search_query)
        
        print(f"✅ Found {issues.totalCount} merged PR(s)")
        
        prs_data = []
        for issue in issues:
            if verbose:
                print(f"   Found PR #{issue.number}: {issue.title}")
            
            try:
                # Get detailed PR data
                pr_data = github_client.get_pr_data(owner, repo, issue.number)
                prs_data.append({
                    'pr_data': pr_data,
                    'url': f"https://github.com/{owner}/{repo}/pull/{issue.number}"
                })
            except Exception as e:
                print(f"   ❌ Error fetching PR #{issue.number}: {str(e)}")
                continue
        
        return prs_data
        
    except Exception as e:
        print(f"❌ Error searching for PRs: {str(e)}")
        return []


def generate_branch_release_notes(ai_client, prs_data, branch, style, combined=True, verbose=False):
    """Generate release notes for branch PRs."""
    
    if not prs_data:
        return None, []
    
    if combined:
        # Generate combined release notes
        if verbose:
            print(f"\n🎯 Generating combined release notes...")
        
        # Combine all PR data
        total_stats = {'files': 0, 'additions': 0, 'deletions': 0}
        pr_summaries = []
        all_jira_tickets = []
        
        for pr_info in prs_data:
            pr_data = pr_info['pr_data']
            pr_summaries.append(f"**{pr_data['title']}** (#{pr_data['number']})")
            
            # Aggregate stats
            pr_stats = pr_data.get('stats', {})
            total_stats['files'] += pr_stats.get('changed_files', 0)
            total_stats['additions'] += pr_stats.get('additions', 0)
            total_stats['deletions'] += pr_stats.get('deletions', 0)
            
            # Collect JIRA tickets
            jira_tickets = pr_data.get('jira_tickets', [])
            all_jira_tickets.extend(jira_tickets)
        
        # Create combined PR data
        combined_pr_data = {
            'title': f"Branch {branch} Release Notes - {len(prs_data)} PRs",
            'body': f"""
Branch release notes for {len(prs_data)} pull requests merged to {branch}.

Included PRs:
{chr(10).join(pr_summaries)}

Total Changes: {total_stats['files']} files, +{total_stats['additions']} -{total_stats['deletions']}
""",
            'repo': prs_data[0]['pr_data']['repo'],
            'author': {'name': 'Branch Release', 'login': 'branch'},
            'stats': {
                'changed_files': total_stats['files'],
                'additions': total_stats['additions'],
                'deletions': total_stats['deletions']
            },
            'commits': [],
            'files_changed': [],
            'labels': [],
            'reviews': [],
            'comments': [],
            'jira_tickets': all_jira_tickets
        }
        
        # Aggregate limited data from all PRs
        all_commits = []
        all_files = []
        
        for pr_info in prs_data:
            pr_data = pr_info['pr_data']
            commits = pr_data.get('commits', [])
            all_commits.extend(commits[:2])  # Max 2 commits per PR
            
            files = pr_data.get('files_changed', [])
            all_files.extend(files[:3])  # Max 3 files per PR
        
        combined_pr_data['commits'] = all_commits[:15]  # Max 15 total commits
        combined_pr_data['files_changed'] = all_files[:30]  # Max 30 total files
        
        # Generate release notes
        release_notes = ai_client.generate_release_notes(combined_pr_data, style=style)
        return release_notes, total_stats
    
    else:
        # Generate individual release notes
        individual_notes = []
        
        for i, pr_info in enumerate(prs_data, 1):
            if verbose:
                print(f"\n🎯 Generating release notes for PR {i}/{len(prs_data)}")
            
            pr_data = pr_info['pr_data']
            release_notes = ai_client.generate_release_notes(pr_data, style=style)
            
            individual_notes.append({
                'release_notes': release_notes,
                'pr_data': pr_data,
                'url': pr_info['url']
            })
        
        return individual_notes, None


def display_branch_release_notes(release_notes, prs_data, owner, repo, branch, start_date, end_date, style, combined=True, stats=None):
    """Display formatted branch release notes."""
    
    if combined and release_notes:
        # Display combined release notes
        print("\n" + "="*80)
        print(f"🌿 BRANCH RELEASE NOTES")
        print("="*80)
        print(f"Repository: {owner}/{repo}")
        print(f"Branch: {branch}")
        print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"PRs Found: {len(prs_data)}")
        if stats:
            print(f"Files Changed: {stats['files']}")
            print(f"Total Changes: +{stats['additions']} -{stats['deletions']}")
        print(f"Style: {style}")
        print("="*80)
        print(release_notes)
        
    elif not combined and isinstance(release_notes, list):
        # Display individual release notes
        display_individual_pr_notes(release_notes, owner, repo, branch, start_date, end_date, style)
    
    else:
        print("\n❌ No release notes to display")


def display_individual_pr_notes(release_notes, owner, repo, branch, start_date, end_date, style):
    """Display individual PR release notes."""
    
    for i, note_data in enumerate(release_notes, 1):
        pr_data = note_data['pr_data']
        
        print("\n" + "="*80)
        print(f"🌿 BRANCH PR #{i}/{len(release_notes)} - {pr_data['title']}")
        print("="*80)
        print(f"Repository: {owner}/{repo}")
        print(f"Branch: {branch}")
        print(f"PR URL: {note_data['url']}")
        print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Style: {style}")
        print("="*80)
        print(note_data['release_notes'])
        
        if i < len(release_notes):
            print("\n" + "-"*80)


def main():
    """Main function."""
    load_dotenv()
    
    try:
        # Get user input
        owner, repo, branch, start_date, end_date, style, combined, verbose = get_branch_input()
        
        # Initialize clients
        github_client = GitHubClient()
        ai_client = get_ai_client()
        
        # Initialize JIRA client if configured
        jira_client = None
        if all(os.getenv(key) for key in ['JIRA_SERVER', 'JIRA_USERNAME', 'JIRA_API_TOKEN']):
            jira_client = JiraClient()
            if not jira_client.is_configured():
                jira_client = None
        
        # Search for PRs
        prs_data = search_merged_prs(github_client, owner, repo, branch, start_date, end_date, verbose)
        
        if not prs_data:
            print(f"\n❌ No merged PRs found for the specified criteria")
            return
        
        # Enrich with JIRA data if available
        if jira_client:
            print("\n🎯 Enriching PR data with JIRA ticket information...")
            for pr_info in prs_data:
                try:
                    jira_client.enrich_pr_data_with_jira(pr_info['pr_data'])
                except Exception as e:
                    if verbose:
                        print(f"⚠️  JIRA enrichment failed for {pr_info['url']}: {str(e)}")
        
        # Generate release notes
        release_notes, stats = generate_branch_release_notes(
            ai_client, prs_data, branch, style, combined, verbose
        )
        
        if release_notes:
            # Display results
            display_branch_release_notes(
                release_notes, prs_data, owner, repo, branch, 
                start_date, end_date, style, combined, stats
            )
            print(f"\n✅ Branch release notes generated successfully!")
        else:
            print("\n❌ Failed to generate release notes")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
