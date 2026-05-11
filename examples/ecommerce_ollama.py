"""
Example: E-commerce bot using Ollama (local/offline) + SQLite
Private mode - no internet required after model download
Includes custom skill for delivery area checking
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugent.db import SQLConnector, SchemaParser
from plugent.llm import get_llm
from plugent.core import ReactAgent, ConversationMemory
from plugent.knowledge import VectorStore, KnowledgeBuilder
from plugent import skill


# === Custom Skills ===
@skill(name="check_delivery", description="Check if we deliver to a specific area")
def check_delivery(area: str) -> str:
    """Check delivery availability to an area.

    Args:
        area: The area/distance to check.
    """
    # Delivery areas in Bangladesh
    delivery_areas = {
        "ঢাকা": "হ্যাঁ, ঢাকায় ফ্রি ডেলিভারি!",
        "চট্টগ্রাম": "হ্যাঁ, চট্টগ্রামে ডেলিভারি আছে (১০০ টাকা)",
        "সিলেট": "হ্যাঁ, সিলেটে ডেলিভারি আছে (১৫০ টাকা)",
        "বরিশাল": "হ্যাঁ, বরিশালে ডেলিভারি আছে (২০০ টাকা)",
        "খুলনা": "হ্যাঁ, খুলনায় ডেলিভারি আছে (২০০ টাকা)",
        "রাজশাহী": "হ্যাঁ, রাজশাহীতে ডেলিভারি আছে (১৫০ টাকা)",
    }

    # Check for matching area
    area_lower = area.lower()
    for known_area, message in delivery_areas.items():
        if known_area in area_lower or area_lower in known_area.lower():
            return f"📦 ডেলিভারি তথ্য: {message}"

    return "😕 দুঃখিত, এই এলাকায় এখনো ডেলিভারি সেবা চালু হয়নি। শীঘ্রই আসবে!"


@skill(name="calculate_shipping", description="Calculate shipping cost based on weight and area")
def calculate_shipping(weight: float, area: str) -> str:
    """Calculate shipping cost.

    Args:
        weight: Weight in kg.
        area: Destination area.
    """
    base_rate = 50  # Base shipping
    weight_rate = 20  # Per kg
    area_extra = {
        "ঢাকা": 0,
        "চট্টগ্রাম": 100,
        "সিলেট": 150,
        "বরিশাল": 200,
        "খুলনা": 200,
        "রাজশাহী": 150,
    }

    extra = area_extra.get(area, 300)
    total = base_rate + (weight * weight_rate) + extra

    return f"🚚 শিপিং খরচ: {total} টাকা (ওজন: {weight} কেজি, এলাকা: {area})"


def main():
    # === Configuration ===
    # Local SQLite (no external database needed)
    DB_PATH = os.getenv("DB_PATH", "./ecommerce.db")
    DB_URL = f"sqlite:///{DB_PATH}"

    # Ollama (local) - NO API KEY NEEDED
    # Make sure Ollama is running: ollama serve
    # Download model: ollama pull llama3.1
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

    # Company config
    COMPANY_CONFIG = {
        "name": "স্থানীয় দোকান",
        "description": "অফলাইন ই-কমার্স প্ল্যাটফর্ম",
        "domain": "ecommerce",
        "custom_instructions": """
        আপনি একটি স্থানীয় বাংলা দোকানের বট।
        - সহজ ভাষায় কথা বলুন
        - দ্রুত উ ant দিন
        - স্থানীয় ব্যবসায়ীদের সাহায্য করুন
        """
    }

    print("=== E-commerce Bot (Ollama - Offline Mode) ===")
    print("🔒 ব্যক্তিগত মোড: সম্পূর্ণ অফলাইন\n")

    # 1. Connect to SQLite
    print("১. SQLite ডাটাবেসে সংযোগ...")
    db = SQLConnector()
    try:
        db.connect(DB_URL)
        print("   → সংযুক্ত")
    except Exception as e:
        print(f"   → নতুন ডাটাবেস তৈরি করা হচ্ছে: {e}")
        db.connect(DB_URL)

    # 2. Parse schema (or create sample)
    parser = SchemaParser()
    try:
        schema = parser.parse(db)
        print(f"   → {len(schema.tables)}টি টেবিল")
    except:
        print("   → কোনো টেবিল নেই, স্কিমা তৈরি করুন")

    # 3. Setup Ollama
    print("২. Ollama কনফিগার করা হচ্ছে...")
    try:
        llm = get_llm({
            "provider": "ollama",
            "model": MODEL,
            "base_url": OLLAMA_BASE_URL,
        })
        print(f"   → {MODEL} সংযুক্ত (অফলাইন)")
    except Exception as e:
        print(f"   → ত্রুটি: {e}")
        print("   → নির্দেশনা: ollama serve চালু করুন")
        return

    # 4. Setup vector store (local)
    print("৩. স্থানীয় ভেক্টর স্টোর তৈরি...")
    vector_store = VectorStore(persist_dir="./chroma_local")
    vector_store.set_llm(llm)

    # 5. Setup agent with custom skills
    print("৪. কাস্টম স্কিল যোগ করা হচ্ছে...")
    agent = ReactAgent(
        llm=llm,
        skills=[],  # Auto-generated skills (none without DB)
        knowledge=vector_store,
        company_config=COMPANY_CONFIG,
        custom_skills=[check_delivery, calculate_shipping],  # Custom skills!
    )
    print("   → check_delivery, calculate_shipping")

    # 6. Chat
    print("\n=== চ্যাট শুরু ===")
    print("'exit' লিখে বের হন\n")

    session_id = "offline_session"
    while True:
        user_input = input("আপনি: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Direct skill check
        if "ডেলিভারি" in user_input or "delivery" in user_input.lower():
            # Try to extract area
            areas = ["ঢাকা", "চট্টগ্রাম", "সিলেট", "বরিশাল", "খুলনা", "রাজশাহী"]
            for area in areas:
                if area in user_input:
                    result = check_delivery(area)
                    print(f"বট: {result}\n")
                    break
            else:
                # Use agent for general query
                response = agent.think(user_input, [])
                print(f"বট: {response}\n")
        else:
            response = agent.think(user_input, [])
            print(f"বট: {response}\n")

    db.close()
    print("👋 বের হয়ে গেছি!")


if __name__ == "__main__":
    main()