
import os
import io
from pathlib import Path
from pydub import AudioSegment

class AudioProcessor:
    
    SAMPLE_RATE = 16000  
    CHANNELS = 1  
    
    def __init__(self, storage_path: str = "./audio_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def save_audio_chunk(self, audio_data: bytes, transcription_id: int, chunk_index: int) -> str:
        filename = f"trans_{transcription_id}_chunk_{chunk_index}.wav"
        filepath = self.storage_path / filename
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        return str(filepath)
    
    def convert_to_wav(self, input_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.wav'))
        
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Convert to mono
            if audio.channels > 1:
                audio = audio.set_channels(self.CHANNELS)
            
            # Set sample rate
            audio = audio.set_frame_rate(self.SAMPLE_RATE)
            
            # Export as WAV
            audio.export(output_path, format='wav')
            
            return output_path
        except Exception as e:
            raise ValueError(f"Failed to convert audio: {str(e)}")
    
    def get_audio_duration(self, file_path: str) -> int:
        audio = AudioSegment.from_file(file_path)
        return int(audio.duration_seconds)
    
    def validate_audio(self, file_path: str) -> dict:
        try:
            audio = AudioSegment.from_file(file_path)
            
            return {
                "valid": True,
                "duration_seconds": audio.duration_seconds,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "file_size_bytes": os.path.getsize(file_path)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

