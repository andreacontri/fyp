import os
import requests

# Load your API key from an environment variable or config file
API_KEY = os.environ["OPENAI_API_KEY"]

import requests

def summarize_text(text, tokens = 100):
    """
    Utilize the OpenAI API to generate a summary of the provided text. This function makes an HTTP POST request
    to the OpenAI API endpoint to process the text summarization task.

    Args:
        text (str): The text to be summarized, typically extracted from a VTT file or similar content.

    Returns:
        str: The summarized text as returned by the OpenAI model, or None if an error occurs.
    """
    # Define the API endpoint and authorization headers
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    # print(int(tokens))d
    # Construct the data payload for the API request
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"Summarize this meeting in {str(int(tokens))} words:\n\n{text}"}],
        # "max_tokens": int(tokens),  # Set the maximum length of the summary
        "n": 1,  # Number of responses to generate
        "stop": None,  # Optional stopping character or sequence
        "temperature": 0.5,  # Sampling temperature
    }

    # Execute the POST request with the prepared headers and data
    response = requests.post(url, headers=headers, json=data)

    # Handle the response
    if response.status_code == 200:
        # Parse the JSON response to extract the summary
        summary = response.json()["choices"][0]["message"]["content"].strip()
        return summary
    else:
        # Log the error and return None if the request failed
        print(f"Error: {response.json()['error']['message']}")
        return None



def utility_text(text):
    """
    Utilize the OpenAI API to generate a summary of the provided text. This function makes an HTTP POST request
    to the OpenAI API endpoint to process the text summarization task.

    Args:
        text (str): The text to be summarized, typically extracted from a VTT file or similar content.

    Returns:
        str: The summarized text as returned by the OpenAI model, or None if an error occurs.
    """
    # Define the API endpoint and authorization headers
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    # print(int(tokens))
    # Construct the data payload for the API request
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"Identify all key points and key decisions made in this transcript:\n\n{text}"}],
        # "max_tokens": int(tokens),  # Set the maximum length of the summary
        "n": 1,  # Number of responses to generate
        "stop": None,  # Optional stopping character or sequence
        "temperature": 0.5,  # Sampling temperature
    }

    # Execute the POST request with the prepared headers and data
    response = requests.post(url, headers=headers, json=data)

    # Handle the response
    if response.status_code == 200:
        # Parse the JSON response to extract the summary
        summary = response.json()["choices"][0]["message"]["content"].strip()
        return summary
    else:
        # Log the error and return None if the request failed
        print(f"Error: {response.json()['error']['message']}")
        return None


# # Example usage
# text = "This is a long text that needs to be summarized."
# summary = summarize_text(text)
# if summary:
#     print(f"Summary: {summary}")