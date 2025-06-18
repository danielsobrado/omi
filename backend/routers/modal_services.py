import json
import os
import uuid
from collections import defaultdict
from typing import List, Optional
from functools import lru_cache

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

# Conditional imports for ML dependencies
try:
    import torch
    from pydub import AudioSegment
    from speechbrain.inference.speaker import SpeakerRecognition
    from pyannote.audio import Pipeline
    ML_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML dependencies not available: {e}")
    print("Speech profile and VAD endpoints will not work until dependencies are installed.")
    ML_DEPENDENCIES_AVAILABLE = False
    # Create mock classes to prevent import errors
    torch = None
    AudioSegment = None
    SpeakerRecognition = None
    Pipeline = None

from utils.stt.speech_profile import get_speech_profile_expanded, get_people_with_speech_samples

router = APIRouter()

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class ResponseItem(BaseModel):
    is_user: bool
    person_id: Optional[str] = None

# --- Lazy-loaded GPU/Model Initialization ---
@lru_cache(maxsize=1)
def get_speech_model():
    """This function loads the speech model on its first call and caches the result."""
    if not ML_DEPENDENCIES_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="ML dependencies not installed. Please install: pip install torch speechbrain"
        )
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Loading speech profile model on: {device}")
    model = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb",
        run_opts={"device": device},
    )
    print("Speech profile model loaded.")
    return model

@lru_cache(maxsize=1)
def get_vad_model():
    """This function loads the VAD model on its first call and caches the result."""
    if not ML_DEPENDENCIES_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="ML dependencies not installed. Please install: pip install pyannote.audio torch"
        )
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading VAD model on: {device}")
    vad = Pipeline.from_pretrained(
        "pyannote/voice-activity-detection",
        use_auth_token=os.getenv('HUGGINGFACE_TOKEN')
    ).to(device)
    print("VAD model loaded.")
    return vad

def sample_same_speaker_as_segment(sample_audio: str, segment: str) -> float:
    model = get_speech_model()  # Load the model when needed
    try:
        score, prediction = model.verify_files(sample_audio, segment)
        return float(score[0]) if bool(prediction[0]) else 0
    except Exception as e:
        print(f"Error in sample_same_speaker_as_segment: {e}")
        return 0

def classify_segments(
        audio_file_path: str, profile_path: str, people: List[dict], segments: List[TranscriptSegment]
):
    if not ML_DEPENDENCIES_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="ML dependencies not installed. Cannot process audio segments."
        )
        
    matches = [{'is_user': False, 'person_id': None}] * len(segments)
    if not profile_path:
        return matches

    print('Duration:', AudioSegment.from_wav(audio_file_path).duration_seconds)
    file_name = os.path.basename(audio_file_path)

    for i, segment in enumerate(segments):
        duration = segment.end - segment.start
        by_chunk_matches = defaultdict(float)

        for j in range(0, int(duration), 30):
            start = segment.start + j
            end = min(segment.end, start + 30)
            temporal_file = f"_temp/{file_name}_{start}_{end}.wav"
            AudioSegment.from_wav(audio_file_path)[start * 1000:end * 1000].export(temporal_file, format="wav")

            by_chunk_matches['user'] += sample_same_speaker_as_segment(temporal_file, profile_path)
            for person in people:
                by_chunk_matches[person['id']] += sample_same_speaker_as_segment(temporal_file, person['path'])
            os.remove(temporal_file)

        if by_chunk_matches:
            print(by_chunk_matches)
            max_match = max(by_chunk_matches, key=by_chunk_matches.get)
            matches[i] = {'is_user': max_match == 'user', 'person_id': None if max_match == 'user' else max_match}

    return matches

# Speech Profile Endpoint (replaces Modal speech_profile_modal.py)
@router.post("/v1/speaker-identification", tags=["Modal Services"])
def speaker_identification(
    uid: str, 
    audio_file: UploadFile = File(...), 
    segments: str = Form(...)
) -> List[ResponseItem]:
    """
    This endpoint obtains the user (speech profile + samples) + all user people speech samples
    and every segment from the transcript from the stt model, and classifies each segment to a person or to the user.
    
    This replaces the Modal speech_profile_modal.py endpoint.
    """
    print('speaker_identification')
    profile_path = get_speech_profile_expanded(uid)
    default = [{'is_user': False}] * len(json.loads(segments))

    if not profile_path:
        return default

    temp_audio_path = f"_temp/{audio_file.filename}"
    try:
        with open(temp_audio_path, 'wb') as f:
            f.write(audio_file.file.read())

        segments_data = json.loads(segments)
        transcript_segments = [TranscriptSegment(**segment) for segment in segments_data]

        # people = get_people_with_speech_samples(uid)
        people = []  # Temporarily disabled as in original
        
        result = classify_segments(temp_audio_path, profile_path, people, transcript_segments)
        return result
    except Exception as e:
        print(f"Error in speaker_identification: {e}")
        return default
    finally:
        if profile_path and os.path.exists(profile_path):
            os.remove(profile_path)
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

# VAD Endpoint (replaces Modal vad_modal.py)
@router.post("/v1/vad", tags=["Modal Services"])
def vad(file: UploadFile = File(...)):
    """
    Voice Activity Detection endpoint.
    
    This replaces the Modal vad_modal.py endpoint.
    """
    print('vad')
    upload_id = str(uuid.uuid4())
    file_path = f"_temp/{upload_id}_{file.filename}"
    
    try:
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        
        vad_model = get_vad_model()
        output = vad_model(file_path)
        segments = output.get_timeline().support()
        
        data = []
        for segment in segments:
            data.append({
                'start': segment.start,
                'end': segment.end,
                'duration': segment.duration,
            })
        return data
    except Exception as e:
        print(f"Error in VAD endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"VAD processing failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/health", tags=["Modal Services"])
def modal_services_health():
    """Health check for modal services"""
    return {
        "status": "healthy", 
        "service": "modal_services",
        "ml_dependencies_available": ML_DEPENDENCIES_AVAILABLE,
        "dependencies_needed": [
            "torch", 
            "speechbrain", 
            "pyannote.audio", 
            "pydub"
        ] if not ML_DEPENDENCIES_AVAILABLE else None
    }

@router.get("/status", tags=["Modal Services"])
def ml_dependencies_status():
    """Check ML dependencies status"""
    status = {
        "ml_dependencies_available": ML_DEPENDENCIES_AVAILABLE,
        "gpu_available": None,
        "models_ready": False
    }
    
    if ML_DEPENDENCIES_AVAILABLE:
        try:
            status["gpu_available"] = torch.cuda.is_available()
            status["cuda_devices"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
        except Exception as e:
            status["gpu_error"] = str(e)
    else:
        status["install_command"] = "pip install torch speechbrain pyannote.audio pydub"
        
    return status
