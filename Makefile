IMAGE_NAME = vtt-service
TAG = 1.0

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

run:
	docker run -p 50052:50052 \
		-v C:\Users\mtse\from-mtsecapdev-github\nwpt-vtt-models\whisper_fine_tuning:/app/whisper_fine_tuning \
		-v C:\ProgramData\NwptRunData\VoiceRecordings:/app/voice_recordings \
		$(IMAGE_NAME):$(TAG)

stop:
	docker stop $$(docker ps -q --filter ancestor=$(IMAGE_NAME):$(TAG))