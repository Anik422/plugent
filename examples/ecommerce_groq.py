"""
Example: E-commerce bot using Groq free tier + PostgreSQL
Supports Bengali language, ecommerce persona
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugent.db import SQLConnector, SchemaParser
from plugent.llm import get_llm
from plugent.core import ReactAgent, ConversationMemory
from plugent.knowledge import VectorStore, KnowledgeBuilder


def main():
    # === Configuration ===
    # Database connection (PostgreSQL)
    DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/ecommerce")

    # Groq API (free tier - no credit card needed)
    # Get free key: https://console.groq.com
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "gsk_your_key_here")
    MODEL = "llama-3.1-70b-versatile"  # Free tier model

    # Language setting (Bengali)
    LANGUAGE = "bn"
    COMPANY_CONFIG = {
        "name": "আমার দোকান",
        "description": "অনলাইন শপিং প্ল্যাটফর্ম",
        "domain": "ecommerce",
        "custom_instructions": """
        আপনি একটি বাংলা ই-কমার্স সহায়ক।
        - সংক্ষেপে উ ant দিন
        - টাকার পরিমাণ বাংলায় লিখুন
        - গ্রাহকদের সাথে বিনয়ী আচরণ করুন
        """
    }

    print("=== E-commerce Bot (Groq + PostgreSQL) ===\n")

    # 1. Connect to database
    print("১. ডাটাবেসে সংযোগ করা হচ্ছে...")
    db = SQLConnector()
    db.connect(DB_URL)

    # 2. Parse schema
    print("২. ডাটাবেস স্কিমা বিশ্লেষণ করা হচ্ছে...")
    parser = SchemaParser()
    schema = parser.parse(db)
    print(f"   → {len(schema.tables)}টি টেবিল পাওয়া গেছে")

    # 3. Setup LLM (Groq)
    print("৩. Groq LLM কনফিগার করা হচ্ছে...")
    llm = get_llm({
        "provider": "groq",
        "api_key": GROQ_API_KEY,
        "model": MODEL,
    })

    # 4. Setup knowledge base
    print("৪. জ্ঞান ভিত্তি তৈরি করা হচ্ছে...")
    vector_store = VectorStore(persist_dir="./chroma_ecommerce")
    vector_store.set_llm(llm)

    builder = KnowledgeBuilder(vector_store)
    doc_count = builder.from_database(db, "ecommerce_kb")
    print(f"   → {doc_count}টি ডকুমেন্ট সংরক্ষিত")

    # 5. Setup agent
    print("৫. এজেন্ট তৈরি করা হচ্ছে...")
    memory = ConversationMemory()

    agent = ReactAgent(
        llm=llm,
        skills=[],
        knowledge=vector_store,
        company_config=COMPANY_CONFIG,
    )

    # 6. Chat loop
    print("\n=== চ্যাট শুরু হয়েছে ===")
    print("'exit' লিখে প্রস্থান করুন\n")

    session_id = "ecommerce_session"
    while True:
        user_input = input("আপনি: ")
        if user_input.lower() in ["exit", "quit", "বের হই"]:
            print("ধন্যবাদ! ভালো থাকবেন!")
            break

        # Add to memory
        memory.add(session_id, "user", user_input)

        # Get history
        history = memory.get_recent(session_id, n=6)

        # Get response
        response = agent.think(user_input, history)

        # Show response
        print(f"বট: {response}\n")

        # Save to memory
        memory.add(session_id, "assistant", response)

    # Cleanup
    db.close()


if __name__ == "__main__":
    main()