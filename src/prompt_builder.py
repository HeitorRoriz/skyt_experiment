# src/prompt_builder.py

def build_prompt_from_contract(contract):
    """
    Generates a prompt string for the LLM based on the contract fields.
    """
    lines = []
    # Build generic prompt based on contract fields
    if hasattr(contract, 'description') and contract.description:
        lines.append(f"Write a {contract.language} function named '{contract.function_name}' that {contract.description}.")
    else:
        # Fallback to generic prompt if no description provided
        lines.append(f"Write a {contract.language} function named '{contract.function_name}' that returns a {contract.output_type}.")

    if contract.required_logic:
        lines.append(f"Use {contract.required_logic}.")

    for constraint in contract.constraints:
        if constraint.lower() == "no comments":
            lines.append("Do not include comments.")
        if constraint.lower() == "no explanation":
            lines.append("Do not add explanations or text outside the code.")

    if contract.output_format and contract.output_format.lower() == "code only":
        lines.append("Output only the code.")

    return " ".join(lines)
