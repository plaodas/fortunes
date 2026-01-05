docker compose exec frontend npm test -- --coverage --coverageDirectory=coverage --coverageReporters=text
docker compose exec backend bash -c "PYTHONPATH=/app pytest"
