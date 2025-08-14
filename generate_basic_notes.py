#!/usr/bin/env python3
"""
Basic AI Release Notes Generator
Simple script for generating release notes with minimal setup.
"""

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_client import GitHubClient
from ai_client import get_ai_client


def get_basic_input():
    """Get basic PR URL and options from user input."""
    
    print("\n⚡ Basic AI Release Notes Generator")
    print("=" * 50)
    
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
    
    # Simple style selection
    print("\n🎨 Choose style:")
    print("1. Standard (default)")
    print("2. Brief")
    print("3. Technical")
    
    while True:
        try:
            style_choice = input("Enter choice (1-3, default: 1): ").strip() or '1'
            if style_choice in ['1', '2', '3']:
                break
            print("❌ Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    # Map choice to style
    style_map = {'1': 'standard', '2': 'brief', '3': 'technical'}
    style = style_map[style_choice]
    
    return pr_url, style


def process_pr(github_client, pr_url, style):
    """Process PR and generate release notes."""
    
    try:
        print(f"\n📥 Fetching PR data...")
        
        # Parse PR URL and get data
        pr_data = github_client.get_pr_data_from_url(pr_url)
        
        print(f"✅ Found PR #{pr_data['number']}: {pr_data['title']}")
        
        # Show basic stats
        stats = pr_data.get('stats', {})
        files_count = stats.get('changed_files', 0)
        print(f"📊 Files changed: {files_count}")
        
        return pr_data
        
    except Exception as e:
        print(f"❌ Error processing PR: {str(e)}")
        return None


def display_basic_release_notes(pr_data, release_notes, style):
    """Display formatted basic release notes."""
    
    print("\n" + "="*60)
    print(f"📝 BASIC RELEASE NOTES")
    print("="*60)
    print(f"PR: #{pr_data['number']} - {pr_data['title']}")
    print(f"Repository: {pr_data['repo']['full_name']}")
    print(f"Style: {style}")
    print("="*60)
    print(release_notes)
    print("="*60)


def main():
    """Main function."""
    load_dotenv()
    
    try:
        # Get user input
        pr_url, style = get_basic_input()
        
        # Initialize clients (basic setup)
        github_client = GitHubClient()
        ai_client = get_ai_client()
        
        # Process PR
        pr_data = process_pr(github_client, pr_url, style)
        if not pr_data:
            return
        
        # Generate release notes
        print(f"\n🎯 Generating {style} release notes...")
        release_notes = ai_client.generate_release_notes(pr_data, style=style)
        
        if release_notes:
            display_basic_release_notes(pr_data, release_notes, style)
            print(f"\n✅ Basic release notes generated successfully!")
        else:
            print("\n❌ Failed to generate release notes")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
