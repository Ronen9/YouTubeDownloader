import requests
import json

def test_api():
    url = "https://youtubedownloader-l7yy.onrender.com/api/transcribe"
    payload = {
        "url": "https://www.youtube.com/watch?v=S_ODdhITydg"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Sending request to:", url)
    print("With payload:", json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("\nStatus Code:", response.status_code)
        print("\nResponse Headers:", json.dumps(dict(response.headers), indent=2))
        print("\nResponse:")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print("Raw response:", response.text)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_api() 