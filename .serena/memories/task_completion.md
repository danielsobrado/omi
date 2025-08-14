# Task Completion Guidelines

## When a Task is Completed

### Backend Development
1. **Testing**: Run all tests to ensure no regressions
   ```bash
   python -m pytest
   ```

2. **Code Quality**: Ensure code follows style guidelines
   - Type hints on all functions
   - Proper error handling
   - Logging implemented
   - Configuration externalized

3. **Documentation**: Update relevant documentation
   - API documentation if endpoints changed
   - README updates if setup changed
   - Comments for complex logic

### Mobile App Development
1. **Testing**: Run unit and integration tests
   ```bash
   flutter test
   flutter test integration_test/
   ```

2. **Build Verification**: Ensure app builds on both platforms
   ```bash
   flutter build ios --flavor dev
   flutter build apk --flavor dev
   ```

3. **Code Quality**: 
   - Dart analyzer warnings resolved
   - No unused imports
   - Proper widget structure

### Firmware Development
1. **Build**: Ensure firmware compiles without errors
   ```bash
   ./scripts/build-docker.sh
   ```

2. **Testing**: Test on actual hardware if available
3. **Documentation**: Update firmware documentation

### General Completion Checklist
- [ ] All tests pass
- [ ] Code builds without errors
- [ ] Documentation updated
- [ ] Configuration files updated if needed
- [ ] TODO comments resolved or tracked
- [ ] Error handling implemented
- [ ] Logging added where appropriate
- [ ] Constants extracted from code
- [ ] SOLID principles followed
- [ ] No hardcoded values
- [ ] Git commit with clear message

### Before Submitting
1. Review code for production quality
2. Check for any sensitive data exposure
3. Verify all dependencies are documented
4. Ensure backward compatibility if applicable
5. Update version numbers if needed

### TODOs
- Mark incomplete work with clear TODO comments
- Include context for why the work is incomplete
- Reference issue numbers if applicable
- Set priority levels for TODOs