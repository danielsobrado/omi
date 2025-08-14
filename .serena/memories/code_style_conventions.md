# Code Style and Conventions

## General Principles
- Follow KISS (Keep It Simple, Stupid) principle
- Apply YAGNI (You Ain't Gonna Need It) 
- Adhere to SOLID principles
- Production-quality code always
- Minimal explanatory comments that are generic
- Constants separated from code
- Proper logging and error handling
- Split large files based on SOLID principles

## Python (Backend)
- **Style**: PEP 8 compliant
- **Type Hints**: Required for all functions
- **Error Handling**: Proper exception handling with logging
- **Imports**: Organized and sorted
- **Configuration**: YAML files, no hardcoded values
- **Database**: SQLAlchemy ORM patterns
- **API**: FastAPI conventions with Pydantic models
- **Testing**: pytest with proper fixtures

## Flutter/Dart (Mobile App)
- **Style**: Dart style guide compliant
- **Architecture**: Provider pattern for state management
- **File Organization**: Feature-based folder structure
- **Widgets**: Stateless widgets preferred
- **Error Handling**: Proper error boundaries
- **Assets**: Organized in assets/ directory
- **Configuration**: Environment-specific config files

## C++ (Firmware)
- **Style**: Embedded C++ conventions
- **Memory Management**: Careful memory allocation
- **Real-time**: Consider real-time constraints
- **Power**: Power-efficient code patterns
- **Comments**: Hardware-specific documentation
- **Build**: CMake with proper configuration

## File Organization
- Keep source files small and focused
- Use proper directory structure
- Separate concerns into different files
- Configuration files in YAML format
- Environment-specific configurations

## Git Conventions
- Clear commit messages
- Feature branches for development
- PR reviews required
- Semantic versioning for releases

## Documentation
- Simple language (Brandon Sanderson style for creative content)
- Code comments only when necessary
- README files for setup instructions
- API documentation with examples