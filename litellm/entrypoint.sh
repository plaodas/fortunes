#!/bin/sh
set -e
echo "litellm container starting"

PROVIDER=${LITELLM_PROVIDER:-}
echo "LITELLM_PROVIDER=${PROVIDER:-(not set)}"

case "$PROVIDER" in
	openai)
		echo "Provider: OpenAI"
		echo "Ensure OPENAI_API_KEY is set in the environment."
		;;
	gemini|google)
		echo "Provider: Gemini (Google)"
		echo "Ensure GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS is available to the container."
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

# Auto-start behavior:
# - Set LITELLM_AUTOSTART=1 (or true) to attempt to run an automatic start command.
# - Provide LITELLM_START_CMD to define the exact command to run (e.g. "litellm serve --host 0.0.0.0 --port 8080").
# If no autostart is requested, the container will keep running for interactive use.

AUTOSTART=${LITELLM_AUTOSTART:-0}
START_CMD=${LITELLM_START_CMD:-}

if [ "${AUTOSTART}" = "1" ] || [ "${AUTOSTART}" = "true" ] || [ "${AUTOSTART}" = "True" ]; then
	if [ -z "${START_CMD}" ]; then
		echo "LITELLM_AUTOSTART is set but LITELLM_START_CMD is empty. Skipping auto-start."
	else
		echo "Starting litellm with: ${START_CMD}"
		# exec replaces the shell with the command so Docker receives its signals
		exec sh -c "${START_CMD}"
	fi
fi

# keep the container running for interactive use
tail -f /dev/null
