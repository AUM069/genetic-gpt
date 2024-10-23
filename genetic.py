import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from groq import Groq
import speech_recognition as sr

# Set page config at the very beginning
st.set_page_config(page_title="Genetics-GPT", layout="wide")

# Initialize Groq client
client = Groq(
    api_key="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"  # Replace with your actual Groq API key
)

ncbi_api_key = "1a0ae67dd7837c7beb18cd6ca75122b13b09"

# Initialize chat history with a more focused system message
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an AI assistant specialized in genetics. Provide accurate and helpful information about genetics topics, and help search for research papers."}
    ]

st.title("Genetics-GPT and Research Paper Finder")

# Function to fetch papers from arXiv
def fetch_arxiv_papers(topic: str, max_results: int = 3):
    """Fetch research papers from arXiv based on the given topic."""
    base_url = "http://export.arxiv.org/api/query?"
    query = f"search_query=all:{topic}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
    response = requests.get(base_url + query)
    if response.status_code != 200:
        st.error("Failed to fetch papers from arXiv. Please try again later.")
        return []
    root = ET.fromstring(response.content)
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
        authors = ", ".join([author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')])
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        papers.append({
            "title": title,
            "authors": authors,
            "year": datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").year,
            "url": link,
            "summary": summary
        })
    return papers

# Chat function using Groq API
def CustomChatGPT(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    resp = client.chat.completions.create(
        model="mixtral-8x7b-32768",  # You can change this to the appropriate Groq model
        messages=st.session_state.messages,
        temperature=0.5,
        max_tokens=800
    )
    output_tokens = resp.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": output_tokens})
    return output_tokens

# Function for transcribing audio input
def transcribe_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening... Speak your query.")
        audio = r.listen(source)
        st.write("Processing speech...")
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.write("Sorry, I couldn't understand that.")
        return None
    except sr.RequestError:
        st.write("Sorry, there was an error processing your speech.")
        return None

# Main function
def main():
    # Display chat history
    for message in st.session_state.messages[1:]:  # Skip the system message
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # User input options
    input_option = st.radio("Choose input method:", ("Text", "Voice"))

    if input_option == "Text":
        user_input = st.chat_input("Write your query or search for research papers:")
    else:
        if st.button("Start Speaking"):
            user_input = transcribe_audio()
            if user_input:
                st.write(f"You said: {user_input}")
        else:
            user_input = None

    if user_input:
        # Determine if the input is for searching research papers or a genetics query
        if "paper" in user_input.lower() or "research" in user_input.lower():
            with st.spinner("Searching for papers..."):
                papers = fetch_arxiv_papers(user_input)
            if papers:
                st.subheader(f"Top Research Papers on '{user_input}' :")
                for i, paper in enumerate(papers, 1):
                    with st.expander(f"{i}. {paper['title']} ({paper['year']})"):
                        st.write(f"Authors: {paper['authors']}")
                        st.write(f"Year: {paper['year']}")
                        st.write(f"Summary: {paper['summary']}")
                        st.markdown(f"[Read Paper]({paper['url']})")
            else:
                st.info("No papers found for the given topic.")
        else:
            # Genetics chat using CustomChatGPT
            response = CustomChatGPT(user_input)
            with st.chat_message("assistant"):
                st.write(response)

if __name__ == "__main__":
    main()
