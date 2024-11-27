# Audio Transcription Tool

Simple command-line tool to transcribe audio files using OpenAI's Whisper API.

## Features

- Supports multiple audio formats (.mp3, .wav, .flac, .m4a, etc.)
- Automatically converts unsupported formats to MP3
- Handles large files by splitting them into chunks
- Preserves previous transcriptions by adding version numbers
- Creates organized directory structure for audio files and results

## Setup

1. Clone this repository
2. Copy `env.py.example` to `env.py`
3. Add your OpenAI API key to `env.py`
4. Install required packages:

```bash
pip install openai pydub
```

5. Install ffmpeg:
   - Windows: `choco install ffmpeg`
   - MacOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

## Usage

1. Place your audio files in the `audio` directory
2. Run the script:

```bash
python start.py
```

3. Choose the file number you want to transcribe from the list
4. Wait for transcription to complete
5. Find results in the `results` directory

### Results

Transcriptions are saved as text files in the `results` directory:

- First transcription: `filename.txt`
- Subsequent transcriptions: `filename_v1.txt`, `filename_v2.txt`, etc.

## Supported Formats

Direct support for:

- .flac
- .m4a
- .mp3
- .mp4
- .mpeg
- .mpga
- .oga
- .ogg
- .wav
- .webm

Other formats will be automatically converted to MP3.
