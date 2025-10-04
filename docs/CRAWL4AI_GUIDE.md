# Crawl4AI Usage Guide

## Overview

Crawl4AI is an advanced web scraping tool optimized for extracting clean, LLM-ready markdown content from websites. This guide explains how to use it effectively with the MCP AI Agent.

## When to Use Crawl4AI

### Perfect Use Cases
- 📄 **Content Extraction**: Getting article text, blog posts, documentation
- 🔍 **Website Analysis**: Understanding site structure and content
- 📊 **Business Information**: Extracting company details, services, contact info
- 📝 **Research**: Collecting information from multiple pages

### When to Use Other Tools
- 🖼️ **Screenshots**: Use Playwright browser tools
- 🖱️ **Interactions**: Use Playwright for clicking, form filling
- 📰 **News Headlines**: Use `fetch-news` tool first
- ⚡ **Quick Checks**: Use `browse-url` + `browser-extract-smart` for simple lookups

## How It Works

### Configuration

The plugin uses optimal settings for clean content extraction:

```python
# Content Filtering
- PruningContentFilter: Removes navigation, ads, boilerplate
- Excluded tags: nav, header, footer, aside, form, script, style
- Word threshold: 15 (skips very short blocks)
- Social media links: Filtered out
- External images: Excluded

# Markdown Generation  
- Skip internal anchor links
- No text wrapping
- Clean formatting
- Prefer fit_markdown (filtered) over raw_markdown
```

### What Gets Filtered Out

✅ **Removed Automatically:**
- Navigation menus
- Headers and footers
- Sidebar widgets
- Form elements
- "Skip to content" links
- Cookie notices
- Social media buttons
- Advertisement sections
- Excessive blank lines

✅ **Kept:**
- Main content text
- Headings and structure
- Important links (2-3 max in summary)
- Business contact information
- Key service/product descriptions

## Usage Examples

### Basic Crawl

**User Request:**
```
crawl https://example.com
```

**What Happens:**
1. Crawl4AI fetches the page
2. Content is filtered and cleaned
3. Markdown is extracted
4. **Agent creates brief summary**
5. **Full markdown saved to artifact**

**Agent Response:**
```
I've successfully crawled Example Company website.

**Summary:**
Example Company provides web services including:
• Website hosting and domain registration
• Email services and cloud storage
• 24/7 customer support

They serve over 1 million customers globally with a focus on 
reliability and ease of use.

**Key Information:**
• Founded: 2010
• Headquarters: San Francisco, CA
• Support: support@example.com

[Full content saved to artifact for detailed review]
```

### Crawl with Specific Focus

**User Request:**
```
crawl https://techblog.com/ai-article and tell me about their AI insights
```

**Agent Process:**
1. Crawls the URL
2. Extracts clean markdown
3. **Analyzes content for AI-related information**
4. Provides focused summary
5. Saves full content to artifact

### Business Website Crawl

**Perfect for extracting:**
- Company name and description
- Services/products offered
- Contact information
- Location/service areas
- Business hours
- Key differentiators

**Example Output:**
```
**ABC Services Analysis:**

Core Business: Professional cleaning services
Service Areas: Phoenix, Scottsdale, Tempe
Contact: (555) 123-4567

Main Services:
• Residential cleaning
• Commercial office cleaning  
• Deep cleaning and sanitization
• Move-in/move-out cleaning

Unique Features:
• Eco-friendly products
• Same-day service available
• 100% satisfaction guarantee
• Licensed and insured

[Complete website content in artifact]
```

## Response Format Guidelines

### Summary Structure (200-300 words max)

```markdown
**[Company/Site Name]:**

[1-2 sentence overview]

**Services/Products:**
• Item 1
• Item 2
• Item 3

**Key Information:**
• Detail 1
• Detail 2
• Contact info

[Brief closing statement]

[Artifact reference]
```

### What NOT to Include in Summary

❌ Navigation menu items
❌ "Skip to content" text
❌ Footer copyright notices
❌ Complete link lists
❌ Raw HTML fragments
❌ Repeated headers/footers
❌ Cookie policy text
❌ Social media follow buttons

### Artifact Content

The artifact should contain:
- ✅ Full cleaned markdown
- ✅ Proper headings and structure
- ✅ All main content text
- ✅ Important links (organized)
- ✅ Clean formatting

## Advanced Features

### CSS Selector (Coming Soon)

Extract specific sections:
```python
crawl_url(
    url="https://example.com",
    css_selector="article.main-content"
)
```

### Structured Extraction (Coming Soon)

Extract data with schema:
```python
extract_structured(
    url="https://example.com",
    schema={
        "name": "Products",
        "baseSelector": "div.product",
        "fields": [
            {"name": "title", "selector": "h2"},
            {"name": "price", "selector": ".price"}
        ]
    }
)
```

## Quality Checklist

Before responding to user with crawl results:

- [ ] Created brief 200-300 word summary
- [ ] Extracted key business information
- [ ] Mentioned only 2-3 most important links
- [ ] Saved full content to artifact
- [ ] Used bullet points for readability
- [ ] No raw markdown dumped to chat
- [ ] No navigation/footer junk
- [ ] Professional formatting
- [ ] Clear, actionable information

## Troubleshooting

### Issue: Content seems incomplete
**Solution:** Check if site uses JavaScript for content loading. Consider using Playwright browser tools instead.

### Issue: Too much boilerplate in results
**Solution:** The pruning filter should handle this. If not, adjust threshold in plugin configuration.

### Issue: Important content filtered out
**Solution:** Use css_selector parameter to target specific content area.

### Issue: Links not appearing correctly
**Solution:** Links are intentionally limited in summary. Full link list is in artifact.

## Technical Details

### Dependencies
```bash
pip install -U crawl4ai
```

### Plugin Location
```
mcp-ai-agent/src/plugins/crawl4ai_plugin.py
```

### Configuration Location
```
Plugin configuration in crawl4ai_plugin.py
Agent instructions in .clinerules
```

## Best Practices

### For Agents
1. **Always create summary first** - Don't dump raw markdown
2. **Save full content to artifact** - Let users access details
3. **Focus on what matters** - Extract key business info
4. **Use bullet points** - Make summaries scannable
5. **Include contact info** - When available and relevant

### For Users
1. **Be specific** - "Crawl [URL] and tell me about [topic]"
2. **Request artifacts** - "Save the full content to an artifact"
3. **Ask follow-ups** - "What are their main services?"
4. **Combine with other tools** - Crawl → Analyze → Summarize

## Examples Gallery

### E-commerce Site
```
Summary focuses on:
- Product categories
- Pricing tiers
- Shipping policies
- Contact/support info
```

### Blog/News Site
```
Summary focuses on:
- Main topics covered
- Recent articles
- Author information
- Subscription options
```

### Service Business
```
Summary focuses on:
- Services offered
- Service areas
- Contact information
- Unique value propositions
```

### Documentation Site
```
Summary focuses on:
- Main topics/sections
- Getting started info
- Key features documented
- Support resources
```

## Future Enhancements

- [ ] Multiple page crawling
- [ ] PDF extraction
- [ ] Screenshot + crawl combination
- [ ] Link validation
- [ ] Content comparison
- [ ] Scheduled crawling
- [ ] Change detection

## Support

For issues or questions:
1. Check this guide first
2. Review .clinerules for agent instructions
3. Examine crawl4ai_plugin.py for technical details
4. Test with simple URLs first
5. Report bugs with example URLs

---

**Remember:** Crawl4AI is about getting clean, usable content - not raw HTML dumps. Always prioritize user experience with clear summaries and organized artifacts.
