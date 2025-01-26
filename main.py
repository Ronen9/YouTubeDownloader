import os
import yt_dlp
import tempfile
import time
import replicate
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Verify required environment variables
if not os.environ.get("REPLICATE_API_KEY"):
    print("WARNING: REPLICATE_API_KEY is not set. The API will not work without it.")

def format_hebrew_text(text):
    """Format Hebrew text with proper RTL alignment."""
    if not text:
        return text
    lines = text.split('\n')
    formatted_lines = [f'\u202B{line.strip()}\u202C' for line in lines if line.strip()]
    return '\n'.join(formatted_lines)

def download_youtube_audio(video_url):
    """Download audio from YouTube using yt-dlp."""
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'audio.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'no_check_certificates': True,
            'ignoreerrors': False,
            'cookiefile': None,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            
            if not os.path.exists(audio_path):
                raise Exception("Failed to download audio")
            
            return info, audio_path, temp_dir
            
    except Exception as e:
        raise Exception(f"YouTube download error: {str(e)}")
    finally:
        os.chdir(original_dir)

def cleanup_temp_dir(temp_dir):
    """Safely cleanup temporary directory."""
    if temp_dir and os.path.exists(temp_dir):
        try:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
            os.rmdir(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp directory: {str(e)}")

def transcribe_audio(audio_file_path):
    """Transcribe audio using Replicate's Whisper API."""
    if not os.environ.get("REPLICATE_API_KEY"):
        raise ValueError("REPLICATE_API_TOKEN environment variable is not set")
    
    try:
        model = replicate.models.get("openai/whisper")
        version = model.versions.get("91ee9c0c3df30478510ff8c8a3a545add1ad0259ad3a9f78fba57fbc05ee64f7")
        
        prediction = replicate.predictions.create(
            version=version,
            input={
                "audio": open(audio_file_path, "rb"),
                "model": "large-v2",
                "transcribe": True,
                "language": "he",
                "temperature": 0,
                "initial_prompt": "This is a Hebrew religious lecture",
                "condition_on_previous_text": True,
                "suppress_tokens": "-1",
                "word_timestamps": True
            }
        )
        
        while prediction.status not in ["succeeded", "failed"]:
            prediction.reload()
            time.sleep(2)
        
        if prediction.status == "succeeded":
            transcript = prediction.output.get('transcription', '')
            return transcript
        else:
            raise Exception(f"Prediction failed with status: {prediction.status}")

    except Exception as e:
        raise e

@app.route('/api/transcribe', methods=['POST'])
def transcribe_endpoint():
    """API endpoint for transcription."""
    if not os.environ.get("REPLICATE_API_KEY"):
        return jsonify({'error': 'REPLICATE_API_KEY environment variable is not set'}), 500
        
    try:
        # Get request data
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'YouTube URL is required'}), 400
            
        youtube_url = data['url']
        temp_dir = None
        
        try:
            # Download and transcribe
            info, audio_path, temp_dir = download_youtube_audio(youtube_url)
            transcript = transcribe_audio(audio_path)
            
            # Format results
            return jsonify({
                'status': 'success',
                'title': format_hebrew_text(info.get('title', '')),
                'transcript': format_hebrew_text(transcript)
            })
                    
        finally:
            # Cleanup using the dedicated function
            if temp_dir:
                cleanup_temp_dir(temp_dir)
                    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)