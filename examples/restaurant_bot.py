"""
Example: Restaurant bot using Gemini free tier + MySQL
Restaurant use case with menu and reservation skills
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugent.db import SQLConnector, SchemaParser
from plugent.llm import get_llm
from plugent.core import ReactAgent, ConversationMemory
from plugent.knowledge import VectorStore, KnowledgeBuilder
from plugent import skill


# === Custom Restaurant Skills ===
@skill(name="show_menu", description="Show restaurant menu items")
def show_menu(category: str = "all") -> str:
    """Show menu items by category.

    Args:
        category: Menu category (appetizer, main, dessert, drinks, all)
    """
    menu = {
        "appetizer": [
            "🥗 সালাদ - ১৫০ টাকা",
            "🥟 পাস্তা - ২০০ টাকা",
            "🍟 ফ্রাই - ১২০ টাকা",
        ],
        "main": [
            "🍛 বিরিয়ানি - ৩৫০ টাকা",
            "🍜 কারি - ৪০০ টাকা",
            "🍝 পাস্তা - ৩০০ টাকা",
            "🍔 বার্গার - ২৫০ টাকা",
        ],
        "dessert": [
            "🍦 আইসক্রিম - ১০০ টাকা",
            "🍰 কেক - ১৫০ টাকা",
            "🥭 ফ্রুট স্যালাড - ১২০ টাকা",
        ],
        "drinks": [
            "🧃 জুস - ৮০ টাকা",
            "☕ চা - ৩০ টাকা",
            "🫖 কফি - ১০০ টাকা",
        ],
    }

    if category == "all":
        result = "📋 সম্পূর্ণ মেনু:\n\n"
        for cat, items in menu.items():
            result += f"**{cat.upper()}:**\n"
            result += "\n".join(f"  {item}" for item in items)
            result += "\n\n"
    else:
        result = f"📋 {category.upper()} মেনু:\n"
        items = menu.get(category, [])
        result += "\n".join(f"  {item}" for item in items) if items else "  এই ক্যাটাগরিতে কিছু নেই"

    return result


@skill(name="make_reservation", description="Book a table reservation")
def make_reservation(name: str, date: str, time: str, guests: int) -> str:
    """Make a table reservation.

    Args:
        name: Customer name
        date: Reservation date (YYYY-MM-DD)
        time: Reservation time
        guests: Number of guests
    """
    # In real app, save to database
    return f"""
✅ **রিজার্ভেশন নিশ্চিত!**

👤 নাম: {name}
📅 তারিখ: {date}
⏰ সময়: {time}
👥 গেস্ট: {জন}

রিজার্ভেশন নম্বর: RES-{hash(name + date) % 10000}

আপনাকে অপেক্ষা করার জন্য ধন্যবাদ! 🍽️
"""


@skill(name="check_availability", description="Check table availability")
def check_availability(date: str, time: str) -> str:
    """Check if tables are available.

    Args:
        date: Date to check (YYYY-MM-DD)
        time: Time to check
    """
    # Simulate availability check
    peak_hours = ["12:00", "13:00", "19:00", "20:00"]

    if time in peak_hours:
        return f"⚠️ {date} তারিখে {time} সম্ভবত ভরা। অন্য সময় চেষ্টা করুন।"

    return f"✅ {date} তারিখে {time} সময় টেবিল ফাঁকা আছে!"


def main():
    # === Configuration ===
    DB_URL = os.getenv("DATABASE_URL", "mysql://root:password@localhost/restaurant")

    # Gemini API (free tier)
    # Get key: https://aistudio.google.com/app/apikey
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_key_here")
    MODEL = "gemini-1.5-flash"

    COMPANY_CONFIG = {
        "name": "স্বাদ রেস্তোরাঁ",
        "description": "বাংলাদেশি ও আন্তর্জাতিক খাবার",
        "domain": "restaurant",
        "custom_instructions": """
        আপনি একটি রেস্তোরাঁ বট।
        - মেনু দেখান, অর্ডার নিন
        - রিজার্ভেশন করুন
        - সংক্ষেপে এবং বিনয়ী থাকুন
        """
    }

    print("=== Restaurant Bot (Gemini + MySQL) ===\n")

    # 1. Database
    print("১. MySQL-এ সংযোগ...")
    db = SQLConnector()
    try:
        db.connect(DB_URL)
        parser = SchemaParser()
        schema = parser.parse(db)
        print(f"   → {len(schema.tables)} টেবিল")
    except Exception as e:
        print(f"   → স্কিপ করা হচ্ছে: {e}")

    # 2. LLM
    print("২. Gemini কনফিগ...")
    try:
        llm = get_llm({
            "provider": "gemini",
            "api_key": GEMINI_API_KEY,
            "model": MODEL,
        })
        print("   → সংযুক্ত")
    except Exception as e:
        print(f"   → ত্রুটি: {e}")
        return

    # 3. Knowledge
    print("৩. মেনু তথ্য প্রস্তুত...")
    vector_store = VectorStore(persist_dir="./chroma_restaurant")
    vector_store.set_llm(llm)

    # Add menu to knowledge
    builder = KnowledgeBuilder(vector_store)
    builder.from_file("restaurant_menu.md", "menu_kb")

    # 4. Agent with skills
    print("৪. রেস্তোরাঁ স্কিল যোগ...")
    agent = ReactAgent(
        llm=llm,
        skills=[],
        knowledge=vector_store,
        company_config=COMPANY_CONFIG,
        custom_skills=[show_menu, make_reservation, check_availability],
    )
    print("   → show_menu, make_reservation, check_availability")

    # 5. Chat
    print("\n=== রেস্তোরাঁ চ্যাট ===\n")

    session_id = "restaurant_session"
    while True:
        user_input = input("আপনি: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Check for keywords to route to skills
        if "মেনু" in user_input or "menu" in user_input.lower():
            result = show_menu("all")
            print(f"বট: {result}\n")
        elif "রিজার্ভ" in user_input or "reserve" in user_input.lower():
            # Extract info and call skill
            result = make_reservation(
                name="গ্রাহক",
                date="2025-01-15",
                time="19:00",
                guests=4
            )
            print(f"বট: {result}\n")
        else:
            response = agent.think(user_input, [])
            print(f"বট: {response}\n")

    print("👋 ধন্যবাদ! আবার আসবেন!")


if __name__ == "__main__":
    main()