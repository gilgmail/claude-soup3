#!/usr/bin/env python3
"""
Create Notion databases for Financial Wisdom Platform
Sets up the complete database schema in Notion
"""

import os
import sys
from notion_client import Client
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_articles_database(client: Client, parent_page_id: str) -> str:
    """Create the articles database in Notion"""
    
    database_config = {
        "parent": {"page_id": parent_page_id},
        "title": [{"text": {"content": "Financial Articles Database"}}],
        "properties": {
            "Title": {
                "title": {}
            },
            "Article ID": {
                "rich_text": {}
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "草稿", "color": "gray"},
                        {"name": "已生成", "color": "blue"},
                        {"name": "質量檢查", "color": "yellow"},
                        {"name": "已批准", "color": "green"},
                        {"name": "已發布", "color": "purple"},
                        {"name": "已存檔", "color": "red"}
                    ]
                }
            },
            "Content Style": {
                "select": {
                    "options": [
                        {"name": "勵志財經", "color": "orange"},
                        {"name": "哲學思考", "color": "purple"},
                        {"name": "實用智慧", "color": "green"},
                        {"name": "歷史洞察", "color": "brown"}
                    ]
                }
            },
            "Topic Category": {
                "select": {
                    "options": [
                        {"name": "投資理財", "color": "blue"},
                        {"name": "數字貨幣投資", "color": "orange"},
                        {"name": "房地產投資", "color": "green"},
                        {"name": "退休規劃", "color": "purple"},
                        {"name": "風險管理", "color": "red"},
                        {"name": "個人財務", "color": "yellow"},
                        {"name": "經濟分析", "color": "gray"}
                    ]
                }
            },
            "Keywords": {
                "multi_select": {
                    "options": [
                        {"name": "投資", "color": "blue"},
                        {"name": "理財", "color": "green"},
                        {"name": "基金", "color": "purple"},
                        {"name": "股票", "color": "red"},
                        {"name": "風險管理", "color": "orange"},
                        {"name": "ESG", "color": "yellow"},
                        {"name": "數字貨幣", "color": "pink"},
                        {"name": "人工智能", "color": "gray"},
                        {"name": "房地產", "color": "brown"}
                    ]
                }
            },
            "Trend Score": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Overall Score": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Readability": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Engagement": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Educational Value": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Actionability": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Originality": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Word Count": {
                "number": {
                    "format": "number"
                }
            },
            "Insights Count": {
                "number": {
                    "format": "number"
                }
            },
            "Action Steps": {
                "number": {
                    "format": "number"
                }
            },
            "Created At": {
                "date": {}
            },
            "Published At": {
                "date": {}
            }
        }
    }
    
    response = client.databases.create(**database_config)
    return response["id"]

def create_topics_database(client: Client, parent_page_id: str) -> str:
    """Create the topics database in Notion"""
    
    database_config = {
        "parent": {"page_id": parent_page_id},
        "title": [{"text": {"content": "Trending Topics Database"}}],
        "properties": {
            "Keywords": {
                "title": {}
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "投資理財", "color": "blue"},
                        {"name": "數字貨幣投資", "color": "orange"},
                        {"name": "房地產投資", "color": "green"},
                        {"name": "退休規劃", "color": "purple"},
                        {"name": "風險管理", "color": "red"},
                        {"name": "個人財務", "color": "yellow"},
                        {"name": "經濟分析", "color": "gray"}
                    ]
                }
            },
            "Trend Score": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Topic Hash": {
                "rich_text": {}
            },
            "Context": {
                "rich_text": {}
            },
            "Mention Count": {
                "number": {
                    "format": "number"
                }
            },
            "Weekly Mentions": {
                "number": {
                    "format": "number"
                }
            },
            "Monthly Mentions": {
                "number": {
                    "format": "number"
                }
            },
            "Peak Score": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "Created At": {
                "date": {}
            },
            "Last Updated": {
                "date": {}
            },
            "Active": {
                "checkbox": {}
            }
        }
    }
    
    response = client.databases.create(**database_config)
    return response["id"]

def create_sources_database(client: Client, parent_page_id: str) -> str:
    """Create the data sources database in Notion"""
    
    database_config = {
        "parent": {"page_id": parent_page_id},
        "title": [{"text": {"content": "Data Sources Database"}}],
        "properties": {
            "Name": {
                "title": {}
            },
            "Source ID": {
                "rich_text": {}
            },
            "Source Type": {
                "select": {
                    "options": [
                        {"name": "web", "color": "blue"},
                        {"name": "api", "color": "green"},
                        {"name": "database", "color": "orange"},
                        {"name": "social", "color": "purple"},
                        {"name": "rss", "color": "yellow"}
                    ]
                }
            },
            "Base URL": {
                "url": {}
            },
            "Active": {
                "checkbox": {}
            },
            "Success Rate": {
                "number": {
                    "format": "percent"
                }
            },
            "Collection Count": {
                "number": {
                    "format": "number"
                }
            },
            "Last Collected": {
                "date": {}
            },
            "Configuration": {
                "rich_text": {}
            },
            "Created At": {
                "date": {}
            },
            "Updated At": {
                "date": {}
            }
        }
    }
    
    response = client.databases.create(**database_config)
    return response["id"]

def create_raw_content_database(client: Client, parent_page_id: str) -> str:
    """Create the raw content database in Notion"""
    
    database_config = {
        "parent": {"page_id": parent_page_id},
        "title": [{"text": {"content": "Raw Content Database"}}],
        "properties": {
            "Title": {
                "title": {}
            },
            "Content ID": {
                "rich_text": {}
            },
            "Source Name": {
                "rich_text": {}
            },
            "Source URL": {
                "url": {}
            },
            "Content Preview": {
                "rich_text": {}
            },
            "Processed": {
                "checkbox": {}
            },
            "Word Count": {
                "number": {
                    "format": "number"
                }
            },
            "Keywords": {
                "multi_select": {}
            },
            "Financial Terms": {
                "multi_select": {}
            },
            "Collected At": {
                "date": {}
            },
            "Content Hash": {
                "rich_text": {}
            }
        }
    }
    
    response = client.databases.create(**database_config)
    return response["id"]

def main():
    """Main function to create all Notion databases"""
    
    # Check environment variables
    notion_token = os.getenv('NOTION_TOKEN')
    parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    
    if not notion_token:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        print("Please set: export NOTION_TOKEN=your_token")
        return
    
    if not parent_page_id:
        print("❌ Error: NOTION_PARENT_PAGE_ID environment variable not set")
        print("Please set: export NOTION_PARENT_PAGE_ID=your_page_id")
        return
    
    try:
        # Initialize Notion client
        client = Client(auth=notion_token)
        
        print("🚀 Creating Notion databases for Financial Wisdom Platform...")
        print(f"📄 Parent page ID: {parent_page_id}")
        print("=" * 60)
        
        # Create databases
        print("1️⃣ Creating Articles database...")
        articles_db_id = create_articles_database(client, parent_page_id)
        print(f"   ✅ Articles DB created: {articles_db_id}")
        
        print("\n2️⃣ Creating Topics database...")
        topics_db_id = create_topics_database(client, parent_page_id)
        print(f"   ✅ Topics DB created: {topics_db_id}")
        
        print("\n3️⃣ Creating Data Sources database...")
        sources_db_id = create_sources_database(client, parent_page_id)
        print(f"   ✅ Sources DB created: {sources_db_id}")
        
        print("\n4️⃣ Creating Raw Content database...")
        raw_content_db_id = create_raw_content_database(client, parent_page_id)
        print(f"   ✅ Raw Content DB created: {raw_content_db_id}")
        
        print("\n" + "=" * 60)
        print("🎉 All databases created successfully!")
        print("\n📝 Environment variables to set:")
        print(f"export NOTION_ARTICLES_DB_ID=\"{articles_db_id}\"")
        print(f"export NOTION_TOPICS_DB_ID=\"{topics_db_id}\"")
        print(f"export NOTION_SOURCES_DB_ID=\"{sources_db_id}\"")
        print(f"export NOTION_RAW_CONTENT_DB_ID=\"{raw_content_db_id}\"")
        
        print("\n🔧 Add to your .env file:")
        print(f"NOTION_TOKEN={notion_token}")
        print(f"NOTION_ARTICLES_DB_ID={articles_db_id}")
        print(f"NOTION_TOPICS_DB_ID={topics_db_id}")
        print(f"NOTION_SOURCES_DB_ID={sources_db_id}")
        print(f"NOTION_RAW_CONTENT_DB_ID={raw_content_db_id}")
        
        print("\n✅ Setup complete! You can now use the Notion service.")
        
    except Exception as e:
        print(f"❌ Error creating databases: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your Notion token is valid")
        print("2. Ensure the integration has access to the parent page")
        print("3. Verify the parent page ID is correct")

if __name__ == "__main__":
    main()