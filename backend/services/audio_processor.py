import os
import uuid
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile
import asyncio

# Audio processing imports
import whisper
import librosa
import numpy as np
from pydub import AudioSegment
from pydub.utils import which

from models.schemas import Document, DocumentChunk, FileType
from services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class AudioProcessor(DocumentProcessor):
    def __init__(self):
        super().__init__()
        self.whisper_model = None
        self._initialize_audio_models()
    
    def _initialize_audio_models(self):
        """Initialize Whisper model for audio transcription"""
        try:
            # Load Whisper model (start with base model for balance of speed/accuracy)
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")
            
            # Check if ffmpeg is available for audio conversion
            if which("ffmpeg") is None:
                logger.warning("FFmpeg not found. Some audio formats may not be supported.")
            
        except Exception as e:
            logger.error(f"Error initializing Whisper model: {e}")
            self.whisper_model = None
    
    async def process_audio_file(self, file_path: str) -> Document:
        """Process audio file and extract text content"""
        try:
            file_path_obj = Path(file_path)
            
            # Convert audio to format supported by Whisper if necessary
            processed_audio_path = await self._preprocess_audio(file_path)
            
            # Transcribe audio using Whisper
            transcript = await self._transcribe_audio(processed_audio_path)
            
            if not transcript or not transcript.strip():
                raise ValueError("Failed to transcribe audio or audio is empty")
            
            # Extract metadata
            audio_metadata = await self._extract_audio_metadata(file_path)
            
            # Generate document metadata
            document_id = str(uuid.uuid4())
            title = self._extract_title(transcript, file_path_obj.stem)
            
            # Create document chunks
            chunks = self._create_chunks(transcript, document_id)
            
            # Generate summary
            summary = await self._generate_summary(transcript)
            
            # Extract tags/entities
            tags = self._extract_tags(transcript)
            tags.extend(["audio", "transcription"])  # Add audio-specific tags
            
            # Get file stats
            file_stats = file_path_obj.stat()
            
            document = Document(
                id=document_id,
                title=title,
                content=transcript,
                summary=summary,
                tags=list(set(tags)),  # Remove duplicates
                file_type=self._get_audio_file_type(file_path_obj.suffix),
                file_path=file_path,
                size_bytes=file_stats.st_size,
                chunk_ids=[chunk.id for chunk in chunks]
            )
            
            # Add audio metadata to document
            document.metadata = {
                "duration_seconds": audio_metadata.get("duration", 0),
                "sample_rate": audio_metadata.get("sample_rate", 0),
                "channels": audio_metadata.get("channels", 0),
                "format": file_path_obj.suffix.lower(),
                "transcription_language": audio_metadata.get("language", "unknown"),
                "confidence_scores": audio_metadata.get("confidence_scores", [])
            }
            
            self.chunks = chunks  # Store for vector database
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing audio file {file_path}: {e}")
            raise
        finally:
            # Clean up temporary files
            if 'processed_audio_path' in locals() and processed_audio_path != file_path:
                try:
                    os.unlink(processed_audio_path)
                except:
                    pass
    
    async def _preprocess_audio(self, file_path: str) -> str:
        """Preprocess audio file for Whisper compatibility"""
        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            
            # Whisper supports many formats, but let's ensure compatibility
            supported_formats = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
            
            if file_extension in supported_formats:
                return file_path  # No conversion needed
            
            # Convert to wav format for maximum compatibility
            logger.info(f"Converting {file_extension} to WAV format")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Use pydub for audio conversion
            audio = AudioSegment.from_file(file_path)
            audio.export(temp_path, format="wav")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error preprocessing audio {file_path}: {e}")
            return file_path  # Return original if conversion fails
    
    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            if not self.whisper_model:
                return await self._fallback_transcription(audio_path)
            
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.whisper_model.transcribe(
                    audio_path,
                    word_timestamps=True,
                    language=None  # Auto-detect language
                )
            )
            
            # Extract text and metadata
            transcript = result.get("text", "").strip()
            
            # Store additional metadata for potential use
            self._last_transcription_metadata = {
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "confidence_scores": self._extract_confidence_scores(result)
            }
            
            logger.info(f"Successfully transcribed audio: {len(transcript)} characters")
            return transcript
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return await self._fallback_transcription(audio_path)
    
    def _extract_confidence_scores(self, whisper_result: Dict[str, Any]) -> List[float]:
        """Extract confidence scores from Whisper result"""
        try:
            segments = whisper_result.get("segments", [])
            confidence_scores = []
            
            for segment in segments:
                # Whisper doesn't provide direct confidence scores, 
                # but we can use probability as a proxy
                if "avg_logprob" in segment:
                    # Convert log probability to approximate confidence
                    confidence = min(1.0, max(0.0, np.exp(segment["avg_logprob"])))
                    confidence_scores.append(confidence)
            
            return confidence_scores
            
        except Exception as e:
            logger.warning(f"Error extracting confidence scores: {e}")
            return []
    
    async def _fallback_transcription(self, audio_path: str) -> str:
        """Fallback transcription method when Whisper is not available"""
        logger.warning("Whisper model not available, using fallback transcription")
        
        # Simple fallback: return filename-based content
        file_path_obj = Path(audio_path)
        return f"Audio file: {file_path_obj.name}\n\nTranscription not available. Please ensure Whisper model is properly installed."
    
    async def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from audio file"""
        try:
            # Use librosa to extract audio metadata
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Get additional metadata using pydub
            audio = AudioSegment.from_file(file_path)
            
            metadata = {
                "duration": duration,
                "sample_rate": sr,
                "channels": audio.channels,
                "frame_rate": audio.frame_rate,
                "sample_width": audio.sample_width
            }
            
            # Add transcription metadata if available
            if hasattr(self, '_last_transcription_metadata'):
                metadata.update(self._last_transcription_metadata)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting audio metadata: {e}")
            return {"duration": 0, "sample_rate": 0, "channels": 0}
    
    def _get_audio_file_type(self, extension: str) -> FileType:
        """Convert audio file extension to FileType enum"""
        # For now, we'll use a generic type or extend the FileType enum
        audio_mapping = {
            '.mp3': 'mp3',
            '.wav': 'wav', 
            '.m4a': 'm4a',
            '.flac': 'flac',
            '.ogg': 'ogg',
            '.aac': 'aac'
        }
        
        # Since FileType enum might not have audio types, we'll return as string for now
        # In production, extend the FileType enum to include audio formats
        return audio_mapping.get(extension.lower(), 'audio')
    
    async def extract_audio_segments(self, file_path: str, segment_length: int = 300) -> List[Dict[str, Any]]:
        """Extract segments from audio for better processing of long files"""
        try:
            if not self.whisper_model:
                return []
            
            # Load audio
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            segments = []
            segment_duration = segment_length  # seconds
            
            for start_time in range(0, int(duration), segment_duration):
                end_time = min(start_time + segment_duration, duration)
                
                # Extract segment
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                segment_audio = y[start_sample:end_sample]
                
                # Create temporary file for segment
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                    librosa.output.write_wav(temp_path, segment_audio, sr)
                
                try:
                    # Transcribe segment
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: self.whisper_model.transcribe(temp_path)
                    )
                    
                    segments.append({
                        "start_time": start_time,
                        "end_time": end_time,
                        "text": result.get("text", "").strip(),
                        "language": result.get("language", "unknown")
                    })
                    
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
            return segments
            
        except Exception as e:
            logger.error(f"Error extracting audio segments: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check audio processor health"""
        return {
            "status": "healthy" if self.whisper_model else "degraded",
            "whisper_available": bool(self.whisper_model),
            "ffmpeg_available": which("ffmpeg") is not None,
            "supported_formats": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"]
        }