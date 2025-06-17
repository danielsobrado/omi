import datetime
import os
from typing import List

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from database.redis_db import cache_signed_url, get_cached_signed_url

# Initialize S3 client for MinIO
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4')
)

# *******************************************
# ************* SPEECH PROFILE **************
# *******************************************
def upload_profile_audio(file_path: str, uid: str):
    object_key = f'speech-profiles/{uid}/speech_profile.wav'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'


def get_user_has_speech_profile(uid: str) -> bool:
    object_key = f'speech-profiles/{uid}/speech_profile.wav'
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        return True
    except ClientError:
        return False


def get_profile_audio_if_exists(uid: str, download: bool = True) -> str:
    object_key = f'speech-profiles/{uid}/speech_profile.wav'
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        if download:
            file_path = f'_temp/{uid}_speech_profile.wav'
            s3_client.download_file(S3_BUCKET_NAME, object_key, file_path)
            return file_path
        return _get_signed_url(object_key, 60)
    except ClientError:
        return None


def upload_additional_profile_audio(file_path: str, uid: str) -> None:
    file_name = file_path.split("/")[-1]
    object_key = f'speech-profiles/{uid}/additional_profile_recordings/{file_name}'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)


def delete_additional_profile_audio(uid: str, file_name: str) -> None:
    object_key = f'speech-profiles/{uid}/additional_profile_recordings/{file_name}'
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        print('delete_additional_profile_audio deleting', file_name)
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)
    except ClientError:
        pass


def get_additional_profile_recordings(uid: str, download: bool = False) -> List[str]:
    prefix = f'speech-profiles/{uid}/additional_profile_recordings/'
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return []
        
        if download:
            paths = []
            for obj in response['Contents']:
                file_name = obj['Key'].split("/")[-1]
                file_path = f'_temp/{uid}_{file_name}'
                s3_client.download_file(S3_BUCKET_NAME, obj['Key'], file_path)
                paths.append(file_path)
            return paths

        return [_get_signed_url(obj['Key'], 60) for obj in response['Contents']]
    except ClientError:
        return []


# ********************************************
# ************* PEOPLE PROFILES **************
# ********************************************

def upload_user_person_speech_sample(file_path: str, uid: str, person_id: str) -> None:
    file_name = file_path.split("/")[-1]
    object_key = f'speech-profiles/{uid}/people_profiles/{person_id}/{file_name}'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)


def delete_user_person_speech_sample(uid: str, person_id: str, file_name: str) -> None:
    object_key = f'speech-profiles/{uid}/people_profiles/{person_id}/{file_name}'
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)
    except ClientError:
        pass


def delete_speech_sample_for_people(uid: str, file_name: str) -> None:
    prefix = f'speech-profiles/{uid}/people_profiles/'
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                if file_name in obj['Key']:
                    print('delete_speech_sample_for_people deleting', obj['Key'])
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])
    except ClientError:
        pass


def delete_user_person_speech_samples(uid: str, person_id: str) -> None:
    prefix = f'speech-profiles/{uid}/people_profiles/{person_id}/'
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])
    except ClientError:
        pass


def get_user_people_ids(uid: str) -> List[str]:
    prefix = f'speech-profiles/{uid}/people_profiles/'
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return []
        
        people_ids = set()
        for obj in response['Contents']:
            # Extract person_id from path like speech-profiles/uid/people_profiles/person_id/filename
            path_parts = obj['Key'].split('/')
            if len(path_parts) >= 4:
                people_ids.add(path_parts[3])
        return list(people_ids)
    except ClientError:
        return []


def get_user_person_speech_samples(uid: str, person_id: str, download: bool = False) -> List[str]:
    prefix = f'speech-profiles/{uid}/people_profiles/{person_id}/'
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return []
        
        if download:
            paths = []
            for obj in response['Contents']:
                file_name = obj['Key'].split("/")[-1]
                file_path = f'_temp/{uid}_person_{file_name}'
                s3_client.download_file(S3_BUCKET_NAME, obj['Key'], file_path)
                paths.append(file_path)
            return paths

        return [_get_signed_url(obj['Key'], 60) for obj in response['Contents']]
    except ClientError:
        return []


# ********************************************
# ************* POST PROCESSING **************
# ********************************************
def upload_postprocessing_audio(file_path: str):
    object_key = f'postprocessing/{file_path}'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'


def delete_postprocessing_audio(file_path: str):
    object_key = f'postprocessing/{file_path}'
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)


# ***********************************
# ************* SDCARD **************
# ***********************************

def upload_sdcard_audio(file_path: str):
    object_key = f'postprocessing/sdcard/{file_path}'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'


def download_postprocessing_audio(file_path: str, destination_file_path: str):
    object_key = f'postprocessing/{file_path}'
    s3_client.download_file(S3_BUCKET_NAME, object_key, destination_file_path)


# ************************************************
# *********** CONVERSATIONS RECORDINGS ***********
# ************************************************

def upload_conversation_recording(file_path: str, uid: str, conversation_id: str):
    object_key = f'memories-recordings/{uid}/{conversation_id}.wav'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'


def get_conversation_recording_if_exists(uid: str, memory_id: str) -> str:
    print('get_conversation_recording_if_exists', uid, memory_id)
    object_key = f'memories-recordings/{uid}/{memory_id}.wav'
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        file_path = f'_temp/{memory_id}.wav'
        s3_client.download_file(S3_BUCKET_NAME, object_key, file_path)
        return file_path
    except ClientError:
        return None


def delete_all_conversation_recordings(uid: str):
    if not uid:
        return
    prefix = f'memories-recordings/{uid}'
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])
    except ClientError:
        pass


# ********************************************
# ************* SYNCING FILES **************
# ********************************************
def get_syncing_file_temporal_url(file_path: str):
    object_key = f'temporal-sync/{file_path}'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'

def get_syncing_file_temporal_signed_url(file_path: str):
    object_key = f'temporal-sync/{file_path}'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    return _get_signed_url(object_key, 15)


def delete_syncing_temporal_file(file_path: str):
    object_key = f'temporal-sync/{file_path}'
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)


# **********************************
# ************* UTILS **************
# **********************************

def _get_signed_url(object_key: str, minutes: int):
    try:
        if cached := get_cached_signed_url(object_key):
            return cached
    except Exception as e:
        print(f"Warning: Redis caching unavailable: {e}")

    signed_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET_NAME, 'Key': object_key},
        ExpiresIn=minutes * 60
    )
    
    try:
        cache_signed_url(object_key, signed_url, minutes * 60)
    except Exception as e:
        print(f"Warning: Could not cache signed URL: {e}")
    
    return signed_url


def upload_app_logo(file_path: str, app_id: str):
    object_key = f'app-logos/{app_id}.png'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    # Set cache control metadata
    s3_client.copy_object(
        Bucket=S3_BUCKET_NAME,
        Key=object_key,
        CopySource={'Bucket': S3_BUCKET_NAME, 'Key': object_key},
        Metadata={'Cache-Control': 'public, no-cache'},
        MetadataDirective='REPLACE'
    )
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'


def delete_app_logo(img_url: str):
    # Extract object key from URL
    if S3_ENDPOINT_URL in img_url:
        object_key = img_url.split(f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/')[1]
    else:
        # Fallback for old GCS URLs or other formats
        object_key = f'app-logos/{img_url.split("/")[-1]}'
    
    print('delete_app_logo', object_key)
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)

def upload_app_thumbnail(file_path: str, thumbnail_id: str) -> str:
    object_key = f'app-thumbnails/{thumbnail_id}.jpg'
    s3_client.upload_file(file_path, S3_BUCKET_NAME, object_key)
    # Set cache control metadata
    s3_client.copy_object(
        Bucket=S3_BUCKET_NAME,
        Key=object_key,
        CopySource={'Bucket': S3_BUCKET_NAME, 'Key': object_key},
        Metadata={'Cache-Control': 'public, no-cache'},
        MetadataDirective='REPLACE'
    )
    public_url = f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'
    return public_url

def get_app_thumbnail_url(thumbnail_id: str) -> str:
    object_key = f'app-thumbnails/{thumbnail_id}.jpg'
    return f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'

# **********************************
# ************* CHAT FILES **************
# **********************************
def upload_multi_chat_files(files_name: List[str], uid: str) -> dict:
    """
    Upload multiple files to S3/MinIO in the chat files prefix.

    Args:
        files_name: List of file paths to upload
        uid: User ID to use as part of the storage path

    Returns:
        dict: A dictionary mapping original filenames to their S3/MinIO URLs
    """
    dictFiles = {}
    for file_name in files_name:
        try:
            object_key = f'chat-files/{uid}/{file_name}'
            s3_client.upload_file(file_name, S3_BUCKET_NAME, object_key)
            dictFiles[file_name] = f'{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}'
        except Exception as e:
            print("Failed to upload {} due to exception: {}".format(file_name, e))
    
    return dictFiles
