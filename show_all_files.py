#!/usr/bin/env python3
"""
Show All Files in PR
Utility script to display all files changed in a pull request.
"""

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient


def get_pr_input():
    """Get PR URL from user input."""
    
    print("\n📁 Show All Files in PR")
    print("=" * 30)
    
    # Get PR URL
    while True:
        try:
            pr_url = input("\n🔗 Enter PR URL: ").strip()
            if pr_url:
                break
            print("❌ Please enter a PR URL")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    return pr_url


def show_files(github_client, pr_url):
    """Fetch and display all files in the PR."""
    
    try:
        print(f"\n📥 Fetching PR data...")
        
        # Parse PR URL and get data
        pr_data = github_client.get_pr_data_from_url(pr_url)
        
        print(f"✅ Found PR #{pr_data['number']}: {pr_data['title']}")
        print(f"Repository: {pr_data['repo']['full_name']}")
        
        # Get files
        files = pr_data.get('files_changed', [])
        stats = pr_data.get('stats', {})
        
        print(f"\n📊 Statistics:")
        print(f"   Files changed: {stats.get('changed_files', len(files))}")
        print(f"   Additions: +{stats.get('additions', 0)}")
        print(f"   Deletions: -{stats.get('deletions', 0)}")
        
        if not files:
            print("\n❌ No files found in this PR")
            return
        
        print(f"\n📁 Files Changed ({len(files)}):")
        print("=" * 60)
        
        # Group files by directory for better organization
        file_groups = {}
        for file in files:
            filename = file['filename']
            directory = '/'.join(filename.split('/')[:-1]) if '/' in filename else '.'
            
            if directory not in file_groups:
                file_groups[directory] = []
            file_groups[directory].append(file)
        
        # Display files grouped by directory
        for directory in sorted(file_groups.keys()):
            files_in_dir = file_groups[directory]
            
            print(f"\n📂 {directory}/")
            for file in sorted(files_in_dir, key=lambda x: x['filename']):
                filename = file['filename'].split('/')[-1]  # Just the filename
                additions = file.get('additions', 0)
                deletions = file.get('deletions', 0)
                status = file.get('status', 'modified')
                
                # Status indicator
                status_icon = {
                    'added': '🟢',
                    'modified': '🔵', 
                    'removed': '🔴',
                    'renamed': '🟡'
                }.get(status, '⚪')
                
                print(f"   {status_icon} {filename} (+{additions}/-{deletions}) [{status}]")
        
        print("\n" + "=" * 60)
        print(f"Total: {len(files)} files changed")
        
    except Exception as e:
        print(f"❌ Error fetching PR files: {str(e)}")


def main():
    """Main function."""
    load_dotenv()
    
    try:
        # Check if PR URL was provided as command line argument
        if len(sys.argv) > 1:
            pr_url = sys.argv[1]
        else:
            # Get PR URL from user input
            pr_url = get_pr_input()
        
        # Initialize GitHub client
        github_client = GitHubClient()
        
        # Show files
        show_files(github_client, pr_url)
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
