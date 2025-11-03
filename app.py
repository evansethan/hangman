import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

st.title("🎮 Hangman Chat")

llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

if "messages" not in st.session_state:
    st.session_state.messages = []
    word_response = llm.invoke([SystemMessage(content="Generate a single random common English word that is 6-8 letters long. Reply with ONLY the word, nothing else.")])
    st.session_state.secret_word = word_response.content.strip().lower()
    st.session_state.guessed = ""
    st.session_state.wrong = 0
    greeting = llm.invoke([SystemMessage(content=f"You are a friendly hangman game host. The secret word has {len(st.session_state.secret_word)} letters. Greet the player and explain the game briefly.")])
    st.session_state.messages.append({"role": "assistant", "content": greeting.content})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Guess a letter or the whole word...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    guess = user_input.strip().lower()
    
    if len(guess) == 1 and guess not in st.session_state.guessed:
        st.session_state.guessed += guess
        if guess not in st.session_state.secret_word:
            st.session_state.wrong += 1
    elif len(guess) > 1 and guess != st.session_state.secret_word:
        st.session_state.wrong += 1
    
    display = " ".join([l if l in st.session_state.guessed else "_" for l in st.session_state.secret_word])
    won = all(l in st.session_state.guessed for l in st.session_state.secret_word) or guess == st.session_state.secret_word
    lost = st.session_state.wrong >= 6
    
    status = f"Word: {display}\nGuessed: {', '.join(st.session_state.guessed)}\nWrong: {st.session_state.wrong}/6"
    if won:
        status = f"🎉 YOU WON! The word was '{st.session_state.secret_word}'!"
    elif lost:
        status = f"💀 Game Over! The word was '{st.session_state.secret_word}'"
    
    prompt = f"I guessed: {user_input}\n\n{status}\n\nReact naturally and be encouraging!"
    response = llm.invoke([SystemMessage(content="You are a friendly hangman game host. Be conversational."), HumanMessage(content=prompt)])
    
    st.session_state.messages.append({"role": "assistant", "content": response.content})
    st.rerun()