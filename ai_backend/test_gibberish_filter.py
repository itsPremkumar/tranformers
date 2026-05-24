import sys
import os

# Add parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.llm_factory import is_gibberish, LLMFactory

def test_gibberish_detector():
    print("Running gibberish detector tests...")
    
    # 1. Normal, valid English sentences
    assert not is_gibberish("Hello, I am a helpful robot. How can I help you today?"), "Valid English sentence flagged"
    assert not is_gibberish("I can see a red ball in the image."), "Valid English sentence flagged"
    assert not is_gibberish("The current Chief Minister of Tamil Nadu is M. K. Stalin."), "Valid English sentence flagged"
    
    # 2. Sentences with long valid URLs or paths should NOT be flagged
    assert not is_gibberish("You can visit https://www.google.com/search?q=query+here for details."), "URL flagged as gibberish"
    assert not is_gibberish("The file is located at C:\\Users\\User\\Documents\\file.txt"), "Path flagged as gibberish"
    
    # 3. Non-Latin content (e.g. Tamil, Hindi, Chinese) should not be flagged by vowel density
    assert not is_gibberish("செர்கேர்"), "Tamil text flagged as gibberish"
    
    # 4. Long words without spaces (gibberish/hallucinations)
    assert is_gibberish("idskfjfhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskf"), "Long gibberish word not flagged"
    assert is_gibberish("This is a verylongcontinuousstringofcharactersthatshouldbeflaggedasgibberish."), "Long word not flagged"
    
    # 5. Repeating substrings
    assert is_gibberish("jhskfjhskfjhskf"), "Repeating substring not flagged"
    assert is_gibberish("abcabcabc"), "Repeating short substring not flagged"
    assert is_gibberish("SAY:jhskfjhskfjhskf"), "SAY command with repeating substring not flagged"
    
    # 6. Low vowel density for Latin text
    assert is_gibberish("bcdfghjklmnpqrstvwxz"), "No vowels string not flagged"
    assert is_gibberish("thswrdsdntnvywls"), "Low vowel density string not flagged"

    print("Gibberish detector tests PASSED!")

def test_llm_factory_formatting():
    print("Running LLMFactory format_response tests...")
    
    # Mocking manager for LLMFactory initialization
    class MockManager:
        pass
    
    factory = LLMFactory(MockManager())
    
    # Test valid JSON list formatting
    valid_json = '["SAY:Hello world", "CMD:FORWARD"]'
    formatted = factory.format_response(valid_json)
    assert formatted == valid_json, f"Failed to format valid JSON list: {formatted}"
    
    # Test valid text (should wrap in SAY)
    valid_text = "I am a robot"
    formatted = factory.format_response(valid_text)
    assert "SAY:I am a robot" in formatted, f"Failed to wrap valid text: {formatted}"
    
    # Test gibberish input (should raise ValueError)
    try:
        factory.format_response("idskfjfhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskfjhskf")
        assert False, "Should have raised ValueError on gibberish"
    except ValueError as e:
        print(f"Correctly caught expected error: {e}")
        
    try:
        factory.format_response('["SAY:jhskfjhskfjhskf"]')
        assert False, "Should have raised ValueError on gibberish inside JSON"
    except ValueError as e:
        print(f"Correctly caught expected error: {e}")

    print("LLMFactory format_response tests PASSED!")

if __name__ == "__main__":
    test_gibberish_detector()
    test_llm_factory_formatting()
    print("All local unit tests completed successfully.")
