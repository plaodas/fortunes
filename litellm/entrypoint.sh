#!/bin/sh
echo "litellm container starting"

PROVIDER=${LITELLM_PROVIDER:-}
echo "LITELLM_PROVIDER=${PROVIDER:-(not set)}"

case "$PROVIDER" in
	openai)
		echo "Provider: OpenAI"
		echo "Ensure OPENAI_API_KEY is set in the environment."
		;;
	gemini|google)
		echo "Provider: Gemini (Google)
		Ensure GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS is available to the container."
		;;
	deepseek)
		echo "Provider: DeepSeek"
		echo "Ensure DEEPSEEK_API_KEY is set in the environment."
		;;
	"")
		echo "No provider selected. Set LITELLM_PROVIDER=openai|gemini|deepseek"
		;;
	*)
		echo "Unknown provider: $PROVIDER"
		;;
esac

echo "To enter the container: docker exec -it fortunes_litellm sh"
echo "To run litellm CLI: litellm --help"

# keep the container running for interactive use
tail -f /dev/null
