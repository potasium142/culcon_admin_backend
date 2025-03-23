from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from config import env
import os
import re

os.environ["GROQ_API_KEY"] = env.GROQ_API_KEY
os.environ["LANGCHAIN_TRACING_V2"] = env.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = env.LANGCHAIN_API_KEY


def initialize_llm():
    return ChatGroq(model="llama3-8b-8192")


def initialize_prompt():
    prompt_template = """
    You are a helpful, creative, and friendly AI assistant specializing in cooking and culinary advice. Answer the user's question concisely and accurately, focusing on recipes, cooking techniques, and food-related topics.

    Use the chat history to maintain context and continuity in the conversation. Refer to previous questions or answers if they are relevant to the current query.

    If the user asks for suggestions or ideas, provide creative and practical advice related to cooking or recipes. Always respond in a friendly and engaging tone, and encourage the user to explore new ideas in cooking.

    Chat History:
    {chat_history}

    User: {question}
    AI:
    """
    return PromptTemplate(
        input_variables=["chat_history", "question"],
        template=prompt_template
    )


def handle_user_input(user_input, memory, llm, prompt):
    try:
        chat_history = memory.load_memory_variables({}).get("chat_history", "")
        if not chat_history:
            chat_history = ""

        formatted_prompt = prompt.format(
            chat_history=chat_history, question=user_input)
        print(f"Formatted Prompt: {formatted_prompt}")

        partial_response = ""
        buffer = ""

        for chunk in llm.stream(formatted_prompt):
            if hasattr(chunk, "content"):
                current_chunk = chunk.content
            else:
                current_chunk = str(chunk)

            buffer += current_chunk

            while any(punct in buffer for punct in [".", "?", "!"]):
                end_idx = -1
                for punct in [".", "?", "!"]:
                    if punct in buffer:
                        end_idx = buffer.index(punct) + 1
                        break

                if end_idx != -1:
                    sentence = buffer[:end_idx].strip()
                    buffer = buffer[end_idx:].lstrip()
                    if sentence:
                        yield sentence
                        partial_response += sentence + " "

        if buffer.strip():
            yield buffer.strip()
            partial_response += buffer.strip()

        memory.save_context({"input": user_input}, {
                            "output": partial_response.strip()})
    except Exception as e:
        import traceback
        print("Error Traceback:", traceback.format_exc())
        yield f"Error: {str(e)}"
