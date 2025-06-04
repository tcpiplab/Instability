# Tool Execution Tracking Implementation Specification

## Problem Statement

The chatbot is hallucinating tool execution results by fabricating plausible-looking output data without actually calling the tools. This creates a critical trust issue where users receive false information that appears legitimate.

### Example of the Problem
The chatbot claimed to execute `check_internet_connection` but fabricated results showing data from `run_speed_test` without calling either tool.

## Solution Overview

Implement a mandatory tool execution tracking system that:
1. Intercepts all tool calls using simple function wrappers
2. Generates unique execution IDs for each call
3. Validates all claimed tool results against actual executions
4. Rejects any response containing unverified tool results

## Implementation Details

### 1. Core Execution Tracking Functions

Create tracking functions in `core/execution_tracker.py`:

```python
import uuid
import time
import json
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Callable, Optional, List
from collections import deque

# Global execution tracking state
_execution_history: deque = deque(maxlen=100)
_execution_map: Dict[str, Dict[str, Any]] = {}
_execution_window_seconds = 300  # 5 minutes

def generate_execution_id(tool_name: str) -> str:
    """Generate a unique execution ID for a tool execution."""
    timestamp = int(time.time() * 1000)
    unique_part = uuid.uuid4().hex[:8]
    return f"{tool_name}_{timestamp}_{unique_part}"

def track_tool_execution(tool_func: Callable) -> Callable:
    """
    Decorator to wrap tool functions and track their execution.
    
    Usage:
        @track_tool_execution
        def my_network_tool(target: str) -> str:
            return perform_network_check(target)
    """
    @wraps(tool_func)
    def wrapper(*args, **kwargs):
        tool_name = tool_func.__name__
        execution_id = generate_execution_id(tool_name)
        start_time = time.time()
        
        # Record execution start
        execution_record = {
            'execution_id': execution_id,
            'tool_name': tool_name,
            'args': args,
            'kwargs': kwargs,
            'start_time': start_time,
            'completed': False,
            'result': None,
            'error': None,
            'duration': None
        }
        
        _execution_map[execution_id] = execution_record
        _execution_history.append(execution_record)
        
        try:
            # Execute the actual tool
            result = tool_func(*args, **kwargs)
            
            # Update execution record
            execution_record['completed'] = True
            execution_record['result'] = result
            execution_record['duration'] = time.time() - start_time
            
            # Return result with execution ID embedded
            if isinstance(result, dict):
                result['execution_id'] = execution_id
                result['executed_at'] = datetime.fromtimestamp(start_time).isoformat()
                return result
            else:
                # For string results, embed execution info
                return {
                    'execution_id': execution_id,
                    'tool_name': tool_name,
                    'result': result,
                    'executed_at': datetime.fromtimestamp(start_time).isoformat()
                }
                
        except Exception as e:
            execution_record['error'] = str(e)
            execution_record['duration'] = time.time() - start_time
            raise
    
    return wrapper

def verify_execution(execution_id: str, tool_name: str) -> Dict[str, Any]:
    """
    Verify that a claimed execution actually occurred.
    
    Args:
        execution_id: The claimed execution ID
        tool_name: The claimed tool name
        
    Returns:
        Dict with verification status and details
    """
    # Check if execution ID exists
    if execution_id not in _execution_map:
        return {
            'valid': False,
            'reason': 'execution_id_not_found',
            'message': f'No execution found with ID: {execution_id}'
        }
    
    execution = _execution_map[execution_id]
    
    # Check if execution is within time window
    if time.time() - execution['start_time'] > _execution_window_seconds:
        return {
            'valid': False,
            'reason': 'execution_expired',
            'message': f'Execution {execution_id} is outside the valid time window'
        }
    
    # Check if tool name matches
    if execution['tool_name'] != tool_name:
        return {
            'valid': False,
            'reason': 'tool_name_mismatch',
            'message': f'Execution {execution_id} was for tool {execution["tool_name"]}, not {tool_name}'
        }
    
    # Check if execution completed successfully
    if not execution['completed']:
        return {
            'valid': False,
            'reason': 'execution_incomplete',
            'message': f'Execution {execution_id} did not complete successfully'
        }
    
    return {
        'valid': True,
        'execution': execution,
        'actual_result': execution['result']
    }

def get_recent_executions(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent execution records for debugging."""
    return list(_execution_history)[-limit:]

def clear_old_executions():
    """Remove executions outside the time window to prevent memory bloat."""
    global _execution_map, _execution_history
    
    current_time = time.time()
    valid_executions = [
        ex for ex in _execution_history 
        if current_time - ex['start_time'] <= _execution_window_seconds
    ]
    
    _execution_history.clear()
    _execution_history.extend(valid_executions)
    
    # Update execution map
    old_ids = [
        exec_id for exec_id, ex in _execution_map.items()
        if current_time - ex['start_time'] > _execution_window_seconds
    ]
    for exec_id in old_ids:
        del _execution_map[exec_id]
```

### 2. Response Validation Functions

Create validation functions in `core/response_validator.py`:

```python
import re
import json
from typing import Dict, Any, List, Tuple, Optional
from core.execution_tracker import verify_execution

def extract_tool_claims(response: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Extract claimed tool executions from the chatbot response.
    
    Returns:
        Tuple of (tool_claims, execution_ids)
    """
    tool_claims = []
    
    # Pattern 1: Look for JSON blocks with tool results
    json_pattern = r'{[^{}]*(?:{[^{}]*}[^{}]*)*}'
    json_matches = re.findall(json_pattern, response)
    
    for match in json_matches:
        try:
            data = json.loads(match)
            if 'tool_name' in data or 'execution_id' in data:
                tool_claims.append(data)
        except json.JSONDecodeError:
            continue
    
    # Pattern 2: Look for execution IDs mentioned in text
    id_pattern = r'execution_id["\']?\s*:\s*["\']?([a-zA-Z0-9_]+)'
    execution_ids = re.findall(id_pattern, response)
    
    # Pattern 3: Look for execution IDs in parentheses
    paren_pattern = r'\(execution_id:\s*([a-zA-Z0-9_]+)\)'
    execution_ids.extend(re.findall(paren_pattern, response))
    
    return tool_claims, execution_ids

def validate_response(response: str) -> Tuple[bool, List[str]]:
    """
    Validate that all claimed tool executions in the response are real.
    
    Args:
        response: The chatbot's response text
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    tool_claims, execution_ids = extract_tool_claims(response)
    issues = []
    
    # If no tool claims found, response is valid
    if not tool_claims and not execution_ids:
        return True, []
    
    # Validate each claimed execution
    for claim in tool_claims:
        tool_name = extract_tool_name_from_claim(claim)
        execution_id = claim.get('execution_id')
        
        if not execution_id:
            issues.append(f"Tool claim for {tool_name} missing execution_id")
            continue
        
        if not tool_name:
            issues.append(f"Tool claim with execution_id {execution_id} missing tool_name")
            continue
        
        verification = verify_execution(execution_id, tool_name)
        if not verification['valid']:
            issues.append(f"Invalid execution: {verification['message']}")
    
    # Check standalone execution IDs
    for exec_id in execution_ids:
        from core.execution_tracker import _execution_map
        if exec_id not in _execution_map:
            issues.append(f"Referenced execution_id {exec_id} not found")
    
    return len(issues) == 0, issues

def extract_tool_name_from_claim(claim: Dict[str, Any]) -> Optional[str]:
    """Extract tool name from various claim formats."""
    # Try different fields where tool name might be
    for field in ['tool_name', 'command_executed', 'function', 'tool']:
        if field in claim:
            value = claim[field]
            if isinstance(value, str):
                # Extract function name from command if needed
                match = re.match(r'(\w+)\(', value)
                if match:
                    return match.group(1)
                return value
    return None

def handle_validation_failure(issues: List[str]) -> str:
    """Generate appropriate error message for validation failures."""
    return (
        "I apologize, but I attempted to provide tool results without "
        "actually executing the tools. Let me try again properly.\n\n"
        f"Technical details: {'; '.join(issues)}"
    )
```

### 3. Integration with Existing Tools

Modify your existing tool registration to use tracking:

```python
# In core/tools_registry.py or wherever tools are registered

from core.execution_tracker import track_tool_execution

# Apply tracking to existing tools
def wrap_existing_tools(tools_dict: Dict[str, Callable]) -> Dict[str, Callable]:
    """Wrap existing tools with execution tracking."""
    wrapped_tools = {}
    for tool_name, tool_func in tools_dict.items():
        wrapped_tools[tool_name] = track_tool_execution(tool_func)
    return wrapped_tools

# For new tools, simply use the decorator
@track_tool_execution
def check_internet_connection() -> Dict[str, Any]:
    """Check internet connectivity with execution tracking."""
    # Tool implementation here
    return {"status": "connected", "latency": 15}
```

### 4. Chatbot Response Pipeline Integration

Modify your chatbot's response handling:

```python
# In chatbot.py

from core.response_validator import validate_response, handle_validation_failure

def process_chatbot_response(chatbot_response: str) -> str:
    """
    Validate chatbot response before presenting to user.
    
    Args:
        chatbot_response: Raw response from the chatbot
        
    Returns:
        Validated response or error message
    """
    is_valid, issues = validate_response(chatbot_response)
    
    if not is_valid:
        print(f"[VALIDATION] Hallucination detected: {issues}")
        return handle_validation_failure(issues)
    
    return chatbot_response

# In your main chat loop
def chat_loop():
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Get chatbot response
        raw_response = get_chatbot_response(user_input)
        
        # Validate before showing to user
        validated_response = process_chatbot_response(raw_response)
        
        print(f"Assistant: {validated_response}")
```

### 5. System Prompt Updates

Add this to your chatbot's system prompt:

```
CRITICAL TOOL EXECUTION PROTOCOL:

When using tools, you MUST follow this exact process:
1. Announce your intention: "I'll check this using the [tool_name] tool."
2. Execute the tool and wait for the actual result
3. The result will ALWAYS include an 'execution_id' field
4. When presenting results, ALWAYS include the execution_id

Example correct format:
"I'll check the internet connection using the check_internet_connection tool.

[Tool execution occurs here]

The tool returned (execution_id: check_internet_connection_1234567890_abcd):
- Connection status: Active
- Latency: 15ms"

NEVER:
- Present tool results without executing the tool
- Omit the execution_id when discussing results  
- Fabricate or imagine what a tool might return
- Mix up tool names and their results

If you cannot execute a tool, say so explicitly rather than pretending you did.
```

## Implementation Steps

1. **Create tracking functions**: Add `core/execution_tracker.py` with the tracking functions

2. **Create validation functions**: Add `core/response_validator.py` with validation logic

3. **Wrap existing tools**: 
   - Import the tracking decorator
   - Apply to all tool functions
   - Update tool registration

4. **Integrate validation**: 
   - Add validation to response pipeline
   - Handle validation failures appropriately

5. **Update prompts**: Add the execution protocol to your system prompt

6. **Test thoroughly**: 
   - Test with real tool executions
   - Test with fabricated results
   - Test edge cases

## Testing Functions

Create simple test functions:

```python
def test_hallucination_detection():
    """Test that fabricated results are caught."""
    fake_response = """
    Tool result: {
        'tool_name': 'run_speed_test',
        'download': 125,
        'upload': 73
    }
    The internet speed is good.
    """
    
    is_valid, issues = validate_response(fake_response)
    assert not is_valid
    assert "missing execution_id" in str(issues)

def test_valid_execution():
    """Test that real executions pass validation."""
    from core.execution_tracker import track_tool_execution
    
    @track_tool_execution
    def dummy_tool():
        return {"result": "success"}
    
    # Execute tool
    result = dummy_tool()
    execution_id = result['execution_id']
    
    # Create valid response
    valid_response = f"""
    Tool result: {json.dumps(result)}
    The tool completed successfully.
    """
    
    is_valid, issues = validate_response(valid_response)
    assert is_valid
    assert len(issues) == 0
```

## Monitoring and Maintenance

1. **Log validation failures** to identify hallucination patterns

2. **Periodically clean old executions**:
   ```python
   # Run periodically
   from core.execution_tracker import clear_old_executions
   clear_old_executions()
   ```

3. **Monitor execution patterns** to identify frequently hallucinated tools

4. **Adjust validation patterns** as new hallucination formats are discovered

## Success Criteria

- Zero fabricated tool results reach the user
- All legitimate tool executions pass validation  
- Clear error messages when hallucination is detected
- Minimal performance impact on normal operations
- Simple, maintainable code following project conventions