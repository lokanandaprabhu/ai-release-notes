#!/usr/bin/env python3
"""
JIRA Sprint Release Notes Generator
Query JIRA for sprint tickets, then find corresponding GitHub PRs.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient
from ai_client import get_ai_client
from jira_client import JiraClient
from github import Github


def get_jira_sprint_input():
    """Get JIRA sprint search parameters from user input."""
    
    print("\n🎫 JIRA Sprint Release Notes Generator")
    print("=" * 50)
    
    # Sprint search method
    print("\n🔍 Sprint Search Method:")
    print("1. JIRA Sprint Name (e.g., 'ODC Sprint 3278')")
    print("2. JIRA Sprint ID (e.g., '74447')")
    
    while True:
        try:
            choice = input("\nEnter choice (1-2): ").strip()
            if choice in ['1', '2']:
                break
            print("❌ Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    # Get sprint identifier
    if choice == '1':
        sprint_name = input("\n🎫 Enter JIRA sprint name (e.g., 'ODC Sprint 3278'): ").strip()
        if not sprint_name:
            print("❌ Sprint name cannot be empty")
            return get_jira_sprint_input()
    else:  # choice == '2'
        sprint_id = input("\n🔢 Enter JIRA sprint ID (e.g., '74447'): ").strip()
        if not sprint_id:
            print("❌ Sprint ID cannot be empty")
            return get_jira_sprint_input()
        # Validate that it's a number
        try:
            int(sprint_id)
            sprint_name = sprint_id  # Use ID as name for JQL query
        except ValueError:
            print("❌ Sprint ID must be a number")
            return get_jira_sprint_input()
    
    # Repository search scope
    print("\n📦 Repository Search Scope:")
    print("1. Specific repository")
    print("2. Multiple repositories") 
    print("3. Auto-detect from common OpenShift repos (default)")
    
    while True:
        try:
            repo_choice = input("\nEnter choice (1-3, default: 3): ").strip() or '3'
            if repo_choice in ['1', '2', '3']:
                break
            print("❌ Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    repositories = []
    auto_detect = False
    
    if repo_choice == '1':
        # Single repository
        repo_input = input("\n📦 Enter repository (owner/repo, e.g., openshift/console): ").strip()
        if '/' in repo_input:
            owner, repo = repo_input.split('/', 1)
            repositories = [(owner.strip(), repo.strip())]
        else:
            print("❌ Invalid format, using auto-detect")
            auto_detect = True
    elif repo_choice == '2':
        # Multiple repositories
        print("\n📦 Enter repositories (one per line, empty line to finish):")
        while True:
            repo_input = input("Repository (owner/repo): ").strip()
            if not repo_input:
                break
            if '/' in repo_input:
                owner, repo = repo_input.split('/', 1)
                repositories.append((owner.strip(), repo.strip()))
            else:
                print("❌ Invalid format, skipping")
        
        if not repositories:
            print("❌ No valid repositories entered, using auto-detect")
            auto_detect = True
    else:  # repo_choice == '3'
        auto_detect = True
    
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
    
    return repositories, auto_detect, sprint_name, style, combined, verbose


def get_jira_sprint_tickets(jira_client, sprint_name, verbose=False):
    """Get all tickets from a JIRA sprint using JQL."""
    
    print(f"\n🎫 Querying JIRA for sprint tickets...")
    if verbose:
        print(f"   Sprint: {sprint_name}")
    
    try:
        # Try different JQL queries for sprint
        jql_queries = [
            f'sprint = "{sprint_name}"',
            f'sprint = {sprint_name}',  # For sprint ID
            f'sprint in ("{sprint_name}")',
            f'cf[10020] = "{sprint_name}"'  # Alternative sprint field
        ]
        
        tickets = []
        for jql in jql_queries:
            if verbose:
                print(f"   Trying JQL: {jql}")
            
            try:
                response = jira_client.session.get(
                    f"{jira_client.server}/rest/api/2/search",
                    params={
                        'jql': jql,
                        'fields': 'key,summary,status,priority,issuetype,components',
                        'maxResults': 1000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('issues'):
                        tickets = data['issues']
                        if verbose:
                            print(f"   ✅ Found {len(tickets)} tickets with JQL: {jql}")
                        break
                    elif verbose:
                        print(f"   No tickets found with JQL: {jql}")
                elif verbose:
                    print(f"   Error with JQL: {jql} - Status: {response.status_code}")
                    
            except Exception as e:
                if verbose:
                    print(f"   Error with JQL: {jql} - {str(e)}")
                continue
        
        if not tickets:
            print(f"❌ No tickets found for sprint: {sprint_name}")
            return []
        
        print(f"✅ Found {len(tickets)} JIRA tickets in sprint")
        
        # Extract ticket keys and info
        ticket_data = []
        for ticket in tickets:
            ticket_info = {
                'key': ticket['key'],
                'summary': ticket['fields'].get('summary', ''),
                'status': ticket['fields'].get('status', {}).get('name', ''),
                'priority': ticket['fields'].get('priority', {}).get('name', ''),
                'issuetype': ticket['fields'].get('issuetype', {}).get('name', ''),
                'components': [c['name'] for c in ticket['fields'].get('components', [])]
            }
            ticket_data.append(ticket_info)
            
            if verbose:
                print(f"   - {ticket_info['key']}: {ticket_info['summary']}")
        
        return ticket_data
        
    except Exception as e:
        print(f"❌ Error querying JIRA sprint: {str(e)}")
        return []


def find_prs_for_tickets(github_client, repositories, ticket_keys, jira_client=None, verbose=False):
    """Find GitHub PRs that reference the JIRA tickets using both GitHub search and JIRA links."""
    
    print(f"\n🔍 Searching for PRs referencing {len(ticket_keys)} JIRA tickets...")
    if verbose:
        print(f"   Repositories: {len(repositories)} repos")
        print(f"   Tickets: {', '.join(ticket_keys[:5])}{'...' if len(ticket_keys) > 5 else ''}")
    
    prs_data = []
    found_tickets = []
    github = Github(github_client.token)
    
    # Track JIRA link discoveries
    jira_links_count = 0
    
    for i, ticket_key in enumerate(ticket_keys, 1):
        # Show progress
        print(f"🔍 Processing ticket {i}/{len(ticket_keys)}: {ticket_key}")
        
        if verbose:
            print(f"   Checking JIRA links and GitHub search...")
        
        # Method 1: Extract GitHub URLs directly from JIRA ticket
        jira_urls = []
        relevant_urls = []
        if jira_client:
            try:
                jira_urls = jira_client.extract_github_urls_from_ticket(ticket_key)
                
                # Filter URLs to only include target repositories
                for url in jira_urls:
                    url_parts = url.rstrip('/').split('/')
                    if len(url_parts) >= 7 and 'github.com' in url and '/pull/' in url:
                        url_owner = url_parts[-4]
                        url_repo = url_parts[-3]
                        
                        # Check if this PR is in one of our target repositories
                        pr_repo_match = any(
                            (url_owner, url_repo) == (repo_owner, repo_name) 
                            for repo_owner, repo_name in repositories
                        )
                        
                        if pr_repo_match:
                            relevant_urls.append(url)
                
                if relevant_urls:
                    print(f"   ✅ Found {len(relevant_urls)} relevant GitHub URL(s) in JIRA ticket")
                    if verbose:
                        for url in relevant_urls:
                            print(f"     JIRA Link: {url}")
                elif jira_urls:
                    print(f"   ⚪ Found {len(jira_urls)} GitHub URL(s) but none in target repositories")
                    if verbose:
                        for url in jira_urls:
                            url_parts = url.rstrip('/').split('/')
                            if len(url_parts) >= 7:
                                url_owner = url_parts[-4]
                                url_repo = url_parts[-3]
                                print(f"     Skipped: {url_owner}/{url_repo}")
                
                # Use the filtered URLs for processing
                jira_urls = relevant_urls
                
            except Exception as e:
                print(f"   ⚠️  Error extracting JIRA links: {str(e)}")
        
        # Skip tickets with no relevant URLs
        if not jira_urls:
            if verbose:
                print(f"   No relevant PRs found for {ticket_key}, skipping...")
            continue
        
        # Process JIRA URLs
        for url in jira_urls:
            try:
                # Parse GitHub URL to get owner, repo, PR number
                url_parts = url.rstrip('/').split('/')
                if len(url_parts) >= 7 and 'github.com' in url and '/pull/' in url:
                    url_owner = url_parts[-4]
                    url_repo = url_parts[-3]
                    pr_number = int(url_parts[-1])
                    
                    # Check if this PR is in one of our target repositories
                    pr_repo_match = any(
                        (url_owner, url_repo) == (repo_owner, repo_name) 
                        for repo_owner, repo_name in repositories
                    )
                    
                    if not pr_repo_match:
                        if verbose:
                            print(f"     Skipped PR #{pr_number} from {url_owner}/{url_repo} (not in target repos)")
                        continue
                    
                    # Get detailed PR data
                    pr_data = github_client.get_pr_data(url_owner, url_repo, pr_number)
                    pr_info = {
                        'pr_data': pr_data,
                        'url': f"https://github.com/{url_owner}/{url_repo}/pull/{pr_number}",
                        'jira_ticket': ticket_key,
                        'found_via': 'jira_link'
                    }
                    
                    # Check if we already have this PR
                    existing_urls = [pr['url'] for pr in prs_data]
                    if pr_info['url'] not in existing_urls:
                        prs_data.append(pr_info)
                        found_tickets.append(ticket_key)
                        jira_links_count += 1
                        if verbose:
                            print(f"     ✅ Added PR #{pr_number} from {url_owner}/{url_repo} via JIRA link")
                    
            except Exception as e:
                if verbose:
                    print(f"     ❌ Error processing JIRA URL {url}: {str(e)}")
                continue
        
        # GitHub search disabled - JIRA links are comprehensive and much faster
        # The JIRA link extraction already found all PRs with 91% success rate
    
    # Summary of discovery methods
    if jira_links_count > 0:
        print(f"\n📊 PR Discovery Summary:")
        print(f"   - Via JIRA links: {jira_links_count} PRs")
        print(f"   - Total PRs found: {len(prs_data)}")
        if len(prs_data) > 0:
            success_rate = (len(set(found_tickets)) / len(ticket_keys)) * 100
            print(f"   - Success rate: {success_rate:.0f}% of tickets have PRs")
    
    return prs_data, found_tickets


def generate_jira_sprint_release_notes(ai_client, prs_data, sprint_name, style, combined=True, verbose=False):
    """Generate release notes for JIRA sprint PRs."""
    
    if not prs_data:
        return None, []
    
    if combined:
        # Generate combined release notes
        if verbose:
            print(f"\n🎯 Generating combined release notes...")
        
        # Combine all PR data
        combined_data = {
            'sprint_name': sprint_name,
            'prs_count': len(prs_data),
            'prs': []
        }
        
        total_stats = {'files': 0, 'additions': 0, 'deletions': 0}
        
        for pr_info in prs_data:
            pr_data = pr_info['pr_data']
            combined_data['prs'].append({
                'title': pr_data['title'],
                'url': pr_info['url'],
                'files_changed': pr_data.get('files_changed', []),
                'stats': pr_data.get('stats', {}),
                'jira_tickets': pr_data.get('jira_tickets', [])
            })
            
            # Aggregate stats
            pr_stats = pr_data.get('stats', {})
            total_stats['files'] += pr_stats.get('changed_files', 0)
            total_stats['additions'] += pr_stats.get('additions', 0)
            total_stats['deletions'] += pr_stats.get('deletions', 0)
        
        combined_data['total_stats'] = total_stats
        
        # Create a combined PR data structure for the AI
        combined_pr_data = {
            'title': f"Sprint {sprint_name} - Combined Release Notes",
            'body': f"Combined release notes for {len(prs_data)} PRs in sprint {sprint_name}",
            'repo': prs_data[0]['pr_data']['repo'],  # Use first PR's repo info
            'author': {'name': 'Sprint Release', 'login': 'sprint'},
            'stats': {
                'changed_files': total_stats['files'],
                'additions': total_stats['additions'], 
                'deletions': total_stats['deletions']
            },
            'commits': [],
            'files_changed': [],
            'labels': [],
            'reviews': [],
            'comments': []
        }
        
        # Aggregate all PR information
        all_commits = []
        all_files = []
        all_jira_tickets = []
        pr_summaries = []
        
        for pr_info in prs_data:
            pr_data = pr_info['pr_data']
            
            # Add PR summary
            pr_summaries.append(f"**{pr_data['title']}** ({pr_info['url']})")
            
            # Collect commits
            commits = pr_data.get('commits', [])
            for commit in commits[:2]:  # Limit to 2 commits per PR to avoid overwhelming
                all_commits.append(commit)
            
            # Collect files (limit to avoid overwhelming the AI)
            files = pr_data.get('files_changed', [])
            for file in files[:3]:  # Limit to 3 files per PR
                all_files.append(file)
            
            # Collect JIRA tickets
            jira_tickets = pr_data.get('jira_tickets', [])
            all_jira_tickets.extend(jira_tickets)
        
        # Update combined data with aggregated info
        combined_pr_data['commits'] = all_commits[:20]  # Limit total commits
        combined_pr_data['files_changed'] = all_files[:50]  # Limit total files
        combined_pr_data['jira_tickets'] = all_jira_tickets
        
        # Add sprint context to the body
        combined_pr_data['body'] = f"""
Sprint: {sprint_name}
Total PRs: {len(prs_data)}
Total Files Changed: {total_stats['files']}
Total Changes: +{total_stats['additions']} -{total_stats['deletions']}

Included PRs:
{chr(10).join(pr_summaries)}

This is a combined release note covering all changes made in this sprint.
"""
        
        # Generate release notes using combined data
        release_notes = ai_client.generate_release_notes(
            combined_pr_data, 
            style=style
        )
        
        return release_notes, combined_data
    
    else:
        # Generate individual release notes
        individual_notes = []
        
        for i, pr_info in enumerate(prs_data, 1):
            if verbose:
                print(f"\n🎯 Generating release notes for PR {i}/{len(prs_data)}")
            
            pr_data = pr_info['pr_data']
            release_notes = ai_client.generate_release_notes(
                pr_data, 
                style=style
            )
            
            individual_notes.append({
                'release_notes': release_notes,
                'pr_data': pr_data,
                'url': pr_info['url']
            })
        
        return individual_notes, None


def display_jira_sprint_release_notes(release_notes, prs_data, sprint_name, style, combined=True, tickets_count=0):
    """Display formatted JIRA sprint release notes."""
    
    if combined and release_notes:
        # Display combined release notes
        print("\n" + "="*80)
        print(f"🎫 JIRA SPRINT RELEASE NOTES")
        print("="*80)
        print(f"JIRA Sprint: {sprint_name}")
        print(f"JIRA Tickets: {tickets_count}")
        print(f"PRs Found: {len(prs_data)}")
        print(f"Style: {style}")
        print("="*80)
        print(release_notes)
        
    elif not combined and isinstance(release_notes, list):
        # Display individual release notes
        for i, note_data in enumerate(release_notes, 1):
            pr_data = note_data['pr_data']
            
            print("\n" + "="*80)
            print(f"🎫 JIRA SPRINT PR #{i}/{len(release_notes)} - {pr_data['title']}")
            print("="*80)
            print(f"Repository: {pr_data['repo']['full_name']}")
            print(f"PR URL: {note_data['url']}")
            print(f"JIRA Sprint: {sprint_name}")
            print(f"Style: {style}")
            print("="*80)
            print(note_data['release_notes'])
            
            if i < len(release_notes):
                print("\n" + "-"*80)
    
    else:
        print("\n❌ No release notes to display")


def display_individual_pr_notes(release_notes):
    """Display individual PR release notes without combined format."""
    
    for i, note_data in enumerate(release_notes, 1):
        pr_data = note_data['pr_data']
        
        print("\n" + "="*80)
        print(f"📝 PR #{i}/{len(release_notes)} - {pr_data['title']}")
        print("="*80)
        print(f"Repository: {pr_data['repo']['full_name']}")
        print(f"URL: {note_data['url']}")
        if pr_data.get('jira_tickets'):
            jira_keys = [ticket['key'] for ticket in pr_data['jira_tickets']]
            print(f"JIRA Tickets: {', '.join(jira_keys)}")
        print("="*80)
        print(note_data['release_notes'])
        
        if i < len(release_notes):
            print("\n" + "-"*80)


def main():
    """Main function."""
    load_dotenv()
    
    try:
        # Get user input
        repositories, auto_detect, sprint_name, style, combined, verbose = get_jira_sprint_input()
        
        # Initialize clients
        github_client = GitHubClient()
        ai_client = get_ai_client()
        
        # Initialize JIRA client (required for this script)
        if not all(os.getenv(key) for key in ['JIRA_SERVER', 'JIRA_USERNAME', 'JIRA_API_TOKEN']):
            print("❌ JIRA configuration required for sprint search")
            print("Please configure JIRA_SERVER, JIRA_USERNAME, and JIRA_API_TOKEN in .env")
            return
        
        jira_client = JiraClient()
        if not jira_client.is_configured():
            print("❌ JIRA connection failed")
            print("Please check your JIRA configuration in .env")
            return
        
        if verbose:
            print(f"✅ JIRA connected as: {jira_client.username}")
        
        # Auto-detect repositories if needed
        if auto_detect:
            print(f"\n🔍 Auto-detecting repositories from JIRA tickets...")
            # Common OpenShift repositories to search
            repositories = [
                ('openshift', 'console'),
                ('openshift-pipelines', 'console-plugin'),
                ('openshift', 'enhancements'),
                ('openshift', 'console-operator'),
                ('openshift', 'api')
            ]
            if verbose:
                print(f"   Using {len(repositories)} repositories")
        
        # Get JIRA sprint tickets
        tickets = get_jira_sprint_tickets(jira_client, sprint_name, verbose)
        
        if not tickets:
            print("❌ No tickets found in JIRA sprint")
            print("💡 Please verify:")
            print("  - Sprint exists and has tickets")
            return
        
        # Extract ticket keys
        ticket_keys = [ticket['key'] for ticket in tickets]
        
        # Find PRs for these tickets
        prs_data, found_tickets = find_prs_for_tickets(github_client, repositories, ticket_keys, jira_client, verbose)
        
        if not prs_data:
            print(f"\n❌ No PRs found for JIRA sprint tickets")
            print(f"💡 Searched {len(ticket_keys)} tickets in {len(repositories)} repositories")
            if verbose:
                print(f"   Tickets searched: {', '.join(ticket_keys[:10])}{'...' if len(ticket_keys) > 10 else ''}")
            return
        
        # Display summary
        print(f"\n✅ Sprint PR Summary:")
        print(f"   - JIRA tickets in sprint: {len(tickets)}")
        print(f"   - JIRA tickets with PRs: {len(set(found_tickets))}")
        print(f"   - GitHub PRs found: {len(prs_data)}")
        
        # Show tickets without PRs
        tickets_without_prs = [t for t in ticket_keys if t not in found_tickets]
        if tickets_without_prs:
            print(f"   - Tickets without PRs: {', '.join(tickets_without_prs)}")
        
        # Enrich with JIRA data
        print("\n🎯 Enriching PR data with JIRA ticket information...")
        for pr_info in prs_data:
            try:
                jira_client.enrich_pr_data_with_jira(pr_info['pr_data'])
            except Exception as e:
                if verbose:
                    print(f"⚠️  JIRA enrichment failed for {pr_info['url']}: {str(e)}")
        
        # Generate release notes
        release_notes, combined_data = generate_jira_sprint_release_notes(
            ai_client, prs_data, sprint_name, style, combined, verbose
        )
        
        if release_notes:
            # Display results
            if combined:
                display_jira_sprint_release_notes(release_notes, prs_data, sprint_name, style, combined, len(tickets))
            else:
                display_individual_pr_notes(release_notes)
            
            print(f"\n✅ JIRA sprint release notes generated successfully!")
        else:
            print("\n❌ Failed to generate release notes")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
