import os
from openai import OpenAI
import glob
import re
from pathlib import Path
from pydub import AudioSegment
import tempfile
import math
from env import MAX_CHUNK_SIZE_MB, OPENAI_API_KEY


def get_output_filename(audio_filename):
    """Generate output filename based on input audio filename"""
    base_name = Path(audio_filename).stem
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(current_dir, "results")

    version = 0
    while True:
        filename = f"{base_name}.txt" if version == 0 else f"{base_name}_v{version}.txt"
        if not os.path.exists(os.path.join(results_dir, filename)):
            return filename
        version += 1


def is_supported_openai_format(filename):
    """Check if the file format is directly supported by OpenAI's Whisper API"""
    supported_formats = {'.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm'}
    file_extension = Path(filename).suffix.lower()
    return file_extension in supported_formats


def calculate_optimal_chunk_duration(file_size):
    """Calculate optimal chunk duration based on file size and API limits

    Uses approximate ratio: 1 minute of MP3 ≈ 1MB at 128kbps
    Includes 20% safety margin for overhead
    """
    chunk_minutes = (MAX_CHUNK_SIZE_MB / 1024 / 1024) * 0.8
    return int(chunk_minutes * 60 * 1000)  # Convert to milliseconds


def convert_audio_to_mp3(input_path):
    """Convert any audio format to MP3 for compatibility"""
    try:
        input_format = Path(input_path).suffix.lower().replace('.', '')
        print(f"Converting {input_format} to mp3...")
        audio = AudioSegment.from_file(input_path, format=input_format)

        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        mp3_path = temp_file.name
        temp_file.close()

        audio.export(mp3_path, format='mp3', bitrate='128k')
        print("Conversion completed successfully")
        return mp3_path
    except Exception as e:
        print(f"Error during file conversion: {str(e)}")
        return None


def split_audio_into_chunks(audio_path):
    """Split large audio files into chunks that meet API size limits"""
    print("Splitting audio into chunks...")

    audio = AudioSegment.from_file(audio_path)
    file_size = os.path.getsize(audio_path)
    chunk_duration = calculate_optimal_chunk_duration(file_size)

    chunks = []
    total_duration = len(audio)
    num_chunks = math.ceil(total_duration / chunk_duration)

    for i in range(num_chunks):
        start = i * chunk_duration
        end = min((i + 1) * chunk_duration, total_duration)

        temp_chunk = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        chunk_path = temp_chunk.name
        temp_chunk.close()

        chunk_audio = audio[start:end]
        chunk_audio.export(chunk_path, format='mp3', bitrate='128k')
        chunks.append(chunk_path)

        print(f"Created chunk {i+1}/{num_chunks}")

    return chunks


def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")


def transcribe_audio_chunk(client, chunk_path):
    """Transcribe a single audio chunk using OpenAI's Whisper API"""
    with open(chunk_path, "rb") as audio_file:
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcription.text
        except Exception as e:
            print(f"Error transcribing chunk: {str(e)}")
            return None


def process_audio_file(api_key, audio_filename):
    """Main function to handle the complete audio transcription process"""
    client = OpenAI(api_key=api_key)
    temp_files = []

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        audio_dir = os.path.join(current_dir, "audio")
        results_dir = os.path.join(current_dir, "results")
        audio_path = os.path.join(audio_dir, audio_filename)

        ensure_directory_exists(audio_dir)
        ensure_directory_exists(results_dir)

        if not os.path.exists(audio_path):
            print(f"Error: File {audio_filename} not found in {audio_dir}")
            return None

        if not is_supported_openai_format(audio_filename):
            print("File format not supported by OpenAI API. Converting to MP3...")
            converted_path = convert_audio_to_mp3(audio_path)
            if converted_path is None:
                return None
            audio_path = converted_path
            temp_files.append(converted_path)

        chunks = split_audio_into_chunks(audio_path)
        temp_files.extend(chunks)

        print("Starting file transcription...")
        transcriptions = []

        for i, chunk_path in enumerate(chunks, 1):
            print(f"Transcribing part {i}/{len(chunks)}...")
            chunk_text = transcribe_audio_chunk(client, chunk_path)
            if chunk_text is None:
                print(f"Skipping part {i} due to error")
                continue
            transcriptions.append(chunk_text)

        full_transcription = " ".join(transcriptions)
        output_filename = get_output_filename(audio_filename)
        output_path = os.path.join(results_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(full_transcription)

        print(f"Transcription completed and saved to: {output_path}")
        return output_filename

    except Exception as e:
        print(f"Transcription error occurred: {str(e)}")
        return None

    finally:
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Failed to remove temporary file {temp_file}: {str(e)}")


def get_available_audio_files():
    """List all supported audio files in the audio directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(current_dir, "audio")

    if not os.path.exists(audio_dir):
        print("'audio' directory not found")
        return []

    supported_formats = {'.aac', '.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm'}

    audio_files = []
    for file in os.listdir(audio_dir):
        if Path(file).suffix.lower() in supported_formats:
            audio_files.append(file)

    return audio_files


if __name__ == "__main__":
    try:
        import pydub
    except ImportError:
        print("Installing required packages...")
        os.system('pip install pydub')
        print("You may also need to install ffmpeg:")
        print("Windows: choco install ffmpeg")
        print("MacOS: brew install ffmpeg")
        print("Linux: sudo apt-get install ffmpeg")
        exit()

    audio_files = get_available_audio_files()
    if audio_files:
        print("Available audio files in 'audio' directory:")
        for i, file in enumerate(audio_files, 1):
            print(f"{i}. {file}")

        try:
            choice = int(input("\nEnter file number to transcribe (or 0 to exit): "))
            if choice == 0:
                print("Program terminated")
                exit()
            if 1 <= choice <= len(audio_files):
                AUDIO_FILENAME = audio_files[choice - 1]
                process_audio_file(OPENAI_API_KEY, AUDIO_FILENAME)
            else:
                print("Invalid file number")
        except ValueError:
            print("Please enter a valid number")
    else:
        print("No supported audio files found in 'audio' directory")
        print("Place audio files in the 'audio' directory and run the script again")
        exit()
