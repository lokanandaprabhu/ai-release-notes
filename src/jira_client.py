"""JIRA client for fetching ticket information to enhance release notes."""

import os
import re
import requests
from typing import Dict, List, Optional
from urllib.parse import urlparse
import base64


class JiraClient:
    """Client for interacting with JIRA API to fetch ticket information."""
    
    def __init__(self, server: Optional[str] = None, username: Optional[str] = None, api_token: Optional[str] = None):
        """Initialize JIRA client."""
        self.server = server or os.getenv('JIRA_SERVER')
        self.username = username or os.getenv('JIRA_USERNAME') 
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN')
        
        self.session = None
        if self.server and self.username and self.api_token:
            try:
                # Use direct REST API calls instead of the jira library
                self.session = requests.Session()
                
                # Set up Bearer token authentication (Red Hat JIRA style)
                self.session.headers.update({
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                
                # Set timeouts for faster responses
                self.session.timeout = 10
                
                # Test connection
                test_url = f"{self.server}/rest/api/2/myself"
                response = self.session.get(test_url)
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"✅ JIRA connected as: {user_info.get('displayName', self.username)}")
                else:
                    print(f"⚠️  JIRA connection test failed: {response.status_code}")
                    self.session = None
                    
            except Exception as e:
                print(f"⚠️  JIRA connection failed: {str(e)}")
                self.session = None
    
    def extract_jira_tickets(self, text: str) -> List[str]:
        """Extract JIRA ticket IDs from text (e.g., SRVKP-8209, ODC-7806)."""
        if not text:
            return []
        
        # Pattern to match JIRA tickets (PROJECT-NUMBER format)
        pattern = r'\b([A-Z]{2,10}-\d+)\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        # Filter out invalid/malformed ticket IDs
        valid_tickets = []
        for ticket in matches:
            # Skip tickets with very short project codes or very long numbers
            parts = ticket.split('-')
            if len(parts) == 2:
                project_code, number = parts
                # Valid project codes are typically 3-10 chars, numbers are 1-6 digits
                if (3 <= len(project_code) <= 10 and 
                    1 <= len(number) <= 6 and 
                    number.isdigit()):
                    valid_tickets.append(ticket.upper())
        
        return list(set(valid_tickets))  # Remove duplicates
    
    def get_jira_ticket_info(self, ticket_id: str) -> Optional[Dict]:
        """Fetch detailed information from a JIRA ticket."""
        if not self.session:
            return None
            
        try:
            url = f"{self.server}/rest/api/2/issue/{ticket_id}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                issue_data = response.json()
                fields = issue_data.get('fields', {})
                
                return {
                    'key': issue_data.get('key'),
                    'summary': fields.get('summary', ''),
                    'description': fields.get('description', '') or '',
                    'status': fields.get('status', {}).get('name', 'Unknown'),
                    'priority': fields.get('priority', {}).get('name', 'None') if fields.get('priority') else 'None',
                    'issue_type': fields.get('issuetype', {}).get('name', 'Unknown'),
                    'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                    'reporter': fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown',
                    'created': fields.get('created', ''),
                    'updated': fields.get('updated', ''),
                    'resolution': fields.get('resolution', {}).get('name', 'Unresolved') if fields.get('resolution') else 'Unresolved',
                    'labels': fields.get('labels', []),
                    'components': [comp.get('name', '') for comp in fields.get('components', [])],
                    'fix_versions': [ver.get('name', '') for ver in fields.get('fixVersions', [])]
                }
            else:
                print(f"⚠️  Failed to fetch JIRA ticket {ticket_id}: HTTP {response.status_code}")
                return None
            
        except Exception as e:
            print(f"⚠️  Failed to fetch JIRA ticket {ticket_id}: {str(e)}")
            return None

    def extract_github_urls_from_ticket(self, ticket_id: str) -> List[str]:
        """Extract GitHub PR/issue URLs from JIRA ticket links and comments."""
        if not self.session:
            return []
        
        github_urls = []
        
        try:
            # Get ticket with links and comments
            url = f"{self.server}/rest/api/2/issue/{ticket_id}"
            params = {
                'expand': 'issuelinks,comments'
            }
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            ticket_data = response.json()
            
            # 1. Check issue links (JIRA Links section)
            issue_links = ticket_data.get('fields', {}).get('issuelinks', [])
            for link in issue_links:
                # Check both inward and outward links
                for link_direction in ['inwardIssue', 'outwardIssue']:
                    if link_direction in link:
                        linked_issue = link[link_direction]
                        # Check if linked issue is actually a GitHub URL (some JIRA setups support this)
                        key = linked_issue.get('key', '')
                        if 'github.com' in key.lower():
                            github_urls.append(key)
            
            # 2. Check description for GitHub URLs
            description = ticket_data.get('fields', {}).get('description', '')
            if description:
                github_urls.extend(self._extract_github_urls_from_text(description))
            
            # 3. Check comments for GitHub URLs
            comments = ticket_data.get('fields', {}).get('comment', {}).get('comments', [])
            for comment in comments:
                comment_body = comment.get('body', '')
                if comment_body:
                    github_urls.extend(self._extract_github_urls_from_text(comment_body))
            
            # 4. Check web links (Remote Links) - this is where manual GitHub links are often added
            try:
                links_url = f"{self.server}/rest/api/2/issue/{ticket_id}/remotelink"
                links_response = self.session.get(links_url, timeout=5)
                
                if links_response.status_code == 200:
                    remote_links = links_response.json()
                    for link in remote_links:
                        link_object = link.get('object', {})
                        link_url = link_object.get('url', '')
                        if link_url and 'github.com' in link_url:
                            github_urls.append(link_url)
            except Exception:
                pass  # Remote links might not be available
            
            # Remove duplicates and filter for PR/issue URLs
            unique_urls = list(set(github_urls))
            pr_urls = []
            
            for url in unique_urls:
                if self._is_github_pr_or_issue_url(url):
                    pr_urls.append(url)
            
            return pr_urls
            
        except Exception as e:
            print(f"⚠️  Error extracting GitHub URLs from {ticket_id}: {str(e)}")
            return []
    
    def _extract_github_urls_from_text(self, text: str) -> List[str]:
        """Extract GitHub URLs from text."""
        if not text:
            return []
        
        # Regex to find GitHub URLs
        github_pattern = r'https?://github\.com/[^\s\]\)>]+(?:/pull/\d+|/issues?/\d+|/commit/[a-f0-9]+)?'
        urls = re.findall(github_pattern, text, re.IGNORECASE)
        
        return urls
    
    def _is_github_pr_or_issue_url(self, url: str) -> bool:
        """Check if URL is a GitHub PR or issue URL."""
        if not url or 'github.com' not in url.lower():
            return False
        
        # Match PR or issue URLs
        pr_issue_pattern = r'github\.com/[^/]+/[^/]+/(?:pull|issues?)/\d+'
        return bool(re.search(pr_issue_pattern, url, re.IGNORECASE))
    
    def enrich_pr_data_with_jira(self, pr_data: Dict) -> Dict:
        """Enrich PR data with JIRA ticket information."""
        if not self.session:
            return pr_data
        
        # Extract JIRA tickets from PR title and body
        jira_tickets = []
        
        # Check PR title
        title_tickets = self.extract_jira_tickets(pr_data.get('title', ''))
        jira_tickets.extend(title_tickets)
        
        # Check PR body
        body_tickets = self.extract_jira_tickets(pr_data.get('body', ''))
        jira_tickets.extend(body_tickets)
        
        # Check commit messages
        for commit in pr_data.get('commits', []):
            commit_tickets = self.extract_jira_tickets(commit.get('message', ''))
            jira_tickets.extend(commit_tickets)
        
        # Remove duplicates
        jira_tickets = list(set(jira_tickets))
        
        if not jira_tickets:
            return pr_data
        
        # Fetch JIRA ticket details
        jira_data = []
        for ticket_id in jira_tickets:
            ticket_info = self.get_jira_ticket_info(ticket_id)
            if ticket_info:
                jira_data.append(ticket_info)
        
        # Add JIRA data to PR data
        enriched_pr_data = pr_data.copy()
        enriched_pr_data['jira_tickets'] = jira_data
        
        return enriched_pr_data
    
    def is_configured(self) -> bool:
        """Check if JIRA client is properly configured."""
        return bool(self.server and self.username and self.api_token and self.session)
