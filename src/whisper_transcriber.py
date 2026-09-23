# This class allows the server to instantiate and make the transcription
# I added alot of logger.info because want to provide some feedback on those areas where there is some perceived stalling

import sys
import os
import numpy as np
from pydub import AudioSegment
import torch
import logging

logger = logging.getLogger(__name__)

logger.info("Starting Voice-To-Text Server v27012026")
logger.info("Importing ML tools..")
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from number_parser import parse

MODEL_PATH = "whisper_fine_tuning/whisper_medium_model_AawMaster"
PROCESSOR_PATH = "whisper_fine_tuning/whisper_medium_processor_AawMaster"

model_path_no_ft = "whisper_downloads/whisper_medium_model"
processor_path_no_ft = "whisper_downloads/whisper_medium_processor"

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32


# Abstract out this method to not overcrowd the WhisperTranscriber class
def generate_samples_from_wav(wav_file_path):
    audio = AudioSegment.from_file(wav_file_path)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
    return samples


# Instantiate this class to transcribe using whisper model
class WhisperTranscriber:
    # Constructor will instantiate the model and processor
    def __init__(self):
        model_path = MODEL_PATH
        processor_path = PROCESSOR_PATH
        logger.info("Loading VTT model. Standby...")
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_path)
        self.model.to(device)
        self.processor = AutoProcessor.from_pretrained(processor_path)
        logger.info("Model successfully loaded")

    def transcribe_from_wav(self, wav_file_path):
        logger.info(f"Transcription request received, transcribing {wav_file_path}")
        samples = generate_samples_from_wav(wav_file_path)
        inputs = self.processor(
            samples,
            return_tensors="pt",
            truncation=False,
            padding="longest",
            return_attention_mask=True,
            sampling_rate=16_000,
        )
        inputs = inputs.to(device, torch.float32)

        # Uncomment this in case there is EOS token id problem again. The issue was because in the fine tuned model's generation_config.json, "eos_token_id": 50257, instead of saving as an int, was saved as a list i.e. [50257]. Can't find the root cause but changing this to plain int 50257 seemed to fix the issue
        # print(
        #     "EOS token id:",
        #     self.model.generation_config.eos_token_id,
        #     type(self.model.generation_config.eos_token_id),
        # )

        generated_ids = self.model.generate(
            **inputs,
            return_timestamps=True,
            language="en",
            condition_on_prev_tokens=True,
        )

        transcription = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )
        parsedNumbers = parse(transcription[0])
        logger.info("Transcription completed")
        return parsedNumbers
