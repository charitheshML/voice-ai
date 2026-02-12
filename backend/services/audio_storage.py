import os
import uuid
from pathlib import Path
from typing import Optional

class AudioStorage:
    """
    Audio storage abstraction - currently filesystem, 
    replace with S3/GCS in production
    """
    
    def __init__(self, base_path: str = "audio_storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def save(self, session_id: str, audio_bytes: bytes, audio_type: str = "input") -> str:
        """
        Save audio and return storage key
        In production: upload to S3 with lifecycle policy (delete after 90 days)
        """
        session_folder = self.base_path / session_id
        session_folder.mkdir(exist_ok=True)
        
        audio_id = str(uuid.uuid4())
        # Use .opus for 10x compression vs .wav
        filename = f"{audio_type}_{audio_id}.wav"  # TODO: Convert to opus
        filepath = session_folder / filename
        
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        
        # Return S3-style key
        return f"{session_id}/{filename}"
    
    def get(self, storage_key: str) -> Optional[bytes]:
        """Retrieve audio by storage key"""
        filepath = self.base_path / storage_key
        if filepath.exists():
            with open(filepath, "rb") as f:
                return f.read()
        return None
    
    def delete(self, storage_key: str) -> bool:
        """Delete audio file"""
        filepath = self.base_path / storage_key
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def cleanup_session(self, session_id: str, older_than_days: int = 7):
        """Delete old session files"""
        import time
        session_folder = self.base_path / session_id
        if not session_folder.exists():
            return
        
        cutoff_time = time.time() - (older_than_days * 86400)
        for file in session_folder.iterdir():
            if file.stat().st_mtime < cutoff_time:
                file.unlink()


"""
import boto3

class S3AudioStorage:
    def __init__(self, bucket_name: str):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name
    
    def save(self, session_id: str, audio_bytes: bytes, audio_type: str = "input") -> str:
        audio_id = str(uuid.uuid4())
        key = f"{session_id}/{audio_type}_{audio_id}.opus"
        
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=audio_bytes,
            ContentType='audio/opus',
            StorageClass='INTELLIGENT_TIERING',
            Tagging='retention=90days'
        )
        return key
    
    def get(self, storage_key: str) -> Optional[bytes]:
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=storage_key)
            return response['Body'].read()
        except:
            return None
"""
