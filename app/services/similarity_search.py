from datetime import datetime
from .database.vector_store import VectorStore
from .services.synthesizer import Synthesizer
from timescale_vector import client

# Initialiser VectorStore
vec = VectorStore()

# --------------------------------------------------------------
# Question sur un manga
# --------------------------------------------------------------

# relevant_question = "Que se passe-t-il dans le volume 1 de 008 Apprenti espion?"
# results = vec.search(relevant_question, limit=3)
#
# response = Synthesizer.generate_response(question=relevant_question, context=results)
#
# print(f"\n{response.answer}")
# print("\nProcessus de réflexion:")
# for thought in response.thought_process:
#     print(f"- {thought}")
# print(f"\nContexte suffisant: {response.enough_context}")

# --------------------------------------------------------------
# Question non pertinente
# --------------------------------------------------------------

# irrelevant_question = "Quel temps fait-il à Tokyo?"
#
# results = vec.search(irrelevant_question, limit=3)
#
# response = Synthesizer.generate_response(question=irrelevant_question, context=results)
#
# print(f"\n{response.answer}")
# print("\nProcessus de réflexion:")
# for thought in response.thought_process:
#     print(f"- {thought}")
# print(f"\nContexte suffisant: {response.enough_context}")

# --------------------------------------------------------------
# Filtrage par métadonnées
# --------------------------------------------------------------

# metadata_filter = {"serie_title": "008 Apprenti espion"}
#
# results = vec.search(relevant_question, limit=3, metadata_filter=metadata_filter)
#
# response = Synthesizer.generate_response(question=relevant_question, context=results)
#
# print(f"\n{response.answer}")
# print("\nProcessus de réflexion:")
# for thought in response.thought_process:
#     print(f"- {thought}")
# print(f"\nContexte suffisant: {response.enough_context}")

# --------------------------------------------------------------
# Filtrage avancé avec Predicates
# --------------------------------------------------------------

# predicates = client.Predicates("genre", "==", "Manga")
# results = vec.search(relevant_question, limit=3, predicates=predicates)
#
#
# predicates = client.Predicates("genre", "==", "Manga") | client.Predicates(
#     "serie_title", "==", "008 Apprenti espion"
# )
# results = vec.search(relevant_question, limit=3, predicates=predicates)
#
#
# predicates = client.Predicates("genre", "==", "Manga") & client.Predicates(
#     "volume_number", ">", 1
# )
# results = vec.search(relevant_question, limit=3, predicates=predicates)

# --------------------------------------------------------------
# Filtrage basé sur le temps
# --------------------------------------------------------------

# # Septembre — Retour de résultats
# time_range = (datetime(2024, 9, 1), datetime(2024, 9, 30))
# results = vec.search(relevant_question, limit=3, time_range=time_range)
#
# # Août — Aucun résultat retourné
# time_range = (datetime(2024, 8, 1), datetime(2024, 8, 30))
# results = vec.search(relevant_question, limit=3, time_range=time_range)
