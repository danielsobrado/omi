# Tech Stack

## Mobile App (Flutter/Dart)
- **Framework**: Flutter 3.32.4+
- **Language**: Dart 3.0+
- **Key Dependencies**:
  - Provider for state management
  - Firebase (Auth, Core, Messaging)
  - Flutter Blue Plus for Bluetooth
  - WebRTC for audio processing
  - Opus codec for audio compression
  - Various UI libraries (Lottie, etc.)

## Backend (Python)
- **Framework**: FastAPI
- **Language**: Python 3.9+
- **Key Dependencies**:
  - FastAPI for API framework
  - SQLAlchemy for database ORM
  - Pydantic for data validation
  - OpenAI/Groq for LLM processing
  - Deepgram for speech-to-text
  - ChromaDB for vector storage
  - Redis for caching
  - Firebase Admin SDK
  - PyTorch for ML processing

## Firmware (C++)
- **RTOS**: Zephyr RTOS
- **Language**: C++
- **Build System**: CMake
- **Platform**: nRF Connect SDK
- **Hardware**: Nordic nRF52/nRF53 series

## Database Options
- **Primary**: Google Firestore (NoSQL)
- **Alternative**: PostgreSQL with pgvector extension
- **Cache**: Redis
- **Vector Database**: ChromaDB (local)

## Documentation
- **Platform**: Mintlify
- **Language**: MDX
- **Node**: 19+

## Infrastructure
- **Containers**: Docker
- **CI/CD**: GitHub Actions
- **Cloud**: Google Cloud Platform
- **Deployment**: Cloud Run, Firebase Hosting