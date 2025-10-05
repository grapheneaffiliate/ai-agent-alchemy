"""Artifact generation for Open WebUI integration."""

from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime
import base64  # For image/PDF handling in Claude API


class ArtifactGenerator:
    """Generate HTML/SVG artifacts for Open WebUI rendering."""
    
    @staticmethod
    async def detect_artifact_request(message: str) -> Optional[str]:
        """Detect if message requests an artifact and return type."""
        message_lower = message.lower()

        # GAME requests (most specific)
        if 'game' in message_lower and any(word in message_lower for word in ['create', 'make', 'build', 'generate', 'play']):
            return 'game'

        # HTML/Webpage requests
        html_keywords = ['create html', 'generate html', 'make a webpage',
                        'build a page', 'create a website', 'html page',
                        'create an artifact', 'create artifact', 'as an artifact']
        if any(kw in message_lower for kw in html_keywords):
            return 'html'
        
        # SVG requests
        svg_keywords = ['create svg', 'generate svg', 'make an svg', 
                       'svg graphic', 'svg image']
        if any(kw in message_lower for kw in svg_keywords):
            return 'svg'
        
        # Visualization requests
        viz_keywords = ['create visualization', 'visualize', 'create chart',
                       'create graph', 'plot', 'diagram']
        if any(kw in message_lower for kw in viz_keywords):
            return 'visualization'
        
        # News display requests
        news_keywords = ['show me news', 'show news', 'get news', 'fetch news',
                        'latest news', 'top news', 'news stories', 'news about']
        if any(kw in message_lower for kw in news_keywords):
            return 'news'
        
        return None
    
    @staticmethod
    async def generate_news_page(news_data: Dict[str, Any]) -> str:
        """Generate an HTML page displaying news articles."""
        articles = news_data.get('articles', [])
        topic = news_data.get('topic', 'News')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic.title()} News</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .header p {{
            font-size: 1rem;
            opacity: 0.9;
        }}
        .articles {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}
        .article {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .article:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }}
        .article h2 {{
            color: #667eea;
            font-size: 1.1rem;
            margin-bottom: 0.75rem;
            line-height: 1.4;
        }}
        .article a {{
            color: #667eea;
            text-decoration: none;
        }}
        .article a:hover {{
            text-decoration: underline;
        }}
        .article .summary {{
            color: #666;
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 0.75rem;
        }}
        .article .meta {{
            color: #999;
            font-size: 0.85rem;
            border-top: 1px solid #eee;
            padding-top: 0.75rem;
            margin-top: 0.75rem;
        }}
        .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 {topic.title()} News</h1>
            <p>Latest articles from around the web</p>
        </div>
        <div class="articles">
"""
        
        for i, article in enumerate(articles[:10], 1):
            headline = article.get('headline', 'No title')
            url = article.get('url', '#')
            summary = article.get('summary', '')
            published = article.get('published', '')
            
            html += f"""
            <div class="article">
                <span class="badge">Article {i}</span>
                <h2><a href="{url}" target="_blank">{headline}</a></h2>
                <p class="summary">{summary[:200]}{'...' if len(summary) > 200 else ''}</p>
                <div class="meta">
                    <strong>Published:</strong> {published}
                </div>
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def generate_data_visualization(data: Dict[str, Any], viz_type: str = 'chart') -> str:
        """Generate an HTML page with D3.js visualization."""
        title = data.get('title', 'Data Visualization')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            max-width: 900px;
            width: 100%;
        }}
        h1 {{
            color: #333;
            margin-bottom: 2rem;
            text-align: center;
        }}
        #chart {{
            width: 100%;
            height: 400px;
        }}
        .bar {{
            fill: steelblue;
            transition: fill 0.3s ease;
        }}
        .bar:hover {{
            fill: #667eea;
        }}
        .axis {{
            font-size: 12px;
        }}
        .axis-label {{
            font-size: 14px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div id="chart"></div>
    </div>
    <script>
        // Sample data visualization
        const data = [
            {{name: 'A', value: 30}},
            {{name: 'B', value: 80}},
            {{name: 'C', value: 45}},
            {{name: 'D', value: 60}},
            {{name: 'E', value: 20}},
            {{name: 'F', value: 90}}
        ];
        
        const margin = {{top: 20, right: 20, bottom: 50, left: 50}};
        const width = 800 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;
        
        const svg = d3.select('#chart')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
        
        const x = d3.scaleBand()
            .range([0, width])
            .domain(data.map(d => d.name))
            .padding(0.2);
        
        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.value)])
            .range([height, 0]);
        
        svg.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('width', x.bandwidth())
            .attr('y', d => y(d.value))
            .attr('height', d => height - y(d.value));
        
        svg.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0,${{height}})`)
            .call(d3.axisBottom(x));
        
        svg.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y));
        
        svg.append('text')
            .attr('class', 'axis-label')
            .attr('text-anchor', 'middle')
            .attr('x', width / 2)
            .attr('y', height + 40)
            .text('Categories');
        
        svg.append('text')
            .attr('class', 'axis-label')
            .attr('text-anchor', 'middle')
            .attr('transform', 'rotate(-90)')
            .attr('x', -height / 2)
            .attr('y', -35)
            .text('Values');
    </script>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def generate_simple_svg(content: str = "Hello") -> str:
        """Generate a simple SVG graphic."""
        return f"""<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="400" height="200" fill="url(#grad1)" rx="10"/>
    <text x="200" y="100" font-family="Arial, sans-serif" font-size="36" 
          fill="white" text-anchor="middle" dominant-baseline="middle">
        {content}
    </text>
</svg>"""
    
    @staticmethod
    def generate_generic_html(title: str, content: str) -> str:
        """Generate a well-formatted HTML page for crawled news content."""
        import re
        
        # Enhanced parsing for news articles
        # Look for patterns like: "Title • Source • Time • Summary"
        articles: List[Dict[str, Any]] = []
        
        # Pattern 1: Lines with bullets (•) often indicate news items
        bullet_pattern = r'\*(.+?)•(.+?)•(.+?)•(.+?)(?:\n|$)'
        bullet_matches = re.findall(bullet_pattern, content, re.MULTILINE)
        
        for match in bullet_matches:
            headline = match[0].strip()
            source = match[1].strip() if len(match) > 1 else ''
            time_info = match[2].strip() if len(match) > 2 else ''
            summary = match[3].strip() if len(match) > 3 else ''
            
            # Extract URL from the section
            url_match = re.search(r'https?://[^\s\)>\]]+', summary + '\n' + content[content.find(headline):content.find(headline)+500])
            url = url_match.group(0) if url_match else '#'
            
            articles.append({
                'headline': headline,
                'text': f"{source} • {time_info}\n{summary}",
                'links': [{'text': 'Read article', 'url': url}]
            })
        
        # Pattern 2: If bullet pattern fails, try numbered lists or markdown headings
        if not articles:
            lines = content.split('\n')
            current_article = {'headline': '', 'text': '', 'links': []}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if it's a numbered item or heading (1., ##, **)
                if (line.startswith(tuple(f'{i}.' for i in range(1, 100))) or 
                    line.startswith('##') or 
                    (line.startswith('**') and line.endswith('**')) or
                    (line.startswith('*') and '•' in line)):
                    
                    # Save previous article if it has content
                    if current_article['headline']:
                        articles.append(current_article)
                        current_article = {'headline': '', 'text': '', 'links': []}
                    
                    # Clean heading - remove numbers, ##, **, etc.
                    headline = re.sub(r'^\d+\.\s*|\*\*|##', '', line).strip()
                    # If it has a bullet, take first part as headline
                    if '•' in headline:
                        headline = headline.split('•')[0].strip()
                    current_article['headline'] = headline
                
                # Check if line contains a link
                elif 'http' in line:
                    url_match = re.search(r'https?://[^\s\)>\]]+', line)
                    if url_match:
                        url = url_match.group(0)
                        text_match = re.search(r'\[(.*?)\]', line)
                        link_text = text_match.group(1) if text_match else 'Read article'
                        current_article['links'].append({'text': link_text[:80], 'url': url})
                
                # Regular text (build summary)
                elif len(line) > 20 and current_article['headline']:
                    current_article['text'] += line + ' '
            
            # Add last article
            if current_article['headline']:
                articles.append(current_article)
        
        # Pattern 3: If still no articles, try splitting by double newlines
        if not articles:
            blocks = content.split('\n\n')
            for block in blocks[:10]:
                if len(block) > 50:
                    # First line is headline, rest is text
                    parts = block.split('\n', 1)
                    headline = parts[0][:100]
                    text = parts[1] if len(parts) > 1 else ''
                    
                    # Extract any URLs from the block
                    urls = re.findall(r'https?://[^\s\)>\]]+', block)
                    
                    articles.append({
                        'headline': headline,
                        'text': text[:300],
                        'links': [{'text': 'Read article', 'url': urls[0]}] if urls else []
                    })
        
        # Fallback: Create one article from content
        if not articles:
            urls = re.findall(r'https?://[^\s\)>\]]+', content)
            articles = [{
                'headline': title,
                'text': content[:500],
                'links': [{'text': 'Read article', 'url': urls[0]}] if urls else []
            }]
        
        # Generate clean HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }}
        .header h1 {{
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            margin-bottom: 0.5rem;
        }}
        .articles {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}
        .article {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }}
        .article:hover {{ transform: translateY(-5px); }}
        .article h2 {{
            color: #667eea;
            font-size: 1.3rem;
            margin-bottom: 1rem;
            line-height: 1.3;
        }}
        .article .text {{
            color: #555;
            line-height: 1.6;
            margin-bottom: 1rem;
        }}
        .article a {{
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            padding: 0.5rem 1rem;
            background: #f0f0f0;
            border-radius: 6px;
            transition: background 0.3s;
        }}
        .article a:hover {{
            background: #667eea;
            color: white;
        }}
        .badge {{
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-bottom: 0.75rem;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{len(articles)} articles found</p>
        </div>
        <div class="articles">
"""
        
        for i, article in enumerate(articles[:10], 1):
            headline = article.get('headline', 'Article')[:100]
            text = article.get('text', '')[:300]
            links = article.get('links', [])
            
            html += f"""
            <div class="article">
                <span class="badge">Article {i}</span>
                <h2>{headline}</h2>
                <p class="text">{text}{'...' if len(text) == 300 else ''}</p>
"""
            # Add first link only
            if links:
                if isinstance(links[0], dict):
                    link_url = links[0].get('url', '#')
                    link_text = links[0].get('text', 'Read more')[:50]
                else:
                    link_url = str(links[0])
                    link_text = 'Read article'
                
                html += f'                <a href="{link_url}" target="_blank">{link_text} →</a>\n'
            
            html += '            </div>\n'
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def extract_articles_from_text(text: str) -> List[Dict[str, Any]]:
        """Extract article data from LLM's formatted response text."""
        import re
        articles = []
        
        # Pattern: Look for numbered lists with article info
        # Example: "1. *Title* • Source: X • Time: Y • Summary: Z"
        pattern = r'(\d+)\.\s*\*(.+?)\*\s*•?\s*(?:Source:\s*(.+?)\s*•)?\s*(?:Time:\s*(.+?)\s*•)?\s*(?:Summary:\s*)?(.+?)(?=\n\n|\n\d+\.|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            num, headline, source, time_info, summary = match
            
            # Extract URL from surrounding text
            # Look for "Full Article" links or embedded URLs
            article_section = text[text.find(headline):text.find(headline)+1000]
            url_match = re.search(r'https?://[^\s\)>\]]+', article_section)
            url = url_match.group(0) if url_match else '#'
            
            articles.append({
                'headline': headline.strip(),
                'summary': (f"{source} • {time_info}\n{summary}" if source else summary).strip()[:300],
                'url': url,
                'published': time_info.strip() if time_info else ''
            })
        
        # Alternative: Lines starting with numbers and asterisks
        if not articles:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # Look for: "1. *Headline*" or similar
                if re.match(r'^\d+\.\s*\*', line):
                    # Extract headline between asterisks
                    headline_match = re.search(r'\*(.+?)\*', line)
                    if headline_match:
                        headline = headline_match.group(1)
                        
                        # Get next few lines as summary
                        summary_lines = []
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and not next_line.startswith(tuple(f'{k}.' for k in range(1, 100))):
                                summary_lines.append(next_line)
                            else:
                                break
                        
                        summary = ' '.join(summary_lines)[:300]
                        
                        # Extract URL
                        url_match = re.search(r'https?://[^\s\)>\]]+', summary + line)
                        url = url_match.group(0) if url_match else '#'
                        
                        articles.append({
                            'headline': headline.strip(),
                            'summary': summary,
                            'url': url,
                            'published': ''
                        })
        
        return articles
    
    @staticmethod
    def format_text_response(text: str) -> str:
        """Format plain text responses with better structure."""
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if not paragraphs:
            paragraphs = [text]

        # Format with proper spacing
        formatted = '\n\n'.join(paragraphs)

        # Add bullet points for lists
        formatted = formatted.replace('- ', '\n• ')
        formatted = formatted.replace('* ', '\n• ')

        return formatted

    @staticmethod
    async def extract_artifact(response: str) -> Optional[str]:
        """
        Extract HTML artifact from LLM response.

        Looks for Claude-style artifacts with MIME types or HTML code blocks.
        Returns HTML string if found, None otherwise.
        """
        import re

        # Pattern 1: Claude-style artifact with MIME type (HTML)
        if 'application/vnd.ant.html' in response or 'text/html' in response:
            # Look for HTML content after the MIME type declaration
            mime_pattern = r'(application/vnd\.ant\.html|text/html)\s*\n'
            mime_match = re.search(mime_pattern, response)

            if mime_match:
                content_start = mime_match.end()

                # Look for <!DOCTYPE html> or <html
                html_match = re.search(r'<!DOCTYPE html>|<html', response[content_start:], re.IGNORECASE)
                if html_match:
                    html_start = content_start + html_match.start()

                    # Find the end - look for closing </html> tag
                    html_end_match = re.search(r'</html>\s*', response[html_start:], re.IGNORECASE)
                    if html_end_match:
                        html_end = html_start + html_end_match.end()
                        artifact_html = response[html_start:html_end].strip()

                        # Clean up any Claude formatting markers
                        artifact_html = re.sub(r'^.*?application/vnd\.ant\.html\s*\n', '', artifact_html)
                        artifact_html = re.sub(r'^.*?text/html\s*\n', '', artifact_html)

                        return artifact_html

        # Pattern 2: Traditional ```html code blocks (fallback)
        if '```html' in response:
            # Extract everything between ```html and the next ```
            start_marker = response.find('```html')
            if start_marker != -1:
                content_start = start_marker + len('```html')

                # Look for closing ```
                end_marker = response.find('```', content_start)
                if end_marker == -1:
                    end_marker = len(response)

                artifact_html = response[content_start:end_marker].strip()
                return artifact_html

        # Pattern 3: Markdown artifacts (convert to HTML for display)
        if ('text/markdown' in response or 'application/vnd.ant.code' in response):
            # Look for markdown content
            if 'text/markdown' in response:
                mime_match = re.search(r'text/markdown\s*\n', response)
                if mime_match:
                    content_start = mime_match.end()
                    markdown_content = response[content_start:].strip()

                    # Convert markdown to simple HTML
                    artifact_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }}
                            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                            h2 {{ color: #555; margin-top: 20px; }}
                            ul {{ margin-left: 20px; }}
                            li {{ margin-bottom: 8px; }}
                        </style>
                    </head>
                    <body>
                        <pre style="white-space: pre-wrap; font-family: inherit;">{markdown_content}</pre>
                    </body>
                    </html>
                    """
                    return artifact_html

        return None
