"""
Data ingestion module for fetching travel guide data
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import json
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)


class JaipurDataFetcher:
    """Fetches travel guide data for Jaipur from various sources"""
    
    def __init__(self, data_dir: str = "data/raw/jaipur"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_wikivoyage(self) -> Dict:
        """Fetch Jaipur page from Wikivoyage"""
        url = "https://en.wikivoyage.org/wiki/Jaipur"
        
        try:
            logger.info(f"Fetching data from Wikivoyage: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['nav', 'footer', 'script', 'style', 'aside']):
                element.decompose()
            
            # Extract main content
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                raise ValueError("Could not find main content")
            
            # Extract sections
            sections = {}
            current_section = None
            current_content = []
            
            for element in content_div.find_all(['h2', 'h3', 'p', 'ul', 'ol', 'dl']):
                if element.name in ['h2', 'h3']:
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = {
                            'content': '\n'.join(current_content),
                            'url': url,
                            'anchor': f"#{element.get('id', current_section.lower().replace(' ', '_'))}"
                        }
                    
                    # Start new section
                    current_section = element.get_text().strip()
                    current_content = []
                else:
                    # Add content to current section
                    text = element.get_text().strip()
                    if text:
                        current_content.append(text)
            
            # Save last section
            if current_section and current_content:
                sections[current_section] = {
                    'content': '\n'.join(current_content),
                    'url': url,
                    'anchor': f"#{current_section.lower().replace(' ', '_')}"
                }
            
            # Save to file
            output_file = self.data_dir / "wikivoyage_jaipur.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'source': 'wikivoyage',
                    'url': url,
                    'sections': sections,
                    'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Fetched {len(sections)} sections from Wikivoyage")
            return sections
            
        except Exception as e:
            logger.error(f"❌ Error fetching Wikivoyage: {e}")
            raise
    
    def fetch_wikipedia(self) -> Dict:
        """Fetch Jaipur article from Wikipedia (travel-related sections)"""
        url = "https://en.wikipedia.org/wiki/Jaipur"
        
        try:
            logger.info(f"Fetching data from Wikipedia: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['nav', 'footer', 'script', 'style', 'table', 'aside']):
                element.decompose()
            
            # Find relevant sections (Tourism, Culture, Transport, etc.)
            relevant_keywords = ['Tourism', 'Culture', 'Transport', 'Geography', 'History', 'Attractions']
            sections = {}
            
            for heading in soup.find_all(['h2', 'h3']):
                heading_text = heading.get_text().strip()
                if any(keyword in heading_text for keyword in relevant_keywords):
                    section_content = []
                    next_element = heading.find_next_sibling()
                    
                    while next_element and next_element.name not in ['h2', 'h3']:
                        if next_element.name in ['p', 'ul', 'ol']:
                            text = next_element.get_text().strip()
                            if text:
                                section_content.append(text)
                        next_element = next_element.find_next_sibling()
                    
                    if section_content:
                        sections[heading_text] = {
                            'content': '\n'.join(section_content),
                            'url': url,
                            'anchor': f"#{heading.get('id', '')}"
                        }
            
            # Save to file
            output_file = self.data_dir / "wikipedia_jaipur.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'source': 'wikipedia',
                    'url': url,
                    'sections': sections,
                    'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Fetched {len(sections)} sections from Wikipedia")
            return sections
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching Wikipedia: {e} (continuing without it)")
            # Don't raise - Wikipedia is optional
            return {}
    
    def fetch_all(self) -> Dict:
        """Fetch all data sources"""
        logger.info("🔄 Fetching data for Jaipur...")
        
        data = {
            'wikivoyage': self.fetch_wikivoyage(),
            'wikipedia': self.fetch_wikipedia()
        }
        
        logger.info(f"✅ Data fetching complete!")
        return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = JaipurDataFetcher()
    fetcher.fetch_all()















