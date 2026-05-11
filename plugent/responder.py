"""Response generation module using Groq."""

from groq import Groq


SYSTEM_PROMPT = """You are a helpful assistant. Answer ONLY based on
the provided context. If the answer is not in the context, say
'I don't have information about that.'"""


def get_answer(question: str, context_chunks: list[str], groq_api_key: str) -> str:
    """Generate an answer using Groq LLM.

    Args:
        question: User question.
        context_chunks: List of context text chunks.
        groq_api_key: Groq API key.

    Returns:
        Generated answer string.
    """
    client = Groq(api_key=groq_api_key)

    context_text = "\n".join(f"{i+1}. {chunk}" for i, chunk in enumerate(context_chunks))

    user_message = f"Context:\n{context_text}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )

    return response.choices[0].message.content


class Responder:
    """Generate responses using LLM."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model
        self.api_key = api_key

    def respond(self, prompt: str, context: str = None):
        """Generate a response."""
        raise NotImplementedError