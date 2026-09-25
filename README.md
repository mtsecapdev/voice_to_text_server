# NWPT Voice-to-Text Server

A gRPC server that transcribes speech audio files using a fine-tuned Whisper model. Built for the NWPT/AawSmartTrainer Unity training simulation — the Unity client sends a path to a `.wav` recording, and the server returns the transcription.

## How It Works

The server exposes a single gRPC endpoint defined in `protos/voice_to_text.proto`:

```
service VoiceToTextHandler {
  rpc TranscribeVoice (VttRequest) returns (VttResponse);
}
```

- **`VttRequest`** contains `audio_file_path` — the path to a `.wav` file on disk.
- **`VttResponse`** contains `transcription` — the transcribed text.

The Unity client calls `TranscribeVoice` after a player finishes speaking. The server uses `faster-whisper` with a fine-tuned Whisper Medium model for inference, running on GPU via CUDA.

### Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point — configures logging, starts the gRPC server |
| `src/whisper_grpc_server.py` | gRPC server implementation — listens on port 50052 |
| `src/whisper_transcriber.py` | Whisper inference logic — loads model, runs transcription |
| `src/voice_to_text_pb2.py` | Generated protobuf message classes (do not edit) |
| `src/voice_to_text_pb2_grpc.py` | Generated gRPC service classes (do not edit) |
| `protos/voice_to_text.proto` | The gRPC contract (source of truth) |
| `test-wav/vtt_server_test_do_not_delete.wav` | Test audio used for server health checks from the Unity client |

### Model Files (Not in Repo)

The fine-tuned Whisper model and processor are **not included in this repository** due to file size. They must be downloaded separately and placed at:

```
whisper_fine_tuning/
├── whisper_medium_model_AawMaster/
│   ├── model.safetensors
│   ├── config.json
│   └── ... (tokenizer, vocab, etc.)
└── whisper_medium_processor_AawMaster/
    ├── preprocessor_config.json
    └── ... (tokenizer, vocab, etc.)
```

Get these from the stetcapdev Google Drive.

## Running Locally (Without Docker)

### Prerequisites

- **Python 3.12** (not 3.14 — `ctranslate2` does not have wheels for 3.14)
- **NVIDIA GPU** with drivers installed
- **CUDA 12.8** and **cuDNN 9** (required by `torch==2.8.0+cu128`)
- **ffmpeg** installed and on PATH

### Setup

```bash
git clone <repo-url>
cd nwpt-vtt-server

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu128
```

The `--extra-index-url` is required because the CUDA 12.8 builds of PyTorch are hosted on PyTorch's own package index, not on PyPI.

### Download the Model

Place the Whisper model and processor folders in `whisper_fine_tuning/` as described above.

### Run

```bash
python src/main.py
```

The server starts on port **50052**. Logs go to both the console and `whisper_server_log.log`.

## Docker

### Prerequisites

- **NVIDIA driver** installed on the host
- **Docker Desktop** with WSL2 backend (handles NVIDIA Container Toolkit integration)

### Build

```bash
make build
```

Or manually:

```bash
docker build -t vtt-service:1.0 .
```

### Run

```bash
make run
```

Or manually:

```bash
docker run --rm -p 50052:50052 --gpus device=0 \
    -v /path/to/whisper_fine_tuning:/app/whisper_fine_tuning \
    -v /path/to/VoiceRecordings:/app/voice_recordings \
    vtt-service:1.0
```

**Two volume mounts are required:**

| Mount | Purpose |
|-------|---------|
| `whisper_fine_tuning` → `/app/whisper_fine_tuning` | The fine-tuned Whisper model and processor |
| `VoiceRecordings` → `/app/voice_recordings` | Directory where Unity saves player voice recordings |

Update the paths in the `Makefile` to match your machine before running `make run`.

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Builds the Docker image as `vtt-service:1.0` |
| `make run` | Runs the container with GPU access and volume mounts |
| `make stop` | Stops any running container of this image |

## Unity Client Integration

The Unity client connects to `localhost:50052` using gRPC. The client has a hardcoded path replacement that converts Windows recording paths to container paths before making gRPC calls:

```csharp
string containerPath = wavFilePath.Replace(
    @"C:\ProgramData\NwptRunData\VoiceRecordings",
    "/app/voice_recordings"
).Replace('\\', '/');
```

**This means the server must run as a Docker container** — the path translation assumes a Linux filesystem with the volume mounted at `/app/voice_recordings`. Running the server locally without Docker will fail because the translated path won't resolve on Windows.

**Future improvement:** Send the audio bytes directly in the gRPC request instead of a file path. This would decouple the server from the client's filesystem and remove the Docker requirement.

## Gotchas

- **Python 3.12 only.** `ctranslate2==4.4.0` does not publish wheels for Python 3.14. If you're on 3.14, the pip install will fail.
- **PyTorch CUDA wheels.** `pip install -r requirements.txt` alone will fail because `torch==2.8.0+cu128` is not on PyPI. You must include `--extra-index-url https://download.pytorch.org/whl/cu128`.
- **Forward slashes in paths.** The Python code uses forward slashes for file paths. This matters inside the Docker container (Linux). If you see a HuggingFace repo ID validation error, check for backslashes.
- **`--break-system-packages` in Docker.** The Dockerfile uses this flag because Ubuntu 24.04 enforces PEP 668, which blocks pip installs into the system Python. This is safe inside a container since there's no system to break.
- **Volume mount paths in Makefile.** The Makefile has hardcoded Windows paths for the volume mounts. Update these to match your machine before running `make run`.