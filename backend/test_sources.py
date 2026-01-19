"""
Test script to verify sources are being generated and stored correctly
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from llm.orchestrator import LLMOrchestrator
from core.session_manager import SessionManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sources_generation():
    """Test if sources are generated and stored when retrieve_city_guidance is called"""
    
    print("=" * 80)
    print("TEST 1: Testing sources generation with retrieve_city_guidance")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = LLMOrchestrator()
    
    # Create a new session
    session_id = orchestrator.session_manager.create_session()
    print(f"\n✅ Created session: {session_id}")
    
    # Check initial state
    session = orchestrator.session_manager.get_session(session_id)
    initial_sources = session.get("sources", [])
    print(f"📋 Initial sources in session: {len(initial_sources)}")
    
    # Make a request that should trigger retrieve_city_guidance
    # This should generate sources
    test_query = "What are the best cultural attractions in Jaipur?"
    print(f"\n🔍 Sending query: '{test_query}'")
    print("   (This should trigger retrieve_city_guidance and generate sources)")
    
    try:
        result = orchestrator.process_user_request(
            user_message=test_query,
            session_id=session_id
        )
        
        print(f"\n✅ Request processed successfully")
        print(f"   Response length: {len(result.get('response', ''))} characters")
        print(f"   Tool calls made: {len(result.get('tool_calls', []))}")
        
        # Check if sources were stored
        session = orchestrator.session_manager.get_session(session_id)
        sources = session.get("sources", [])
        
        print(f"\n📚 Sources in session after request: {len(sources)}")
        
        if sources:
            print("\n✅ SOURCES FOUND! Structure:")
            for idx, source in enumerate(sources[:3], 1):  # Show first 3
                print(f"\n   Source {idx}:")
                print(f"      Keys: {list(source.keys())}")
                for key, value in source.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"      {key}: {value[:100]}...")
                    else:
                        print(f"      {key}: {value}")
        else:
            print("\n❌ NO SOURCES FOUND in session!")
            print("   This means retrieve_city_guidance may not have been called,")
            print("   or sources weren't stored properly.")
        
        return sources
        
    except Exception as e:
        print(f"\n❌ Error during request: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_sources_with_trip_planning():
    """Test if sources are generated during trip planning"""
    
    print("\n" + "=" * 80)
    print("TEST 2: Testing sources during trip planning")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = LLMOrchestrator()
    
    # Create a new session
    session_id = orchestrator.session_manager.create_session()
    print(f"\n✅ Created session: {session_id}")
    
    # Make a trip planning request
    test_query = "Plan a two day trip to Jaipur with moderate pace"
    print(f"\n🔍 Sending query: '{test_query}'")
    print("   (This should trigger search_pois and build_itinerary)")
    print("   Note: retrieve_city_guidance may NOT be called during trip planning")
    
    try:
        result = orchestrator.process_user_request(
            user_message=test_query,
            session_id=session_id
        )
        
        print(f"\n✅ Request processed successfully")
        print(f"   Response length: {len(result.get('response', ''))} characters")
        print(f"   Tool calls made: {len(result.get('tool_calls', []))}")
        
        # List tool calls
        tool_calls = result.get('tool_calls', [])
        if tool_calls:
            print(f"\n   Tool calls:")
            for tc in tool_calls:
                func_name = getattr(tc, 'function', {}).get('name', 'unknown') if hasattr(tc, 'function') else 'unknown'
                print(f"      - {func_name}")
        
        # Check if sources were stored
        session = orchestrator.session_manager.get_session(session_id)
        sources = session.get("sources", [])
        
        print(f"\n📚 Sources in session after trip planning: {len(sources)}")
        
        if sources:
            print("\n✅ SOURCES FOUND during trip planning!")
            for idx, source in enumerate(sources[:3], 1):
                print(f"\n   Source {idx}: {source.get('source', 'Unknown')}")
        else:
            print("\n⚠️  NO SOURCES FOUND during trip planning")
            print("   This is expected if retrieve_city_guidance wasn't called")
            print("   (Trip planning typically uses search_pois + build_itinerary)")
        
        return sources
        
    except Exception as e:
        print(f"\n❌ Error during request: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_voice_chat_sources_format():
    """Test the format transformation that happens in voice chat endpoint"""
    
    print("\n" + "=" * 80)
    print("TEST 3: Testing source format transformation (voice chat format)")
    print("=" * 80)
    
    # Simulate citation structure from retrieve_city_guidance
    sample_citations = [
        {
            "source": "Wikivoyage",
            "url": "https://en.wikivoyage.org/wiki/Jaipur",
            "section": "Understand",
            "section_anchor": "#Understand"
        },
        {
            "source": "Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Jaipur",
            "section": "History",
            "section_anchor": "#History"
        }
    ]
    
    print(f"\n📋 Sample citations (backend format): {len(sample_citations)}")
    for idx, citation in enumerate(sample_citations, 1):
        print(f"\n   Citation {idx}:")
        for key, value in citation.items():
            print(f"      {key}: {value}")
    
    # Transform to frontend format
    print(f"\n🔄 Transforming to frontend format...")
    sources = []
    seen_urls = set()
    
    for idx, citation in enumerate(sample_citations):
        url = citation.get("url", "")
        source_name = citation.get("source", "Unknown Source")
        
        # Skip duplicates by URL
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        
        # Transform to frontend format
        transformed_source = {
            "id": f"source_{idx}_{hash(url) if url else hash(source_name)}",
            "name": source_name,
            "type": citation.get("section", "General"),
            "url": url
        }
        sources.append(transformed_source)
    
    print(f"\n✅ Transformed sources (frontend format): {len(sources)}")
    for idx, source in enumerate(sources, 1):
        print(f"\n   Source {idx}:")
        for key, value in source.items():
            print(f"      {key}: {value}")
    
    return sources


def main():
    """Run all tests"""
    
    print("\n" + "=" * 80)
    print("SOURCES TEST SUITE")
    print("=" * 80)
    print("\nThis script tests:")
    print("1. Sources generation with retrieve_city_guidance")
    print("2. Sources during trip planning")
    print("3. Source format transformation")
    print("\n" + "=" * 80)
    
    # Test 1: Sources with retrieve_city_guidance
    sources1 = test_sources_generation()
    
    # Test 2: Sources during trip planning
    sources2 = test_sources_with_trip_planning()
    
    # Test 3: Format transformation
    sources3 = test_voice_chat_sources_format()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Test 1 (retrieve_city_guidance): {len(sources1)} sources")
    print(f"✅ Test 2 (trip planning): {len(sources2)} sources")
    print(f"✅ Test 3 (format transformation): {len(sources3)} sources")
    
    if sources1:
        print("\n✅ Sources ARE being generated when retrieve_city_guidance is called")
    else:
        print("\n❌ Sources are NOT being generated - check orchestrator logic")
    
    if sources2:
        print("✅ Sources found during trip planning (unexpected but good!)")
    else:
        print("⚠️  No sources during trip planning (expected - uses search_pois instead)")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
