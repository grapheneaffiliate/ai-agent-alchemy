from __future__ import annotations

"""Rendering helpers for the enhanced news dashboard."""

import html
import json
from dataclasses import asdict
from datetime import datetime
from typing import Sequence

from .intelligence import NewsArticle
from .sources import NewsSource


class NewsRenderer:
    """Generate HTML dashboards and artifacts for enhanced news."""

    def render_dashboard(
        self,
        articles: Sequence[NewsArticle],
        topic: str,
        sources: Sequence[NewsSource],
    ) -> str:
        article_dicts = [asdict(article) for article in articles]
        article_dicts.sort(
            key=lambda item: (
                item.get("credibility_score", 0.0),
                item.get("published_date") or "",
            ),
            reverse=True,
        )

        source_badges = [
            self._render_source_badge(source)
            for source in list(sources)[:8]
        ]

        articles_html = [
            self._render_article(article)
            for article in article_dicts
        ]

        return self._wrap_dashboard_html(topic, article_dicts, source_badges, articles_html)

    def _render_source_badge(self, source: NewsSource) -> str:
        level = "high" if source.credibility_score > 0.8 else "medium" if source.credibility_score > 0.6 else "low"
        return (
            f'<span class="source-badge credibility-{level}" '
            f'title="{source.name} (Credibility: {source.credibility_score:.2f})">'
            f'{source.name}'
            '</span>'
        )

    def _render_article(self, article: dict) -> str:
        sentiment_score = float(article.get("sentiment_score") or 0.0)
        sentiment_class = (
            "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral"
        )

        date_string = "Recently"
        published = article.get("published_date")
        if published:
            try:
                parsed_date = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
                date_string = parsed_date.strftime("%B %d, %Y at %I:%M %p")
            except Exception:
                pass

        key_points = article.get("key_points") or []
        key_points_html = (
            '<div class="key-points"><h4>Key Points:</h4><ul>'
            + ''.join(f'<li>{html.escape(point)}</li>' for point in key_points[:3])
            + '</ul></div>'
            if key_points
            else ''
        )

        entities = article.get("entities") or []
        entities_html = (
            '<div class="entities"><h4>Entities:</h4><div class="entity-tags">'
            + ''.join(f'<span class="entity-tag">{html.escape(entity)}</span>' for entity in entities[:5])
            + '</div></div>'
            if entities
            else ''
        )

        source_name = article.get("source", {}).get("name", "Unknown")
        summary = html.escape(article.get("summary", ""))
        headline = html.escape(article.get("headline", ""))
        url = article.get("url", "")

        return (
            '<div class="news-article" '
            f'data-credibility="{article.get("credibility_score", 0.0)}" '
            f'data-sentiment="{sentiment_score}">'            '<div class="article-header">'
            f'<h3><a href="{url}" target="_blank">{headline}</a></h3>'
            '<div class="article-meta">'
            f'<span class="source">{html.escape(source_name)}</span>'
            f'<span class="date">{date_string}</span>'
            f'<span class="credibility-badge">Credibility: {article.get("credibility_score", 0.0):.2f}</span>'
            f'<span class="sentiment-badge sentiment-{sentiment_class}">Sentiment: {sentiment_score:.2f}</span>'
            '</div>'
            '</div>'
            '<div class="article-content">'
            f'<p class="summary">{summary}</p>'
            f'{key_points_html}'
            f'{entities_html}'
            '</div>'
            '<div class="article-footer">'
            f'<a href="{url}" target="_blank" class="read-more">Read Full Article →</a>'
            '</div>'
            '</div>'
        )

    def _wrap_dashboard_html(
        self,
        topic: str,
        article_dicts: list[dict],
        source_badges: list[str],
        articles_html: list[str],
    ) -> str:
        generated_on = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        topic_slug = topic.lower().replace(" ", "-")
        topic_escaped = html.escape(topic)
        source_badges_html = ''.join(source_badges)
        articles_section = ''.join(articles_html)
        export_payload = json.dumps(article_dicts)

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Enhanced News Dashboard - {topic_escaped}</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    margin: 0;
                    padding: 0;
                    color: #2c3e50;
                }}
                .dashboard-header {{
                    padding: 2rem;
                    text-align: center;
                }}
                .dashboard-header h1 {{
                    font-size: 2.5rem;
                    margin-bottom: 0.5rem;
                }}
                .dashboard-header .subtitle {{
                    opacity: 0.9;
                    font-size: 1.1rem;
                }}
                .sources-section {{
                    background: white;
                    padding: 1.5rem;
                    margin: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .sources-section h2 {{
                    color: #333;
                    margin-bottom: 1rem;
                }}
                .source-badges {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }}
                .source-badge {{
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    font-weight: 500;
                }}
                .credibility-high {{ background: #d4edda; color: #155724; }}
                .credibility-medium {{ background: #fff3cd; color: #856404; }}
                .credibility-low {{ background: #f8d7da; color: #721c24; }}
                .controls-section {{
                    background: white;
                    padding: 1.5rem;
                    margin: 0 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .controls {{
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                    flex-wrap: wrap;
                }}
                .control-group {{
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}
                .control-group label {{
                    font-weight: 500;
                    color: #555;
                }}
                .control-group select {{
                    padding: 0.5rem;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    font-size: 0.9rem;
                }}
                .articles-section {{
                    padding: 2rem;
                }}
                .articles-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 2rem;
                    margin-top: 1rem;
                }}
                .news-article {{
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                .news-article:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}
                .article-header {{
                    padding: 1.5rem;
                    border-bottom: 1px solid #eee;
                }}
                .article-header h3 {{
                    margin-bottom: 0.75rem;
                }}
                .article-header h3 a {{
                    color: #2c3e50;
                    text-decoration: none;
                }}
                .article-header h3 a:hover {{
                    color: #3498db;
                }}
                .article-meta {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 1rem;
                    font-size: 0.85rem;
                    color: #666;
                }}
                .credibility-badge, .sentiment-badge {{
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 500;
                }}
                .sentiment-positive {{ background: #d4edda; color: #155724; }}
                .sentiment-negative {{ background: #f8d7da; color: #721c24; }}
                .sentiment-neutral {{ background: #e2e3e5; color: #383d41; }}
                .article-content {{
                    padding: 1.5rem;
                }}
                .summary {{
                    margin-bottom: 1rem;
                    color: #555;
                }}
                .key-points, .entities {{
                    margin-top: 1rem;
                }}
                .key-points h4, .entities h4 {{
                    font-size: 0.9rem;
                    color: #333;
                    margin-bottom: 0.5rem;
                }}
                .key-points ul {{
                    list-style: none;
                    padding-left: 0;
                }}
                .key-points li {{
                    padding: 0.25rem 0;
                    padding-left: 1rem;
                    position: relative;
                }}
                .key-points li:before {{
                    content: "•";
                    color: #667eea;
                    font-weight: bold;
                    position: absolute;
                    left: 0;
                }}
                .entity-tags {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }}
                .entity-tag {{
                    background: #e3f2fd;
                    color: #1976d2;
                    padding: 0.25rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.8rem;
                }}
                .article-footer {{
                    padding: 1rem 1.5rem;
                    background: #f8f9fa;
                    border-top: 1px solid #eee;
                }}
                .read-more {{
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .read-more:hover {{
                    color: #5a6fd8;
                }}
                .export-controls {{
                    text-align: center;
                    margin: 2rem 0;
                }}
                .export-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    margin: 0 0.5rem;
                    font-size: 0.9rem;
                    transition: background 0.2s;
                }}
                .export-btn:hover {{
                    background: #5a6fd8;
                }}
                @media (max-width: 768px) {{
                    .dashboard-header h1 {{ font-size: 2rem; }}
                    .articles-grid {{ grid-template-columns: 1fr; }}
                    .controls {{ flex-direction: column; align-items: stretch; }}
                    .source-badges {{ justify-content: center; }}
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-header" data-topic="{topic_escaped}">
                <h1>📰 Enhanced News Dashboard</h1>
                <div class="subtitle">Intelligent news aggregation for "{topic_escaped}"</div>
                <div class="subtitle">Generated on {generated_on}</div>
            </div>
            <div class="sources-section">
                <h2>🔍 Sources Used ({len(sources)} authoritative sources)</h2>
                <div class="source-badges">{source_badges_html}</div>
            </div>
            <div class="controls-section">
                <h2>⚙️ Filter & Sort Options</h2>
                <div class="controls">
                    <div class="control-group">
                        <label for="sort-by">Sort by:</label>
                        <select id="sort-by">
                            <option value="credibility">Credibility</option>
                            <option value="sentiment">Sentiment</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="filter-sentiment">Sentiment:</label>
                        <select id="filter-sentiment">
                            <option value="all">All sentiment</option>
                            <option value="positive">Positive</option>
                            <option value="negative">Negative</option>
                            <option value="neutral">Neutral</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="min-credibility">Credibility ≥</label>
                        <select id="min-credibility">
                            <option value="0">0.0</option>
                            <option value="0.5">0.5</option>
                            <option value="0.7">0.7</option>
                            <option value="0.8">0.8</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="articles-section">
                <h2>🗞️ Latest Articles ({len(article_dicts)} found)</h2>
                <div class="articles-grid" id="articles-container">{articles_section}</div>
            </div>
            <div class="export-controls">
                <button class="export-btn" onclick="exportToJSON()">📄 Export to JSON</button>
                <button class="export-btn" onclick="exportToCSV()">📊 Export to CSV</button>
                <button class="export-btn" onclick="printDashboard()">🖨️ Print Dashboard</button>
                <button class="export-btn" onclick="shareDashboard()">📤 Share Dashboard</button>
            </div>
            <script>
                const articlesContainer = document.getElementById('articles-container');
                const articles = Array.from(articlesContainer.children);
                function applyFilters() {{
                    const sortBy = document.getElementById('sort-by').value;
                    const filterSentiment = document.getElementById('filter-sentiment').value;
                    const minCredibility = parseFloat(document.getElementById('min-credibility').value);
                    const filteredArticles = articles.filter(article => {{
                        const credibility = parseFloat(article.dataset.credibility);
                        const sentiment = parseFloat(article.dataset.sentiment);
                        if (credibility < minCredibility) return false;
                        if (filterSentiment !== 'all') {{
                            if (filterSentiment === 'positive' && sentiment <= 0) return false;
                            if (filterSentiment === 'negative' && sentiment >= 0) return false;
                            if (filterSentiment === 'neutral' && Math.abs(sentiment) > 0.1) return false;
                        }}
                        return true;
                    }});
                    filteredArticles.sort((a, b) => {{
                        const aCred = parseFloat(a.dataset.credibility);
                        const bCred = parseFloat(b.dataset.credibility);
                        const aSent = parseFloat(a.dataset.sentiment);
                        const bSent = parseFloat(b.dataset.sentiment);
                        if (sortBy === 'credibility') {{
                            return bCred - aCred;
                        }} else if (sortBy === 'sentiment') {{
                            return bSent - aSent;
                        }}
                        return 0;
                    }});
                    articlesContainer.innerHTML = '';
                    filteredArticles.forEach(article => articlesContainer.appendChild(article));
                }}
                document.getElementById('sort-by').addEventListener('change', applyFilters);
                document.getElementById('filter-sentiment').addEventListener('change', applyFilters);
                document.getElementById('min-credibility').addEventListener('change', applyFilters);
                const articlesData = {export_payload};
                function exportToJSON() {{
                    const data = {{topic: "{topic_escaped}", articles: articlesData}};
                    const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'news-dashboard-{topic_slug}.json';
                    a.click();
                    URL.revokeObjectURL(url);
                }}
                function exportToCSV() {{
                    let csv = 'Headline,URL,Source,Summary,Credibility,Sentiment\n';
                    articlesData.forEach(article => {{
                        const line = `"${{article.headline.replace(/"/g, '""')}}","${{article.url}}","${{article.source.name}}","${{article.summary.replace(/"/g, '""')}}",${{article.credibility_score}},${{article.sentiment_score}}`;
                        csv += line + '
';
                    }});
                    const blob = new Blob([csv], {{type: 'text/csv'}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'news-dashboard-{topic_slug}.csv';
                    a.click();
                    URL.revokeObjectURL(url);
                }}
                function printDashboard() {{ window.print(); }}
                function shareDashboard() {{
                    const title = 'Enhanced News Dashboard - {topic_escaped}';
                    const text = 'Check out this intelligent news aggregation for {topic_escaped}';
                    if (navigator.share) {{
                        navigator.share({{title, text, url: window.location.href}});
                    }} else {{
                        navigator.clipboard.writeText(window.location.href);
                        alert('Dashboard URL copied to clipboard!');
                    }}
                }}
                applyFilters();
            </script>
        </body>
        </html>
        """
