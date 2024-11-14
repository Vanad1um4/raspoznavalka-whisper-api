import os
from openai import OpenAI
import glob
import re
from pathlib import Path
from pydub import AudioSegment
import tempfile
import math
from env import OPENAI_API_KEY

# Максимальный размер чанка в байтах (20MB)
MAX_CHUNK_SIZE = 20 * 1024 * 1024


def get_next_file_number():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(current_dir, "results")
    existing_files = glob.glob(os.path.join(results_dir, "result*.txt"))
    if not existing_files:
        return "001"
    numbers = []
    for filename in existing_files:
        match = re.search(r'result(\d+)\.txt', filename)
        if match:
            numbers.append(int(match.group(1)))
    next_num = max(numbers) + 1 if numbers else 1
    return f"{next_num:03d}"


def is_supported_openai_format(filename):
    supported_formats = {'.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm'}
    file_extension = Path(filename).suffix.lower()
    return file_extension in supported_formats


def get_chunk_duration(file_size):
    """Вычисляет оптимальную длительность чанка в миллисекундах"""
    # Примерное соотношение: 1 минута MP3 ≈ 1MB (при битрейте 128kbps)
    # Используем запас в 20% для надежности
    chunk_minutes = (MAX_CHUNK_SIZE / 1024 / 1024) * 0.8
    return int(chunk_minutes * 60 * 1000)  # конвертируем в миллисекунды


def convert_to_mp3(input_path):
    """Конвертирует аудио файл в MP3 формат"""
    try:
        input_format = Path(input_path).suffix.lower().replace('.', '')
        print(f"Конвертация {input_format} в mp3...")
        audio = AudioSegment.from_file(input_path, format=input_format)

        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        mp3_path = temp_file.name
        temp_file.close()

        audio.export(mp3_path, format='mp3', bitrate='128k')
        print("Конвертация завершена успешно")
        return mp3_path
    except Exception as e:
        print(f"Ошибка при конвертации файла: {str(e)}")
        return None


def split_audio(audio_path):
    """Разделяет аудио файл на части подходящего размера"""
    print("Разделение аудио на части...")

    # Загружаем аудио
    audio = AudioSegment.from_file(audio_path)

    # Получаем размер файла
    file_size = os.path.getsize(audio_path)

    # Вычисляем длительность одного чанка
    chunk_duration = get_chunk_duration(file_size)

    # Разделяем на части
    chunks = []
    total_duration = len(audio)
    num_chunks = math.ceil(total_duration / chunk_duration)

    for i in range(num_chunks):
        start = i * chunk_duration
        end = min((i + 1) * chunk_duration, total_duration)

        # Создаем временный файл для чанка
        temp_chunk = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        chunk_path = temp_chunk.name
        temp_chunk.close()

        # Экспортируем чанк
        chunk_audio = audio[start:end]
        chunk_audio.export(chunk_path, format='mp3', bitrate='128k')
        chunks.append(chunk_path)

        print(f"Создан чанк {i+1}/{num_chunks}")

    return chunks


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Создана директория: {directory}")


def transcribe_chunk(client, chunk_path):
    """Транскрибирует один чанк аудио"""
    with open(chunk_path, "rb") as audio_file:
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcription.text
        except Exception as e:
            print(f"Ошибка при транскрибации чанка: {str(e)}")
            return None


def transcribe_audio(api_key, audio_filename):
    client = OpenAI(api_key=api_key)
    temp_files = []

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        audio_dir = os.path.join(current_dir, "audio")
        results_dir = os.path.join(current_dir, "results")
        audio_path = os.path.join(audio_dir, audio_filename)

        # Создаем необходимые директории
        ensure_directory_exists(audio_dir)
        ensure_directory_exists(results_dir)

        if not os.path.exists(audio_path):
            print(f"Ошибка: Файл {audio_filename} не найден в директории {audio_dir}")
            return None

        # Конвертируем в MP3 если нужно
        if not is_supported_openai_format(audio_filename):
            print("Формат файла не поддерживается OpenAI API. Выполняется конвертация в MP3...")
            converted_path = convert_to_mp3(audio_path)
            if converted_path is None:
                return None
            audio_path = converted_path
            temp_files.append(converted_path)

        # Разделяем аудио на части
        chunks = split_audio(audio_path)
        temp_files.extend(chunks)

        # Транскрибируем каждый чанк
        print("Начало транскрибации файла по частям...")
        transcriptions = []

        for i, chunk_path in enumerate(chunks, 1):
            print(f"Транскрибация части {i}/{len(chunks)}...")
            chunk_text = transcribe_chunk(client, chunk_path)
            if chunk_text is None:
                print(f"Пропуск части {i} из-за ошибки")
                continue
            transcriptions.append(chunk_text)

        # Объединяем результаты
        full_transcription = " ".join(transcriptions)

        # Сохраняем результат в папку results
        file_number = get_next_file_number()
        output_filename = f"result{file_number}.txt"
        output_path = os.path.join(results_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(full_transcription)

        print(f"Транскрипция успешно завершена и сохранена в файл: {output_path}")
        return output_filename

    except Exception as e:
        print(f"Произошла ошибка при транскрибации: {str(e)}")
        return None

    finally:
        # Удаляем все временные файлы
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Не удалось удалить временный файл {temp_file}: {str(e)}")


def list_audio_files():
    """Выводит список всех аудио файлов в директории audio"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(current_dir, "audio")

    if not os.path.exists(audio_dir):
        print("Директория 'audio' не найдена")
        return []

    supported_formats = {'.aac', '.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm'}

    audio_files = []
    for file in os.listdir(audio_dir):
        if Path(file).suffix.lower() in supported_formats:
            audio_files.append(file)

    return audio_files


if __name__ == "__main__":
    # Проверяем наличие необходимых библиотек
    try:
        import pydub
    except ImportError:
        print("Установка необходимых библиотек...")
        os.system('pip install pydub')
        print("Также может потребоваться установить ffmpeg:")
        print("Windows: choco install ffmpeg")
        print("MacOS: brew install ffmpeg")
        print("Linux: sudo apt-get install ffmpeg")
        exit()

    # Показываем список доступных аудио файлов
    audio_files = list_audio_files()
    if audio_files:
        print("Доступные аудио файлы в директории 'audio':")
        for i, file in enumerate(audio_files, 1):
            print(f"{i}. {file}")

        try:
            choice = int(input("\nВведите номер файла для транскрибации (или 0 для выхода): "))
            if choice == 0:
                print("Работа программы завершена")
                exit()
            if 1 <= choice <= len(audio_files):
                AUDIO_FILENAME = audio_files[choice - 1]
                transcribe_audio(OPENAI_API_KEY, AUDIO_FILENAME)
            else:
                print("Неверный номер файла")
        except ValueError:
            print("Необходимо ввести число")
    else:
        print("В директории 'audio' нет поддерживаемых аудио файлов")
        print("Поместите аудио файлы в директорию 'audio' и запустите скрипт снова")
        exit()
