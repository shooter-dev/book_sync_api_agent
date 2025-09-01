# Initialiser VectorStore
from timescale_vector import client

from app.database.vector_store import VectorStore
from app.services.synthesizer import Synthesizer
#from app.similarity_search import relevant_question

vec = VectorStore()
vec.create_tables()

def main():
    relevant_question = "Quel serie et plus centré dans les categori (action, shomen ou senen)."
    results = vec.search(relevant_question, limit=5)

    response = Synthesizer.generate_response(question=relevant_question, context=results)

    print(f"\n{response.answer}")
    print("\nProcessus de réflexion:")
    for thought in response.thought_process:
        print(f"- {thought}")
    print(f"\nContexte suffisant: {response.enough_context}")


if __name__ == '__main__':
    main()
