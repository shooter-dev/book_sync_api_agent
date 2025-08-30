from datetime import datetime
import uuid
import time

import pandas as pd
from app.database.vector_store import VectorStore

# Initialiser VectorStore
vec = VectorStore()

# Lire le fichier CSV
df = pd.read_csv("data/volume_content.csv", sep=";")

# Variable pour suivre le progrès
total_rows = len(df)

print(f"Traitement de {total_rows} lignes une par une avec insertion immédiate...")

# Créer les tables
vec.create_tables()

# Traiter ligne par ligne avec insertion immédiate
for i in range(total_rows):
    print(f"\n=== Ligne {i + 1}/{total_rows} ===")
    
    # Extraire une seule ligne
    row = df.iloc[i]

    # Traiter la ligne
    start_time = time.time()
    
    # Formatter le contenu
    content = f"Serie: {row['serie_title']}\nGenre: {row['genre']}\nCategorie: {row['categorie']}\nVolume {row['volume_number']}: {row['content']}"
    embedding = vec.get_embedding(content)
    
    # Créer l'enregistrement (conversion des types pandas vers Python natifs)
    record_data = pd.DataFrame([{
        "id": str(uuid.uuid4()),
        "metadata": {
            "serie_id": str(row["serie_id"]),
            "serie_title": str(row["serie_title"]),
            "genre": str(row["genre"]) if pd.notna(row["genre"]) else "No Genre",
            "categorie": str(row["categorie"]) if pd.notna(row["categorie"]) else "No Categorie",
            "volume_id": str(row["volume_id"]),
            "volume_number": int(row["volume_number"]),
            "created_at": datetime.now().isoformat(),
        },
        "contents": content,
        "embedding": embedding,
    }])
    
    # Insérer immédiatement en base
    vec.upsert(record_data)
    
    elapsed_time = time.time() - start_time
    print(f"Ligne {i + 1} traitée et insérée en {elapsed_time:.1f} secondes")
    
    # Vérifier le nombre d'enregistrements en base
    with vec.conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM embeddings')
        count = cur.fetchone()[0]
        print(f"Total en base : {count} enregistrements")


# Créer l'index après l'insertion de toutes les données
print("\nCréation de l'index...")
# vec.create_index()  # Désactivé car text-embedding-3-large (3072 dim) > 2000 dim max pour HNSW
print("Index désactivé : text-embedding-3-large (3072 dim) > limite HNSW (2000 dim)")

print(f"\nInsertion terminée ! {total_rows} enregistrements traités.")
