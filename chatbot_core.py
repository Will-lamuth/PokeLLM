import requests
import json
import re
import random

# Load Pokémon database once
with open("pokemon_gen12_moveset.json") as f:
    pokemon_db = json.load(f)

# --- Utility Functions ---

def extract_moves(text):
    lines = text.splitlines()
    move_lines = []
    blocked_terms = {
        "atk", "def", "spa", "spd", "spe", "hp",
        "speed", "attack", "defense", "special attack", "special defense",
        "type", "nature", "moveset"
    }
    for line in lines:
        if re.match(r"^\s*[\-\+\u2022\*]\s*", line):
            move_name = re.sub(r"^\s*[\-\+\u2022\*]\s*", "", line).strip()
            if move_name.lower() in blocked_terms:
                continue
            if re.match(r"^[A-Z][A-Za-z0-9 \-']+$", move_name) and ":" not in move_name:
                move_lines.append(move_name)
    return move_lines

def detect_pokemon_names(text):
    return [name for name in pokemon_db if name.lower() in text.lower()]

def split_movesets_by_pokemon(text, pokemon_names):
    sections = {}
    current_name = None
    buffer = []
    for line in text.splitlines():
        match = next((name for name in pokemon_names if name.lower() in line.lower()), None)
        if match:
            if current_name and buffer:
                sections[current_name] = "\n".join(buffer)
                buffer = []
            current_name = match
        elif current_name:
            buffer.append(line)
    if current_name and buffer:
        sections[current_name] = "\n".join(buffer)
    return sections

def validate_moves(pokemon_name, moves):
    legal = set(pokemon_db.get(pokemon_name, {}).get("legal_moves", []))
    return [move for move in moves if move not in legal]

def suggest_legal_moves(pokemon_name, num_moves=4):
    legal_moves = pokemon_db.get(pokemon_name, {}).get("legal_moves", [])
    return legal_moves[:num_moves] if len(legal_moves) >= num_moves else legal_moves

def correct_team_movesets(text):
    pokemon_names = detect_pokemon_names(text)
    sections = split_movesets_by_pokemon(text, pokemon_names)
    corrected_text = text

    for name, block in sections.items():
        original_moves = extract_moves(block)
        illegal = validate_moves(name, original_moves)

        if illegal:
            legal_replacement = suggest_legal_moves(name, len(original_moves))
            move_block_pattern = r"(\*\s*Moveset:\s*\n)(?:[^\n]*\n)+"
            replacement_block = r"\1" + "\n".join(f"        + {m}" for m in legal_replacement) + "\n"
            new_block = re.sub(move_block_pattern, replacement_block, block)
            corrected_text = corrected_text.replace(block, new_block)
            print(f"\nCorrected illegal moves for {name}: Replaced with {', '.join(legal_replacement)}")

    return corrected_text

def build_grounded_prompt(user_input, pokemon_list):
    grounding_lines = ["Only use these moves for each Pokémon:\n"]
    for name in pokemon_list:
        moves = pokemon_db.get(name, {}).get("legal_moves", [])
        if moves:
            grounding_lines.append(f"{name}: {', '.join(moves)}")
    grounding_lines.append("\nDo not use any moves that are not in this list.")
    grounding_text = "\n".join(grounding_lines)
    return f"{grounding_text}\n\n{user_input.strip()}"

def query_llm(model, messages):
    response = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": model, "messages": messages},
        stream=True
    )
    if response.status_code != 200:
        print(f"\nError: {response.status_code}")
        print(response.text)
        return ""

    full_response = ""
    print("Assistant:", end=" ", flush=True)
    for line in response.iter_lines(decode_unicode=True):
        if line:
            try:
                json_data = json.loads(line)
                content = json_data.get("message", {}).get("content", "")
                print(content, end="", flush=True)
                full_response += content
            except json.JSONDecodeError:
                print(f"\n[Error parsing line: {line}]")
    print()

    return correct_team_movesets(full_response.strip())

# --- Shared message state and system prompt ---
model_name = "pokemon-assistant-v3"
system_prompt = """You are a Pokémon expert assistant that helps build competitive Smogon-style teams. 
You must only use legal Gen 1 and Gen 2 movesets for each Pokémon.
You will be given a list of legal moves for each Pokémon — do not use any moves outside of that list, even if they are competitively good in later generations.
Make sure the team includes 6 Pokémon to form a complete team, covering all necessary roles like offensive, defensive, and special attackers, and includes a balance of types.
Only build teams using Pokémon from the first and second generation.
Organize each team like this:

**Team:**

1. **[Pokémon Name]** (Type)
    * EV Spread: 252 HP / 252 Atk / 4 Spe
    * Moveset:
        + Move 1
        + Move 2
        + Move 3
        + Move 4
...repeat...

**Team Strategy:**
Briefly explain synergy and roles."""
messages = [{"role": "system", "content": system_prompt}]

# --- Optional CLI Mode ---
if __name__ == "__main__":
    print("Pokémon Assistant LLM (type 'exit' to quit)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        detected_names = detect_pokemon_names(user_input)
        grounded_prompt = build_grounded_prompt(user_input, detected_names) if detected_names else user_input
        print("grounded prompt: ", grounded_prompt)

        messages.append({"role": "user", "content": grounded_prompt})
        response_text = query_llm(model_name, messages)
        messages.append({"role": "assistant", "content": response_text})

        # Show legality check
        pokemon_names = detect_pokemon_names(user_input + " " + response_text)
        if pokemon_names:
            sections = split_movesets_by_pokemon(response_text, pokemon_names)
            for name, section in sections.items():
                moves = extract_moves(section)
                illegal = validate_moves(name, moves)
                if illegal:
                    print(f"\n⚠️ Warning: These moves are illegal for {name}: {', '.join(illegal)}")
                else:
                    print(f"\nAll moves for {name} are legal.")
