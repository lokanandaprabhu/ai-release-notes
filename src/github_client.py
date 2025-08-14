"""GitHub API client for fetching pull request data."""

import os
import requests
from typing import Dict, List, Optional
from github import Github, PullRequest


class GitHubClient:
    """Client for interacting with GitHub API to fetch PR data."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with optional token."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.github = Github(self.token) if self.token else Github()
        
    def parse_pr_url(self, pr_url: str) -> tuple[str, str, int]:
        """Parse GitHub PR URL to extract owner, repo, and PR number."""
        # Handle different URL formats:
        # https://github.com/owner/repo/pull/123
        # https://github.com/owner/repo/pulls/123
        parts = pr_url.strip('/').split('/')
        
        if 'github.com' not in pr_url:
            raise ValueError("Invalid GitHub URL")
            
        try:
            github_index = parts.index('github.com')
            owner = parts[github_index + 1]
            repo = parts[github_index + 2]
            pr_number = int(parts[-1])
            return owner, repo, pr_number
        except (ValueError, IndexError):
            raise ValueError("Could not parse GitHub PR URL")
    
    def get_pr_data_from_url(self, pr_url: str) -> Dict:
        """Parse PR URL and fetch comprehensive PR data."""
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        return self.get_pr_data(owner, repo, pr_number)
    
    def get_pr_data(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Fetch comprehensive PR data from GitHub API."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            # Get commits and files changed
            commits = list(pr.get_commits())
            files = list(pr.get_files())
            
            # Get reviews and comments
            reviews = list(pr.get_reviews())
            comments = list(pr.get_issue_comments())
            review_comments = list(pr.get_review_comments())
            
            return {
                'title': pr.title,
                'number': pr.number,
                'body': pr.body or '',
                'state': pr.state,
                'merged': pr.merged,
                'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                'created_at': pr.created_at.isoformat(),
                'updated_at': pr.updated_at.isoformat(),
                'author': {
                    'login': pr.user.login,
                    'name': pr.user.name or pr.user.login
                },
                'base_branch': pr.base.ref,
                'head_branch': pr.head.ref,
                'labels': [label.name for label in pr.labels],
                'milestone': pr.milestone.title if pr.milestone else None,
                'commits': [
                    {
                        'sha': commit.sha,
                        'message': commit.commit.message,
                        'author': commit.commit.author.name,
                        'date': commit.commit.author.date.isoformat()
                    }
                    for commit in commits
                ],
                'files_changed': [
                    {
                        'filename': file.filename,
                        'status': file.status,
                        'additions': file.additions,
                        'deletions': file.deletions,
                        'changes': file.changes,
                        'patch': file.patch if hasattr(file, 'patch') else None
                    }
                    for file in files
                ],
                'stats': {
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                    'changed_files': pr.changed_files,
                    'commits': len(commits)
                },
                'reviews': [
                    {
                        'user': review.user.login,
                        'state': review.state,
                        'body': review.body or '',
                        'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None
                    }
                    for review in reviews
                ],
                'comments_count': len(comments) + len(review_comments),
                'url': pr.html_url,
                'repo': {
                    'name': repository.name,
                    'full_name': repository.full_name,
                    'description': repository.description
                }
            }
            
        except Exception as e:
            raise Exception(f"Error fetching PR data: {str(e)}")
    
    def get_pr_from_url(self, pr_url: str) -> Dict:
        """Get PR data from a GitHub PR URL."""
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        return self.get_pr_data(owner, repo, pr_number)
