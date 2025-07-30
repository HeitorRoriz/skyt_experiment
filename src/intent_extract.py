import re
import json
from llm import query_llm
from config import MODEL, TEMPERATURE

# --------- DEV INTENT EXTRACTION ----------

DEV_INTENT_PROMPT = '''
Given the following prompt, extract the developer's intent as a JSON object with the following fields:
- goal: WHAT is the developer being asked to do?
- how: HOW should it be done? (methods, constraints, e.g., "using recursion", "bare metal", "interrupt driven")
- functions: List of functions/methods to implement, with names, arguments, and (if stated) return type.
- num_functions: Number of functions/methods specified.
- variables: List of variables to declare/use (names, and types if present).
- num_variables: Number of variables specified.
- target_scope: Is the scope a function, class, module, ISR, etc.?
- core_intent: Main task type (e.g., generate_code, refactor_code, test_code, configure).
- certainty: Is the intent explicit, implicit, or ambiguous?
- timing_requirements: Any explicit timing/real-time requirements (e.g., max latency, period).
- memory_constraints: RAM/ROM/stack limits or requirements.
- platform: Hardware/RTOS/OS target (e.g., STM32, FreeRTOS).
- peripherals: Which HW peripherals should be used.
- external_dependencies: Any libraries or drivers to be used/avoided.
- safety_requirements: Standards or coding rules to follow (e.g., MISRA).
- power_constraints: Requirements related to power management/sleep.

Prompt: "{prompt}"

Respond with only the JSON object.
'''

def extract_dev_intent(prompt):
    llm_prompt = DEV_INTENT_PROMPT.format(prompt=prompt)
    response = query_llm(llm_prompt, model=MODEL, temperature=TEMPERATURE)
    try:
        result = json.loads(response)
        # Schema stability: ensure all keys exist
        for key in [
            "goal", "how", "functions", "num_functions", "variables", "num_variables",
            "target_scope", "core_intent", "certainty", "timing_requirements",
            "memory_constraints", "platform", "peripherals", "external_dependencies",
            "safety_requirements", "power_constraints"
        ]:
            if key not in result:
                result[key] = None
        return result
    except Exception:
        return regex_extract_dev_intent(prompt)

def regex_extract_dev_intent(prompt):
    # Goal (WHAT)
    goal = None
    goal_match = re.search(
        r"(?:to|for|that|which)\s+((?:generate|print|output|compute|return|find|sort|calculate|implement|initialize|control|configure)[\w\s,.'\"-]+)",
        prompt, re.IGNORECASE
    )
    if goal_match:
        goal = goal_match.group(1).strip().rstrip('.')

    # HOW (constraints/methods)
    how_patterns = [
        r"(using recursion)",
        r"(no comments?)",
        r"(no explanation)",
        r"(use list comprehension)",
        r"(no libraries|no imports?)",
        r"(time complexity: [\w\s]+)",
        r"(space complexity: [\w\s]+)",
        r"(interrupt driven|polling mode|DMA|ISR)",
        r"(bare metal|RTOS|FreeRTOS|Zephyr)"
    ]
    how = []
    for pattern in how_patterns:
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        how.extend([m.strip() for m in matches])
    if not how:
        how = None

    # Functions/methods extraction (names, args, return type)
    function_pattern = re.compile(
        r"""(?:(?:function|method|procedure|routine|def|void|int|float|double|char|bool|static|inline|extern)\s+)?   # function keyword or C-style return type
        ([a-zA-Z_][a-zA-Z0-9_]*)                                           # function/method name
        \s*\(\s*([^)]*)\s*\)                                               # arguments
        (?:\s*->\s*([\w\[\],\s*]+))?                                       # optional python-style return type
        """, re.IGNORECASE | re.VERBOSE
    )
    functions = []
    for match in function_pattern.finditer(prompt):
        name, args, return_type = match.groups()
        arg_list = []
        if args:
            for arg in args.split(','):
                arg = arg.strip()
                type_match = re.match(r"(unsigned|signed|int|float|double|char|bool|void|struct|class)?\s*([a-zA-Z_][a-zA-Z0-9_]*)", arg)
                if type_match:
                    arg_type, arg_name = type_match.groups()
                    arg_list.append({'name': arg_name, 'type': arg_type if arg_type else None})
                else:
                    arg_list.append({'name': arg, 'type': None})
        if return_type:
            return_type = return_type.strip()
        else:
            ctype_match = re.match(r"(void|int|float|double|char|bool|struct|class)", prompt)
            return_type = ctype_match.group(1) if ctype_match else None
        functions.append({
            'name': name,
            'args': arg_list if arg_list else None,
            'return_type': return_type
        })
    num_functions = len(functions) if functions else 0

    # Variables (names/types if present)
    var_patterns = [
        r"(?:int|float|double|char|bool|unsigned|signed|long|short)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"(?:set|declare|create|initialize|use) variable[s]?\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*="
    ]
    variables = set()
    for pattern in var_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            variables.add(match)
    variables = list(variables)
    num_variables = len(variables) if variables else 0

    # Timing requirements
    timing_patterns = [
        r"(?:every|each)\s+(\d+(\.\d+)?\s*(ms|us|s|seconds?|microseconds?|milliseconds?))",
        r"(latency\s*<\s*\d+\s*(ms|us|s))",
        r"(max latency\s*:\s*\d+\s*(ms|us|s))"
    ]
    timing_requirements = []
    for pattern in timing_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            timing_requirements.append(' '.join([str(x) for x in match if x]))
    if not timing_requirements:
        timing_requirements = None

    # Memory constraints
    memory_patterns = [
        r"(must use less than\s*\d+\s*(KB|MB|bytes|words))",
        r"(no dynamic allocation)",
        r"(RAM usage\s*<\s*\d+\s*(KB|MB|bytes))"
    ]
    memory_constraints = []
    for pattern in memory_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            memory_constraints.append(' '.join([str(x) for x in match if x]))
    if not memory_constraints:
        memory_constraints = None

    # Platform (hardware/RTOS)
    platform_patterns = [
        r"\b(STM32|AVR|PIC|MSP430|ESP32|ARM Cortex|FreeRTOS|Zephyr|bare metal)\b"
    ]
    platform = None
    for pattern in platform_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            platform = match.group(1)
            break

    # Peripherals
    periph_patterns = [
        r"\b(ADC|UART|PWM|I2C|SPI|CAN|GPIO|DAC|RTC|Watchdog)\b"
    ]
    peripherals = []
    for pattern in periph_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            peripherals.append(match.upper())
    if not peripherals:
        peripherals = None

    # External dependencies
    external_patterns = [
        r"(HAL library|custom bootloader|proprietary driver|third[- ]party library)"
    ]
    external_dependencies = []
    for pattern in external_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            external_dependencies.append(match)
    if not external_dependencies:
        external_dependencies = None

    # Safety requirements
    safety_patterns = [
        r"(MISRA compliance|AUTOSAR|no unchecked casts|safety critical|ASIL)"
    ]
    safety_requirements = []
    for pattern in safety_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            safety_requirements.append(match)
    if not safety_requirements:
        safety_requirements = None

    # Power constraints
    power_patterns = [
        r"(must enter sleep mode between cycles|low power|power consumption\s*<\s*\d+\s*(mA|uA|W|mW))"
    ]
    power_constraints = []
    for pattern in power_patterns:
        for match in re.findall(pattern, prompt, re.IGNORECASE):
            power_constraints.append(match)
    if not power_constraints:
        power_constraints = None

    # Target scope
    if re.search(r"\bmodule\b", prompt, re.IGNORECASE):
        target_scope = "module"
    elif re.search(r"\bclass\b", prompt, re.IGNORECASE):
        target_scope = "class"
    elif re.search(r"\bscript\b", prompt, re.IGNORECASE):
        target_scope = "script"
    elif re.search(r"\bISR\b", prompt, re.IGNORECASE):
        target_scope = "interrupt_service_routine"
    elif re.search(r"\bmethod\b", prompt, re.IGNORECASE):
        target_scope = "method"
    else:
        target_scope = "function"

    # Core intent
    if "refactor" in prompt.lower():
        core_intent = "refactor_code"
    elif "test" in prompt.lower():
        core_intent = "test_code"
    elif "configure" in prompt.lower() or "setup" in prompt.lower():
        core_intent = "configure"
    else:
        core_intent = "generate_code"

    certainty = "implicit"

    return {
        "goal": goal,
        "how": how,
        "functions": functions if functions else None,
        "num_functions": num_functions,
        "variables": variables if variables else None,
        "num_variables": num_variables,
        "target_scope": target_scope,
        "core_intent": core_intent,
        "certainty": certainty,
        "timing_requirements": timing_requirements,
        "memory_constraints": memory_constraints,
        "platform": platform,
        "peripherals": peripherals,
        "external_dependencies": external_dependencies,
        "safety_requirements": safety_requirements,
        "power_constraints": power_constraints
    }

# --------- USER INTENT EXTRACTION ----------

USER_INTENT_PROMPT = '''
Given the following prompt, extract the user's underlying motivation as a single sentence explaining WHY the user would want the RESULT of the code to be generated.
Do not describe HOW the code works, only WHY the user would want to use it.

Prompt: "{prompt}"

Respond with only the WHY statement as a string.
'''

def extract_user_intent(prompt):
    llm_prompt = USER_INTENT_PROMPT.format(prompt=prompt)
    response = query_llm(llm_prompt, model=MODEL, temperature=TEMPERATURE)
    why = response.strip().strip('"').strip("'")
    if len(why) < 8 or why.lower() in ["to test code", "to see results", "for fun"]:
        why = regex_extract_user_why(prompt)
    return why

def regex_extract_user_why(prompt):
    # Heuristic fallback for WHY (embedded/system context included)
    pl = prompt.lower()
    if "fibonacci" in pl:
        return "To generate or analyze a mathematical sequence"
    if "sequence" in pl or "series" in pl:
        return "To generate or analyze a numerical sequence"
    if "sort" in pl:
        return "To arrange data for further processing or display"
    if "prime" in pl:
        return "To identify or analyze prime numbers"
    if "interrupt" in pl or "ISR" in pl:
        return "To handle real-time events in embedded systems"
    if "adc" in pl:
        return "To acquire and process analog sensor data"
    if "uart" in pl:
        return "To enable device communication via serial protocol"
    if "pwm" in pl:
        return "To control hardware with precise timing"
    if "test" in pl:
        return "To verify correctness or performance of the code"
    return "To obtain the result for further analysis or use"
