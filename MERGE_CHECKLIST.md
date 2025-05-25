# v3 Integration - Merge Checklist

## Current Status
The v3 architecture has been successfully implemented with core functionality working. The main integration is complete but requires testing and refinement before merging to main.

## Completed ✅
- ✅ Core v3 modules (startup_checks, memory_manager, tool_detector)
- ✅ Network diagnostics suite (layer2, layer3, DNS, web connectivity)
- ✅ First pentesting tool wrapper (nmap)
- ✅ Main instability.py v3 integration
- ✅ Basic chatbot compatibility (ping function fixed)

## Before Merge - Critical Tasks 🔧

### 1. Comprehensive Testing
- [ ] **Test all manual mode tools** - `python instability.py manual [tool_name]`
- [ ] **Test comprehensive diagnostics** - `python instability.py manual all`
- [ ] **Test v3 startup sequence** - `python instability.py test`
- [ ] **Test chatbot integration** - Verify all chatbot tools work with v3 modules
- [ ] **Cross-platform testing** - Test on Windows/Linux if possible

### 2. Tool Interface Standardization
- [ ] **Audit all chatbot tools** - Check for `arg_name` parameter compatibility
- [ ] **Fix remaining tool argument mismatches** - Similar to ping_target fix
- [ ] **Update chatbot tool descriptions** - Ensure they match actual v3 capabilities
- [ ] **Test tool execution** - Verify all tools in chatbot work correctly

### 3. Error Handling & Edge Cases
- [ ] **Test offline mode** - Verify graceful degradation when Ollama/internet unavailable
- [ ] **Test missing tools** - Ensure proper fallbacks when pentesting tools not installed
- [ ] **Test invalid inputs** - Handle malformed targets, timeouts, etc.
- [ ] **Memory file permissions** - Ensure memory/ directory creation works properly

### 4. Documentation Updates
- [ ] **Update README.md** - Document v3 features and new capabilities
- [ ] **Update CLAUDE.md** - Ensure development guidelines reflect v3 architecture
- [ ] **Create migration guide** - Help users transition from v2 to v3
- [ ] **Update help text** - Ensure all help commands show current v3 functionality

### 5. Performance & Optimization
- [ ] **Tool inventory caching** - Verify cache works properly and doesn't slow startup
- [ ] **Memory usage** - Check for any memory leaks in persistent operations
- [ ] **Startup time** - Ensure v3 startup sequence isn't too slow
- [ ] **Large network scans** - Test nmap with larger targets for performance

## Known Issues to Fix 🐛

### Chatbot Tool Interface
- **Issue**: Some tools may still have `arg_name` parameter mismatches
- **Solution**: Audit and fix all tool functions like we did with `ping_target`
- **Files**: `tools.py`, `network_diagnostics.py`

### Memory Directory Creation
- **Issue**: Memory directory might not exist on fresh installs
- **Solution**: Ensure `get_memory_dir()` is called appropriately during startup
- **Files**: `config.py`, `memory/memory_manager.py`

### Tool Detection Errors
- **Issue**: Some tools might not be detected properly on different systems
- **Solution**: Test tool detection on various platforms and fix path issues
- **Files**: `pentest/tool_detector.py`, `config.py`

## Testing Commands 🧪

```bash
# Basic functionality
python instability.py test
python instability.py manual
python instability.py manual all

# Specific tool tests
python instability.py manual ping
python instability.py manual dns_check
python instability.py manual nmap_scan
python instability.py manual tool_inventory

# Chatbot integration
python instability.py chatbot
# Then test: ping, dns, web checks, nmap commands
```

## Post-Merge Enhancements 🚀

### Phase 2 Features (Future)
- [ ] Additional pentesting tool wrappers (nuclei, httpx, feroxbuster)
- [ ] Enhanced chatbot integration with v3 startup context
- [ ] Advanced memory persistence features
- [ ] Web-based dashboard interface
- [ ] Automated penetration testing workflows

### Integration Improvements
- [ ] Chatbot awareness of startup results
- [ ] Dynamic tool recommendations based on detected tools
- [ ] Session persistence across chatbot restarts
- [ ] Enhanced reporting and export capabilities

## Branch Management 📋

**Current Branch**: `feature/v3-integration`
**Target**: `main`

**Before merge**:
1. Complete critical tasks above
2. Run full test suite: `python instability.py run-tests`
3. Test on clean environment (new clone)
4. Create comprehensive merge commit message documenting v3 features

**Merge Strategy**: 
- Use merge commit (not squash) to preserve development history
- Tag the merge as `v3.0.0` release
- Update version references in code after merge