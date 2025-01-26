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
    os.chdir(temp_dir)
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'audio.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            
            if not os.path.exists(audio_path):
                raise Exception("Failed to download audio")
            
            return info, audio_path, temp_dir
            
    except Exception as e:
        if os.path.exists(temp_dir):
            try:
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
            except:
                pass
        raise e

def transcribe_audio(audio_file_path):
    """Transcribe audio using Replicate's Whisper API."""
    if not os.environ.get("REPLICATE_API_TOKEN"):
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
    try:
        # Get request data
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'YouTube URL is required'}), 400
            
        youtube_url = data['url']
        
        # Process the video
        temp_dir = None
        original_dir = os.getcwd()
        
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
            # Cleanup
            os.chdir(original_dir)
            if temp_dir and os.path.exists(temp_dir):
                try:
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    os.rmdir(temp_dir)
                except:
                    pass
                    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)