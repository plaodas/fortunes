#!/bin/sh
echo "litellm is installed in this container."
echo "Run 'litellm --help' inside the container to see available commands."
echo "To keep the container running for interactive use, this entrypoint will sleep."
tail -f /dev/null
