import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Store chat history
history = [
    {"role": "system", "content": """you are jarvis, chill guy, don't act as a robot be more normal and human"""}
]

def send_to_llm(text):
    global history  # Keep track of past messages

    client = Groq(api_key=GROQ_API_KEY)

    # Add user input to history
    history.append({"role": "user", "content": text})

    # Send entire conversation history
    chat_completion = client.chat.completions.create(
        messages=history,
        model="llama-3.3-70b-versatile",
    )

    # Get LLM response
    response_text = chat_completion.choices[0].message.content

    # Add assistant response to history
    history.append({"role": "assistant", "content": response_text})

    print("LLM Response:", response_text)
    return response_text

def parse_llm_response(response_text):
    """
    Parse the LLM's response into a conversational reply and a servo command.
    """
    if "CMD:POS:" not in response_text:
        return response_text, "CMD:NO_COMMAND"

    # Split the response into conversational text and command
    parts = response_text.split("CMD:POS:")
    conversational_reply = parts[0].strip()  # Text before the command
    command_part = parts[1].strip()  # Text after "CMD:POS:"

    # Extract the command (e.g., "180") and any trailing text
    command_line = "CMD:POS:" + command_part.split()[0].strip()  # Extract the first word after "CMD:POS:"
    return conversational_reply, command_line

def parse_command(command_line):
    """
    Extract the servo command from the command line.
    """
    if command_line.startswith("CMD:POS:"):
        try:
            angle = int(command_line.split("CMD:POS:")[1])
            if 0 <= angle <= 180:
                return f"POS:{angle}"
        except ValueError:
            pass
    return None

# Main loop
while True:
    text = input('You: ')
    llm_response = send_to_llm(text)
    conversational_reply, command_line = parse_llm_response(llm_response)

    # Print conversational reply
    print("\nLLM Conversational Reply:")
    print(conversational_reply)

    # Extract and print servo command
    servo_command = parse_command(command_line)
    if servo_command:
        print(f"Servo Command: {servo_command}")
    else:
        print("No valid servo command detected.")