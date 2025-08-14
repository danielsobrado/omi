# Project Architecture

## System Overview
Omi is a distributed system consisting of multiple components:

```
[Omi Device] <--BLE--> [Mobile App] <--HTTP--> [Backend] <---> [AI Services]
     |                      |                     |
     |                      |                     |
[Firmware]              [Flutter]            [FastAPI]
```

## Component Architecture

### Omi Device (Firmware)
- **RTOS**: Zephyr-based real-time operating system
- **Audio Pipeline**: Microphone → Codec → Bluetooth
- **Storage**: SD card for offline recording
- **Power Management**: Battery optimization
- **Communication**: Bluetooth Low Energy (BLE)

### Mobile App (Flutter)
- **State Management**: Provider pattern
- **Communication**: 
  - BLE for device connection
  - HTTP for backend API
  - WebRTC for audio streaming
- **Audio Processing**: Opus codec for compression
- **UI**: Material Design with custom components
- **Background Services**: Audio processing, notifications

### Backend (Python FastAPI)
- **API Layer**: FastAPI with Pydantic models
- **Database Layer**: SQLAlchemy ORM
- **AI Processing**: 
  - Speech-to-text (Deepgram)
  - LLM processing (OpenAI/Groq)
  - Vector search (ChromaDB)
- **Authentication**: Firebase Auth
- **File Storage**: Google Cloud Storage
- **Caching**: Redis
- **Background Tasks**: Celery/APScheduler

### Web Platform
- **Frontend**: React/Next.js
- **AI Personas**: Custom AI personality system
- **API Integration**: Backend REST APIs

## Data Flow

### Audio Processing Pipeline
1. **Capture**: Device microphone captures audio
2. **Encode**: Opus codec compression
3. **Transmit**: BLE to mobile app
4. **Process**: App sends to backend
5. **Transcribe**: Speech-to-text conversion
6. **Analyze**: AI processing for insights
7. **Store**: Conversation storage
8. **Notify**: User notifications

### Device Communication
- **BLE Protocol**: Custom protocol for audio streaming
- **Pairing**: Device discovery and authentication
- **Streaming**: Real-time audio data transfer
- **Commands**: Control messages (start/stop recording)

## Database Schema (Simplified)

### Users
- User profiles and preferences
- Authentication tokens
- Device associations

### Conversations
- Transcribed audio content
- Metadata (timestamp, location, participants)
- AI-generated summaries and insights

### Devices
- Device registration and status
- Firmware versions
- Battery levels

## Security Architecture
- **Authentication**: Firebase Auth tokens
- **Authorization**: Role-based access control
- **Encryption**: TLS for all communications
- **Data Privacy**: User data isolation
- **Device Security**: Secure firmware updates

## Scalability Considerations
- **Horizontal Scaling**: Multiple backend instances
- **Database Sharding**: User-based partitioning
- **CDN**: Static asset distribution
- **Caching**: Redis for frequently accessed data
- **Load Balancing**: Traffic distribution

## Monitoring and Observability
- **Logging**: Structured logging across all components
- **Metrics**: Performance and usage metrics
- **Error Tracking**: Centralized error collection
- **Health Checks**: Service availability monitoring