"""
Chat Agent - Natural language interface
You say: "write me a book about holi 10 pages with images"
Instead of: python cli.py build --topic "Holi festival" --pages 10

Parses natural language and calls BookBuilder automatically
"""

import re
from pathlib import Path

class ChatAgent:
    def __init__(self):
        from agents.book_builder import BookBuilder
        self.builder = BookBuilder()
    
    def parse(self, message: str):
        """
        Parse natural language into book params
        Examples:
          "write me a book about holi 10 pages with images" -> topic=Holi festival, pages=10
          "make a diwali book for kids 5 pages" -> topic=Diwali, pages=5
          "write a book about farm animals" -> topic=farm animals, pages=5 (default)
        """
        msg = message.lower()
        
        # Extract topic - after "about", "on", "for"
        topic = "Holi festival"  # default
        m = re.search(r'(?:about|on|for|of)\s+([a-zA-Z\s]+?)(?:\s+\d+\s*pages?|\s+with|\s+for kids|\s*$)', msg)
        if m:
            topic = m.group(1).strip()
            # Clean up common trailing words
            topic = re.sub(r'\b(a book|book|story)\b', '', topic).strip()
            if not topic:
                topic = "Holi festival"
        else:
            # Try to find known topics
            for known in ["holi", "diwali", "eid", "christmas", "farm", "jungle", "space", "ocean", "dinosaur"]:
                if known in msg:
                    topic = f"{known} festival" if known in ["holi", "diwali", "eid", "christmas"] else f"{known} animals" if known in ["farm", "jungle"] else known
                    break
        
        # Extract pages - "10 pages", "5 page", "10pg"
        pages = 10  # default
        m = re.search(r'(\d+)\s*(?:pages?|pg)', msg)
        if m:
            pages = int(m.group(1))
            pages = max(1, min(pages, 32))  # Clamp 1-32 for KDP
        
        # Extract title if quoted
        title = None
        m = re.search(r'["\'](.+?)["\']', message)
        if m and len(m.group(1)) > 3:
            title = m.group(1)
        
        # Extract audience
        audience = "children ages 4-8"
        if "toddler" in msg or "2-4" in msg:
            audience = "toddlers ages 2-4"
        elif "6-8" in msg or "7" in msg or "8" in msg:
            audience = "children ages 6-8"
        
        # Extract words per page if mentioned
        words = 120
        if "short" in msg:
            words = 60
        elif "long" in msg:
            words = 200
        
        return {
            "topic": topic.title(),
            "pages": pages,
            "title": title or f"My First {topic.title()}",
            "audience": audience,
            "words": words
        }
    
    def chat(self, message: str):
        """Main entry - you chat like here, it builds book"""
        print(f"\n💬 You said: '{message}'")
        params = self.parse(message)
        print(f"🤖 Parsed: topic='{params['topic']}', pages={params['pages']}, title='{params['title']}'")
        print(f"📚 Building your book now...\n")
        
        result = self.builder.build(
            topic=params["topic"],
            pages=params["pages"],
            title=params["title"],
            audience=params["audience"],
            word_count_per_page=params["words"]
        )
        return result

# For CLI usage
def cmd_chat(args):
    agent = ChatAgent()
    if args.message:
        agent.chat(args.message)
    else:
        # Interactive mode
        print("\n🤖 Book Factory Chat - Just say what you want!")
        print("Examples:")
        print("  'write me a book about holi 10 pages with images'")
        print("  'make a diwali book for kids 5 pages'")
        print("  'I want a farm animals book 8 pages'")
        print("Type 'quit' to exit\n")
        
        while True:
            try:
                msg = input("You: ").strip()
                if not msg:
                    continue
                if msg.lower() in ('quit', 'exit', 'q'):
                    print("Bye! 📚")
                    break
                agent.chat(msg)
                print("\n--- Ready for next book! ---\n")
            except KeyboardInterrupt:
                print("\nBye! 📚")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    agent = ChatAgent()
    if len(sys.argv) > 1:
        agent.chat(" ".join(sys.argv[1:]))
    else:
        cmd_chat(None)
