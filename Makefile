.PHONY: up down logs dev-api dev-worker dev-web test lint typecheck check face-model

up:            ## Build and start the full stack (web :3000, api :8000)
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api worker

face-model:    ## Download the YuNet face detector for local (non-docker) runs
	mkdir -p apps/api/models
	curl -fsSL -o apps/api/models/face_detection_yunet_2023mar.onnx \
	  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

dev-api:
	cd apps/api && uv run fastapi dev app/main.py --port 8000

dev-worker:
	cd apps/api && uv run arq app.worker.WorkerSettings --watch app

dev-web:
	cd apps/web && npm run dev

test:
	cd apps/api && uv run pytest -q

lint:
	cd apps/api && uv run ruff check app tests && uv run ruff format --check app tests

typecheck:
	cd apps/api && uv run mypy app
	cd apps/web && npm run typecheck

check: lint test typecheck   ## Everything CI runs
	cd apps/web && npm run build
