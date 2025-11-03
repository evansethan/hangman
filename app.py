import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document

st.title("Hangman Chat")

# Initialize LLM
llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "vectorstore" not in st.session_state:
    # Get LLM to generate a secret word
    word_gen_msg = SystemMessage(content="Generate a single random common English word that is 6-8 letters long. Reply with ONLY the word, nothing else.")
    word_response = llm.invoke([word_gen_msg])
    secret_word = word_response.content.strip().lower()
    
    # Store game state in vectorstore
    docs = [
        Document(page_content=f"SECRET_WORD:{secret_word}", metadata={"type": "word"}),
        Document(page_content="GUESSED_LETTERS:", metadata={"type": "guessed"}),
        Document(page_content="WRONG_GUESSES:0", metadata={"type": "wrong"})
    ]
    
    embeddings = OpenAIEmbeddings()
    st.session_state.vectorstore = FAISS.from_documents(docs, embeddings)
    
    # Initial greeting
    system_msg = SystemMessage(content=f"""You are a friendly hangman game host. The secret word has {len(secret_word)} letters. 
    Be conversational and encouraging. When the user guesses a letter, I'll tell you if it's correct and update the word display.
    Start by greeting the player and explaining the game.""")
    
    initial_response = llm.invoke([system_msg])
    st.session_state.messages.append({"role": "assistant", "content": initial_response.content})

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_input = st.chat_input("Guess a letter or the whole word...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # Retrieve game state from vectorstore
    docs = st.session_state.vectorstore.similarity_search("SECRET_WORD GUESSED_LETTERS WRONG_GUESSES", k=3)
    
    secret_word = ""
    guessed_letters = ""
    wrong_guesses = 0
    
    for doc in docs:
        if "SECRET_WORD:" in doc.page_content:
            secret_word = doc.page_content.split(":")[1]
        elif "GUESSED_LETTERS:" in doc.page_content:
            guessed_letters = doc.page_content.split(":")[1]
        elif "WRONG_GUESSES:" in doc.page_content:
            wrong_guesses = int(doc.page_content.split(":")[1])
    
    # Process the guess
    guess = user_input.strip().lower()
    
    if len(guess) == 1:
        # Single letter guess
        if guess in guessed_letters:
            status = f"You already guessed '{guess}'!"
        else:
            guessed_letters += guess
            if guess in secret_word:
                status = f"Yes! '{guess}' is in the word!"
            else:
                wrong_guesses += 1
                status = f"Sorry, '{guess}' is not in the word. Wrong guesses: {wrong_guesses}/6"
    else:
        # Full word guess
        if guess == secret_word:
            status = f"🎉 You won! The word was '{secret_word}'!"
        else:
            wrong_guesses += 1
            status = f"Sorry, that's not the word. Wrong guesses: {wrong_guesses}/6"
    
    # Build current word display
    display = ""
    for letter in secret_word:
        if letter in guessed_letters:
            display += letter + " "
        else:
            display += "_ "
    
    # Check win/lose
    if all(letter in guessed_letters for letter in secret_word):
        game_status = f"🎉 YOU WON! The word was '{secret_word}'!"
    elif wrong_guesses >= 6:
        game_status = f"💀 Game Over! The word was '{secret_word}'"
    else:
        game_status = f"Word: {display}\nGuessed letters: {', '.join(guessed_letters)}\nWrong guesses: {wrong_guesses}/6"
    
    # Update vectorstore
    updated_docs = [
        Document(page_content=f"SECRET_WORD:{secret_word}", metadata={"type": "word"}),
        Document(page_content=f"GUESSED_LETTERS:{guessed_letters}", metadata={"type": "guessed"}),
        Document(page_content=f"WRONG_GUESSES:{wrong_guesses}", metadata={"type": "wrong"})
    ]
    st.session_state.vectorstore = FAISS.from_documents(updated_docs, OpenAIEmbeddings())
    
    # Get LLM response
    context = f"{status}\n\n{game_status}"
    
    system_msg = SystemMessage(content="""You are a friendly hangman game host. React naturally to the player's guess. 
    Be encouraging, playful, and conversational. Comment on their progress.""")
    
    history = [system_msg]
    for m in st.session_state.messages[-6:]:
        if m["role"] == "user":
            history.append(HumanMessage(content=m["content"]))
        else:
            history.append(AIMessage(content=m["content"]))
    
    history.append(HumanMessage(content=f"I guessed: {user_input}\n\nGame status:\n{context}"))
    
    response = llm.invoke(history)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response.content})
    with st.chat_message("assistant"):
        st.write(response.content)
    
    st.rerun()