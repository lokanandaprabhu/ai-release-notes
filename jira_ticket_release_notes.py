#!/usr/bin/env python3
"""
JIRA Ticket Release Notes Generator
Generate release notes from JIRA ticket(s) with optional GitHub PR enhancement.
"""

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient
from ai_client import get_ai_client
from jira_client import JiraClient


def get_jira_ticket_input():
    """Get JIRA ticket IDs and options from user input."""
    
    print("\n🎫 JIRA Ticket Release Notes Generator")
    print("=" * 50)
    
    # Get JIRA ticket IDs
    print("\n📝 Enter JIRA ticket ID(s):")
    print("• Single ticket: ODC-7806")
    print("• Multiple tickets: ODC-7806, SRVKP-8210, OCPBUGS-59564")
    
    while True:
        try:
            ticket_input = input("\n🎫 JIRA ticket ID(s): ").strip()
            if ticket_input:
                break
            print("❌ Please enter at least one JIRA ticket ID")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    # Parse ticket IDs
    ticket_ids = [ticket.strip().upper() for ticket in ticket_input.split(',') if ticket.strip()]
    
    # Validate ticket format
    valid_tickets = []
    for ticket in ticket_ids:
        if '-' in ticket and len(ticket.split('-')) == 2:
            project, number = ticket.split('-')
            if project.isalpha() and number.isdigit():
                valid_tickets.append(ticket)
            else:
                print(f"⚠️  Skipping invalid ticket format: {ticket}")
        else:
            print(f"⚠️  Skipping invalid ticket format: {ticket}")
    
    if not valid_tickets:
        print("❌ No valid JIRA tickets provided")
        return get_jira_ticket_input()
    
    ticket_ids = valid_tickets
    
    # Style selection
    styles = ['standard', 'brief', 'marketing', 'technical', 'changelog']
    print(f"\n🎨 Available styles: {', '.join(styles)}")
    style = input("📋 Select style (default: standard): ").strip().lower() or 'standard'
    if style not in styles:
        print(f"⚠️  Unknown style '{style}', using 'standard'")
        style = 'standard'
    
    # Combined or individual (only for multiple tickets)
    combined = True
    if len(ticket_ids) > 1:
        print("\n📄 Output Format:")
        print("1. Combined release notes (all tickets together)")
        print("2. Individual release notes (separate for each ticket)")
        
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
    
    return ticket_ids, style, combined, verbose


def process_jira_ticket(jira_client, github_client, ticket_id, verbose=False):
    """Process a single JIRA ticket and find related PR if available."""
    
    try:
        print(f"\n📥 Fetching JIRA ticket: {ticket_id}")
        
        # Get JIRA ticket info
        jira_data = jira_client.get_jira_ticket_info(ticket_id)
        if not jira_data:
            print(f"❌ Could not fetch JIRA ticket {ticket_id}")
            return None
        
        print(f"✅ Found JIRA ticket: {jira_data['summary']}")
        print(f"📊 Status: {jira_data['status']} | Priority: {jira_data['priority']} | Type: {jira_data['issue_type']}")
        
        # Look for GitHub PR links
        github_urls = jira_client.extract_github_urls_from_ticket(ticket_id)
        pr_data = None
        
        if github_urls:
            print(f"🔗 Found {len(github_urls)} GitHub URL(s) in JIRA ticket")
            
            for url in github_urls:
                if verbose:
                    print(f"   Checking: {url}")
                
                try:
                    # Try to get PR data from the URL
                    pr_data = github_client.get_pr_data_from_url(url)
                    print(f"✅ Found linked PR #{pr_data['number']}: {pr_data['title']}")
                    
                    # Enrich PR data with JIRA info
                    pr_data['jira_tickets'] = [jira_data]
                    
                    # Show PR stats
                    stats = pr_data.get('stats', {})
                    files_count = stats.get('changed_files', 0)
                    additions = stats.get('additions', 0)
                    deletions = stats.get('deletions', 0)
                    print(f"📊 PR Stats: {files_count} files, +{additions}/-{deletions}")
                    
                    break  # Use first valid PR found
                    
                except Exception as e:
                    if verbose:
                        print(f"   ❌ Error fetching PR from {url}: {str(e)}")
                    continue
        
        if not pr_data:
            print("📝 No GitHub PR found, will generate notes from JIRA ticket only")
        
        return {
            'ticket_id': ticket_id,
            'jira_data': jira_data,
            'pr_data': pr_data,
            'has_pr': pr_data is not None
        }
        
    except Exception as e:
        print(f"❌ Error processing JIRA ticket {ticket_id}: {str(e)}")
        return None


def create_ticket_data_for_ai(ticket_info):
    """Create a data structure suitable for AI processing."""
    
    jira_data = ticket_info['jira_data']
    pr_data = ticket_info['pr_data']
    
    if pr_data:
        # Use PR data as base and enhance with JIRA
        ai_data = pr_data.copy()
        # Ensure JIRA data is included
        ai_data['jira_tickets'] = [jira_data]
    else:
        # Create AI data structure from JIRA ticket only
        ai_data = {
            'title': f"{jira_data['key']}: {jira_data['summary']}",
            'body': jira_data['description'],
            'repo': {'full_name': 'JIRA Ticket', 'name': 'ticket'},
            'author': {'name': jira_data['reporter'], 'login': jira_data['assignee']},
            'number': jira_data['key'],
            'state': jira_data['status'].lower(),
            'stats': {'changed_files': 0, 'additions': 0, 'deletions': 0},
            'commits': [],
            'files_changed': [],
            'labels': jira_data['labels'],
            'reviews': [],
            'comments': [],
            'jira_tickets': [jira_data]
        }
    
    return ai_data


def generate_combined_ticket_notes(ai_client, ticket_infos, style, verbose=False):
    """Generate combined release notes for multiple tickets."""
    
    if not ticket_infos:
        return None
    
    if len(ticket_infos) == 1:
        # Single ticket - use normal generation
        ai_data = create_ticket_data_for_ai(ticket_infos[0])
        return ai_client.generate_release_notes(ai_data, style=style)
    
    print(f"\n🎯 Generating combined release notes for {len(ticket_infos)} tickets...")
    
    # Create combined data structure
    ticket_summaries = []
    all_jira_tickets = []
    pr_count = 0
    total_stats = {'files': 0, 'additions': 0, 'deletions': 0}
    
    for ticket_info in ticket_infos:
        jira_data = ticket_info['jira_data']
        pr_data = ticket_info['pr_data']
        
        # Add ticket summary
        status_icon = "🔗" if ticket_info['has_pr'] else "📝"
        ticket_summaries.append(f"{status_icon} **{jira_data['key']}**: {jira_data['summary']}")
        
        # Collect JIRA data
        all_jira_tickets.append(jira_data)
        
        # Aggregate PR stats if available
        if pr_data:
            pr_count += 1
            stats = pr_data.get('stats', {})
            total_stats['files'] += stats.get('changed_files', 0)
            total_stats['additions'] += stats.get('additions', 0)
            total_stats['deletions'] += stats.get('deletions', 0)
    
    # Create combined AI data structure
    combined_ai_data = {
        'title': f"Combined Release Notes - {len(ticket_infos)} JIRA Tickets",
        'body': f"""
Combined release notes for {len(ticket_infos)} JIRA tickets.

Included Tickets:
{chr(10).join(ticket_summaries)}

Summary:
- Total JIRA tickets: {len(ticket_infos)}
- Tickets with PRs: {pr_count}
- Tickets without PRs: {len(ticket_infos) - pr_count}
""",
        'repo': {'full_name': 'JIRA Tickets', 'name': 'tickets'},
        'author': {'name': 'Combined Release', 'login': 'combined'},
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
    
    # Aggregate limited data from PRs
    all_commits = []
    all_files = []
    
    for ticket_info in ticket_infos:
        if ticket_info['pr_data']:
            pr_data = ticket_info['pr_data']
            commits = pr_data.get('commits', [])
            all_commits.extend(commits[:2])  # Max 2 commits per PR
            
            files = pr_data.get('files_changed', [])
            all_files.extend(files[:3])  # Max 3 files per PR
    
    combined_ai_data['commits'] = all_commits[:10]  # Max 10 total commits
    combined_ai_data['files_changed'] = all_files[:20]  # Max 20 total files
    
    # Generate release notes
    return ai_client.generate_release_notes(combined_ai_data, style=style)


def display_ticket_release_notes(ticket_info, release_notes, style):
    """Display formatted release notes for a single ticket."""
    
    jira_data = ticket_info['jira_data']
    pr_data = ticket_info['pr_data']
    
    print("\n" + "="*80)
    print(f"🎫 JIRA TICKET RELEASE NOTES")
    print("="*80)
    print(f"JIRA Ticket: {jira_data['key']} - {jira_data['summary']}")
    print(f"Status: {jira_data['status']} | Priority: {jira_data['priority']} | Type: {jira_data['issue_type']}")
    print(f"Assignee: {jira_data['assignee']}")
    
    if pr_data:
        print(f"🔗 Linked PR: #{pr_data['number']} - {pr_data['title']}")
        print(f"Repository: {pr_data['repo']['full_name']}")
    else:
        print("📝 Source: JIRA ticket only (no GitHub PR)")
    
    print(f"Style: {style}")
    print("="*80)
    print(release_notes)


def display_combined_ticket_notes(ticket_infos, release_notes, style):
    """Display formatted combined release notes."""
    
    pr_count = sum(1 for t in ticket_infos if t['has_pr'])
    
    print("\n" + "="*80)
    print(f"🎫 COMBINED JIRA TICKET RELEASE NOTES")
    print("="*80)
    print(f"JIRA Tickets: {len(ticket_infos)}")
    print(f"Tickets with PRs: {pr_count}")
    print(f"Tickets without PRs: {len(ticket_infos) - pr_count}")
    print(f"Style: {style}")
    print("="*80)
    print(release_notes)


def main():
    """Main function."""
    load_dotenv()
    
    try:
        # Get user input
        ticket_ids, style, combined, verbose = get_jira_ticket_input()
        
        # Initialize clients
        github_client = GitHubClient()
        ai_client = get_ai_client()
        
        # Initialize JIRA client (required)
        if not all(os.getenv(key) for key in ['JIRA_SERVER', 'JIRA_USERNAME', 'JIRA_API_TOKEN']):
            print("❌ JIRA configuration required for ticket processing")
            print("Please configure JIRA_SERVER, JIRA_USERNAME, and JIRA_API_TOKEN in .env")
            return
        
        jira_client = JiraClient()
        if not jira_client.is_configured():
            print("❌ JIRA connection failed")
            print("Please check your JIRA configuration in .env")
            return
        
        if verbose:
            print(f"✅ JIRA connected as: {jira_client.username}")
        
        # Process all tickets
        ticket_infos = []
        for i, ticket_id in enumerate(ticket_ids, 1):
            print(f"\n📝 Processing ticket {i}/{len(ticket_ids)}: {ticket_id}")
            
            ticket_info = process_jira_ticket(jira_client, github_client, ticket_id, verbose)
            if ticket_info:
                ticket_infos.append(ticket_info)
                
                # For individual mode, generate and display immediately
                if not combined:
                    print(f"\n🎯 Generating release notes for {ticket_id}...")
                    ai_data = create_ticket_data_for_ai(ticket_info)
                    release_notes = ai_client.generate_release_notes(ai_data, style=style)
                    display_ticket_release_notes(ticket_info, release_notes, style)
                    
                    if i < len(ticket_ids):
                        print("\n" + "-"*80)
        
        if not ticket_infos:
            print("\n❌ No tickets could be processed successfully")
            return
        
        # For combined mode, generate notes for all tickets together
        if combined:
            release_notes = generate_combined_ticket_notes(ai_client, ticket_infos, style, verbose)
            if release_notes:
                display_combined_ticket_notes(ticket_infos, release_notes, style)
            else:
                print("\n❌ Failed to generate combined release notes")
        
        # Summary
        pr_count = sum(1 for t in ticket_infos if t['has_pr'])
        print(f"\n✅ Successfully processed {len(ticket_infos)}/{len(ticket_ids)} tickets")
        print(f"   - With GitHub PRs: {pr_count}")
        print(f"   - JIRA only: {len(ticket_infos) - pr_count}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
