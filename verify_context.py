import os
import sys
from unittest.mock import MagicMock, patch

# Mock dependencies to avoid errors during import
sys.modules["elevenlabs"] = MagicMock()
sys.modules["twilio.twiml.voice_response"] = MagicMock()

# Mock google package and submodules
mock_google = MagicMock()
sys.modules["google"] = mock_google
mock_genai = MagicMock()
sys.modules["google.generativeai"] = mock_genai
mock_google.generativeai = mock_genai

# Ensure environment variables are set
os.environ["GEMINI_API_KEY"] = "test"
os.environ["ELEVENLABS_API_KEY"] = "test"

# Import main
import main

def test_context_integration():
    print("Testing Context Integration...")
    
    # 1. Verify Context Loading
    if hasattr(main, "CONTEXTO_ORISOD") and len(main.CONTEXTO_ORISOD) > 0:
        print("✅ CONTEXTO_ORISOD loaded successfully.")
    else:
        print("❌ CONTEXTO_ORISOD failed to load.")
        return

    # 2. Verify Prompt Construction (by running voice function)
    # We need to mock asyncio and request
    import asyncio
    from fastapi import Request

    async def run_voice_test():
        # Mock Request
        scope = {"type": "http", "query_string": b"attempt=1"}
        request = Request(scope)
        request._form = {
            "SpeechResult": "Qué beneficios tiene?",
            "Confidence": "0.9"
        }
        
        # Mock request.form() coroutine
        async def get_form():
            return request._form
        request.form = get_form

        # Mock generar_audio
        main.generar_audio = MagicMock()
        future = asyncio.Future()
        future.set_result("http://fake.url/audio.mp3")
        main.generar_audio.return_value = future

        # Mock GenerativeModel instance
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Respuesta simulada."
        mock_model_instance.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model_instance

        # Run voice
        try:
            await main.voice(request)
        except Exception as e:
            # Even if it fails later (e.g. returning Response), we check the mock call
            pass
        
        # Check if generate_content was called with context
        if mock_model_instance.generate_content.called:
            args, _ = mock_model_instance.generate_content.call_args
            prompt_used = args[0]
            if main.CONTEXTO_ORISOD in prompt_used:
                print("✅ Prompt contains the ORISOD context.")
            else:
                print("❌ Prompt does NOT contain the ORISOD context.")
                print(f"Prompt start: {prompt_used[:100]}")
        else:
            print("❌ generate_content was not called.")

    asyncio.run(run_voice_test())

if __name__ == "__main__":
    test_context_integration()
