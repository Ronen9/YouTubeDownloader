# YouTube Hebrew Transcription API

A REST API service that transcribes Hebrew audio from YouTube videos using Whisper AI.

## Setup

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API key:
```
REPLICATE_API_KEY=your_replicate_api_key
```

## API Usage

### Endpoint: POST /api/transcribe

Request:
```json
{
    "url": "https://www.youtube.com/watch?v=your_video_id"
}
```

Response:
```json
{
    "status": "success",
    "title": "Video Title",
    "transcript": "Hebrew transcript with RTL formatting"
}
```

## Deployment to Render.com

1. Create a new Web Service
2. Connect your repository
3. Set environment variables:
   - `REPLICATE_API_KEY`: Your Replicate API key
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn main:app`

## Make.com Integration

1. Create a new Custom App in Make.com
2. Set Base URL to your Render.com deployment URL
3. Create a new module:
   - Method: POST
   - Endpoint: /api/transcribe
   - Request Body: `{"url": "{{youtube_url}}"}` 