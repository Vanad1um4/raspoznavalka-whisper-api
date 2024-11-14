# raspoznavalka-whisper-api

This tool automates the process of transcribing audio files using OpenAI's Whisper API. It supports various audio formats, handles large files by splitting them into chunks, and manages the transcription process efficiently.

## Features

- Supports multiple audio formats (mp3, wav, m4a, flac, etc.)
- Automatically converts unsupported formats to MP3
- Handles large files by splitting them into manageable chunks
- Processes files sequentially with progress tracking
- Saves transcriptions with automatic file numbering
- Supports folder organization for audio files and results

## Prerequisites

- Python 3.7 or higher
- FFmpeg (required for audio processing)
- OpenAI API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Vanad1um4/raspoznavalka-whisper-api.git
cd raspoznavalka-whisper-api
```

2. Install the required Python packages:

```bash
pip install openai pydub
```

3. Install FFmpeg:

- Windows (using Chocolatey):
  ```bash
  choco install ffmpeg
  ```
- MacOS (using Homebrew):
  ```bash
  brew install ffmpeg
  ```
- Linux:
  ```bash
  sudo apt-get install ffmpeg
  ```

4. Create an environment file `env.py` with your OpenAI API key:

```python
OPENAI_API_KEY = "your-api-key-here"
```

## Project Structure

```
.
├── audio/             # Directory for audio files
├── results/           # Directory for transcription results
├── env.py             # Environment configuration
└── start.py            # Main script
```

## Usage

1. Place your audio files in the `audio` directory.

2. Run the script:

```bash
python start.py
```

3. Select the file you want to transcribe from the displayed list.

4. The transcription will be saved in the `results` directory with an automatically generated filename (e.g., `result001.txt`).

## Supported Audio Formats

- FLAC (.flac)
- M4A (.m4a)
- MP3 (.mp3)
- MP4 (.mp4)
- MPEG (.mpeg)
- MPGA (.mpga)
- OGA (.oga)
- OGG (.ogg)
- WAV (.wav)
- WebM (.webm)

Note: Unsupported formats will be automatically converted to MP3 before processing.

## How It Works

1. The script first checks if the input format is supported by the OpenAI API
2. If needed, converts the audio to MP3 format
3. Splits large files into chunks (max 20MB each)
4. Transcribes each chunk using OpenAI's Whisper API
5. Combines all transcriptions into a single result file
6. Cleans up temporary files
7. Saves the result in the `results` directory

## Error Handling

- The script includes comprehensive error handling for file operations
- Temporary files are cleaned up even if errors occur
- Progress is displayed during long operations
- Clear error messages for common issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses OpenAI's Whisper API for transcription
- Uses pydub for audio processing
- Uses FFmpeg for audio conversion
