from ai.llm_handler import initialize_llm, initialize_prompt, handle_user_input
from langchain.memory import ConversationBufferMemory


def test_handle_user_input():
    llm = initialize_llm()
    prompt = initialize_prompt()
    memory = ConversationBufferMemory()

    user_input = "My name is Nam. Nice too meet you. Can you give me a recipe for spaghetti?"

    generator = handle_user_input(user_input, memory, llm, prompt)

    print("Output:")
    for output in generator:
        print(output)


if __name__ == "__main__":
    test_handle_user_input()
