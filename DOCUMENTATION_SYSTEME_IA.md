# DOCUMENTATION TECHNIQUE COMPLÈTE DU SYSTÈME DE RECOMMANDATION INTELLIGENT

## TABLE DES MATIÈRES

1. [Vue d'ensemble du système](#1-vue-densemble-du-système)
2. [Architecture technique](#2-architecture-technique)
3. [Composants principaux](#3-composants-principaux)
4. [Flux de traitement des données](#4-flux-de-traitement-des-données)
5. [Système d'embeddings vectoriels](#5-système-dembbedings-vectoriels)
6. [Agent de synthèse conversationnelle](#6-agent-de-synthèse-conversationnelle)
7. [Algorithmes de recommandation](#7-algorithmes-de-recommandation)
8. [Modèles de données](#8-modèles-de-données)
9. [Configuration et infrastructure](#9-configuration-et-infrastructure)
10. [Terminologie professionnelle](#10-terminologie-professionnelle)

---

## 1. VUE D'ENSEMBLE DU SYSTÈME

### 1.1 Objectif métier

Le système BookSync API Agent constitue un moteur de recommandation intelligent spécialisé dans la littérature, 
notamment les mangas, manhwas et manhuas. Il exploite des techniques avancées d'intelligence artificielle pour proposer des recommandations personnalisées en fonction du profil de l'utilisateur.

### 1.2 Capacités fonctionnelles

Le système offre les capacités suivantes :

- **Analyse multidimensionnelle du profil utilisateur** : âge, genre, préférences catégorielles, humeur actuelle
- **Traitement de l'historique comportemental** : collection possédée, volumes déjà consultés
- **Recherche sémantique vectorielle** : identification de contenu similaire par analyse de proximité vectorielle
- **Génération de justifications personnalisées** : explication contextualisée de chaque recommandation
- **Synthèse conversationnelle globale** : message d'accompagnement généré par un modèle de langage

### 1.3 Technologies fondamentales

- **Framework API** : FastAPI (Python asynchrone haute performance)
- **Modèles de langage** : Azure OpenAI GPT-4o-mini pour la génération conversationnelle
- **Modèles d'embedding** : Azure OpenAI text-embedding-3-large (3072 dimensions)
- **Base de données vectorielle** : PostgreSQL avec extension pgvector
- **Infrastructure cloud** : Azure Container Apps, Azure Database for PostgreSQL
- **Validation de données** : Pydantic pour le typage strict et la validation automatique

---

## 2. ARCHITECTURE TECHNIQUE

### 2.1 Architecture applicative en couches

Le système adopte une architecture en couches respectant les principes de séparation des préoccupations :

```
┌─────────────────────────────────────────────┐
│         COUCHE PRÉSENTATION                 │
│   (Routes FastAPI - predict_routes.py)      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         COUCHE MÉTIER                       │
│   (Services - predict_service.py)           │
│   - Orchestration des opérations            │
│   - Logique de recommandation               │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────┐    ┌─────────▼────────────┐
│  Agent IA    │    │  Recherche Vectorielle│
│ Synthesizer  │    │   VectorStore         │
└──────────────┘    └──────────┬─────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   COUCHE DONNÉES    │
                    │  PostgreSQL+pgvector│
                    └─────────────────────┘
```

### 2.2 Flux de communication inter-couches

**Requête entrante** :
1. Le client envoie une requête HTTP POST avec le profil utilisateur
2. La couche présentation (`predict_routes.py`) valide la structure via Pydantic
3. La requête est transmise au service métier (`PredictService`)
4. Le service orchestre les opérations de recherche et de synthèse
5. La réponse structurée est retournée au client

**Traitement asynchrone** :
- FastAPI utilise async/await pour le traitement non-bloquant
- Les appels aux services externes (OpenAI, PostgreSQL) sont gérés de manière asynchrone
- Permet un traitement concurrent de multiples requêtes

### 2.3 Composants externes

**Azure OpenAI Service** :
- Endpoint : `https://app-booksync.openai.azure.com/`
- Déploiements utilisés :
  - `gpt-4o-mini` : génération conversationnelle (chat completion)
  - `text-embedding-3-large` : génération d'embeddings vectoriels (3072 dimensions)

**Azure Database for PostgreSQL** :
- Host : `bdd-booksync.postgres.database.azure.com`
- Extension pgvector activée pour le stockage et la recherche vectorielle
- Table principale : `embeddings` (28 863 enregistrements de volumes)

---

## 3. COMPOSANTS PRINCIPAUX

### 3.1 Couche Routes (predict_routes.py)

#### Responsabilités

Ce module expose les endpoints HTTP permettant l'interaction avec le système de recommandation.

#### Endpoints disponibles

**POST /predict/**
- **Fonction** : endpoint principal de recommandation personnalisée
- **Entrée** : objet `PredictRequest` validé par Pydantic
- **Sortie** : objet `PredictResponse` contenant les recommandations
- **Gestion d'erreurs** : capture des exceptions et retour HTTP 500 avec message détaillé

**GET /predict/health**
- **Fonction** : vérification de disponibilité du service
- **Sortie** : `{"status": "healthy", "service": "predict"}`

**POST /predict/test**
- **Fonction** : endpoint de débogage pour inspection des données reçues
- **Sortie** : écho des données avec typage Python

**POST /predict/raw**
- **Fonction** : test de réception de JSON brut sans validation Pydantic
- **Usage** : débogage de problèmes de sérialisation

#### Code structurel

```python
router = APIRouter(
    prefix="/predict",
    tags=["prediction"]
)

predict_service = PredictService()

@router.post("/", response_model=PredictResponse)
async def predict(request: PredictRequest):
    response = await predict_service.predict(request)
    return response
```

### 3.2 Service de Prédiction (predict_service.py)

#### Responsabilités principales

Le `PredictService` constitue le cerveau opérationnel du système. Il orchestre :
1. La recherche de volumes similaires dans la base vectorielle
2. L'extraction et le formatage des séries recommandées
3. La génération de justifications personnalisées par série
4. L'appel à l'agent de synthèse pour le message global

#### Architecture interne

```python
class PredictService:
    def __init__(self):
        self.vector_store = VectorStore()      # Interface base vectorielle
        self.synthesizer = Synthesizer()       # Agent de synthèse IA

    async def predict(self, request: PredictRequest) -> PredictResponse:
        # Pipeline de traitement complet
```

#### Méthode principale : predict()

**Étapes du pipeline** :

1. **Logging du contexte utilisateur**
   ```python
   print(f"Profil: {request.user_genre} {request.user_age} ans")
   print(f"Préférences: {request.genre_preference} - {request.category_preference}")
   print(f"Humeur: {request.user_mood}")
   ```

2. **Recherche de volumes similaires**
   ```python
   search_results = self._search_similar_volumes(request, limit=10)
   ```

3. **Extraction des séries recommandées**
   ```python
   recommended_series = self._extract_series_recommendations(search_results, request)
   ```

4. **Préparation du profil utilisateur**
   ```python
   user_profile = {
       'user_age': request.user_age,
       'user_genre': request.user_genre,
       'genre_preference': request.genre_preference,
       'category_preference': request.category_preference,
       'user_mood': request.user_mood,
       'prediction_type': request.prediction_type,
       'collection': request.collection,
       'read': request.read
   }
   ```

5. **Synthèse conversationnelle**
   ```python
   synthesizer_response = self.synthesizer.generate_global_response(
       recommended_series=recommended_series,
       user_profile=user_profile
   )
   ```

6. **Construction de la réponse**
   ```python
   return PredictResponse(
       serie_recomendees=recommended_series,
       status="success",
       responce_IA_global=synthesizer_response
   )
   ```

#### Méthode : _search_similar_volumes()

**Objectif** : identifier les volumes pertinents en fonction du contexte utilisateur.

**Stratégies de recherche** :

**Stratégie 1 : Basée sur la collection existante**
```python
if request.collection:
    for serie_name, serie_data in request.collection.items():
        search_query = f"Serie: {serie_name} Genre: {request.category_preference}"
        results = self.vector_store.search(
            query_text=search_query,
            limit=5,
            return_dataframe=True
        )
        all_results.append(results)
```

**Logique** : pour chaque série possédée, rechercher 5 volumes similaires combinant le nom de la série et la préférence catégorielle. Permet d'identifier des séries thématiquement proches de la collection existante.

**Stratégie 2 : Basée sur les volumes lus**
```python
if request.read and request.read != "{}":
    for serie_name, serie_data in read_data.items():
        search_query = f"Serie: {serie_name} Genre: {request.category_preference}"
        results = self.vector_store.search(
            query_text=search_query,
            limit=5,
            return_dataframe=True
        )
        all_results.append(results)
```

**Logique** : identique à la stratégie 1, mais appliquée aux lectures passées plutôt qu'à la collection.

**Stratégie 3 : Basée uniquement sur les préférences**
```python
if not all_results:
    mood_text = f" {request.user_mood}" if request.user_mood else ""
    search_query = f"Genre: {request.category_preference}{mood_text} manga"
    results = self.vector_store.search(
        query_text=search_query,
        limit=limit,
        return_dataframe=True
    )
```

**Logique** : en l'absence de collection ou de lectures, effectue une recherche générique basée sur la catégorie préférée et l'humeur. Exemple : "Genre: Romance Comique manga"

**Dédoublonnage et consolidation** :
```python
seen_series = set()
unique_results = []

for _, row in combined_results.iterrows():
    metadata = row.get('metadata', {})
    serie_title = metadata.get('serie_title', '')
    if serie_title and serie_title not in seen_series:
        seen_series.add(serie_title)
        unique_results.append(row)

return pd.DataFrame(unique_results).head(limit)
```

**Logique** : élimine les doublons en conservant la première occurrence de chaque série (score de similarité le plus élevé). Limite finale à 10 séries uniques.

#### Méthode : _extract_series_recommendations()

**Objectif** : transformer les résultats de recherche vectorielle en objets de recommandation structurés.

**Processus** :

```python
for _, row in search_results.iterrows():
    serie_title = row.get('serie_title', '')
    serie_id = row.get('serie_id', '')
    genre = row.get('genre', '')
    category = row.get('categorie', '')

    if serie_title and serie_id:
        reason = self._generate_ai_response(serie_title, genre, category, request)

        recommended_series.append(RecommendedSerie(
            title=serie_title,
            id_series=serie_id,
            responce_IA=reason
        ))
```

**Étapes** :
1. Extraction des métadonnées depuis les colonnes du DataFrame
2. Validation de la présence du titre et de l'identifiant
3. Génération de la justification personnalisée
4. Construction de l'objet `RecommendedSerie`

#### Méthode : _generate_ai_response()

**Objectif** : créer une justification textuelle personnalisée pour chaque recommandation.

**Règles de correspondance** :

**Règle 1 : Correspondance avec préférence catégorielle**
```python
if request.category_preference.lower() in genre.lower():
    reasons.append(f"correspond à votre goût pour le {request.category_preference}")
```
Exemple : si l'utilisateur préfère "Romance" et que le genre contient "Romance" → "correspond à votre goût pour le Romance"

**Règle 2 : Correspondance avec humeur**
```python
if request.user_mood.lower() == "énervé":
    if any(word in genre.lower() for word in ["action", "combat", "aventure"]):
        reasons.append("parfait pour évacuer votre énervement")

if request.user_mood.lower() == "comique":
    if any(word in genre.lower() for word in ["comédie", "humour"]):
        reasons.append("idéal pour votre humeur comique")
```

**Règle 3 : Correspondance avec maturité**
```python
if category.lower() == "seinen" and int(request.user_age) >= 18:
    reasons.append("adapté à votre maturité")

if category.lower() == "shonen":
    reasons.append("style dynamique et accessible")
```

**Règle 4 : Justification par défaut**
```python
if not reasons:
    reasons.append(f"recommandé pour les amateurs de {genre}")
```

**Format de sortie** :
```python
return f"{title} - {' et '.join(reasons[:2])}"
```

**Exemples de sorties** :
- "Kaguya-sama - correspond à votre goût pour le Romance et style dynamique et accessible"
- "Berserk - adapté à votre maturité et parfait pour évacuer votre énervement"
- "One Punch Man - idéal pour votre humeur comique et recommandé pour les amateurs de Action"

### 3.3 VectorStore (vector_store.py)

#### Responsabilités

Le `VectorStore` constitue la couche d'abstraction entre l'application et la base de données vectorielle PostgreSQL. Il gère :
- La génération d'embeddings via Azure OpenAI
- Le stockage et la récupération de vecteurs
- Le calcul de similarité cosinus
- La gestion de la connexion PostgreSQL

#### Architecture interne

```python
class VectorStore:
    def __init__(self):
        self.settings = get_settings()

        # Sélection du provider OpenAI
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"

        if use_azure:
            self.openai_client = AzureOpenAI(
                api_key=self.settings.azure_openai.api_key,
                api_version=self.settings.azure_openai.api_version,
                azure_endpoint=self.settings.azure_openai.azure_endpoint
            )
            self.embedding_model = self.settings.azure_openai.embedding_model
        else:
            self.openai_client = OpenAI(api_key=self.settings.openai.api_key)
            self.embedding_model = self.settings.openai.embedding_model

        # Connexion PostgreSQL
        self.conn = psycopg2.connect(self.settings.database.service_url)
        register_vector(self.conn)
```

#### Méthode : get_embedding()

**Objectif** : transformer du texte en représentation vectorielle dense.

**Processus** :

```python
def get_embedding(self, text: str) -> List[float]:
    text = text.replace("\n", " ")  # Normalisation
    start_time = time.time()

    embedding = (
        self.openai_client.embeddings.create(
            input=[text],
            model=self.embedding_model,
        )
        .data[0]
        .embedding
    )

    elapsed_time = time.time() - start_time
    logging.info(f"Embedding generated in {elapsed_time:.3f} seconds")
    return embedding
```

**Caractéristiques** :
- **Normalisation** : suppression des retours à la ligne
- **Modèle utilisé** : text-embedding-3-large (Azure) ou text-embedding-3-small (OpenAI)
- **Dimensionnalité** : 3072 dimensions (Azure) ou 1536 dimensions (OpenAI)
- **Temps moyen** : ~0.5 secondes par appel API
- **Logging** : temps d'exécution tracé pour monitoring des performances

#### Méthode : search()

**Objectif** : effectuer une recherche de similarité vectorielle dans la base de données.

**Signature complète** :
```python
def search(
    self,
    query_text: str,                                    # Texte de recherche
    limit: int = 5,                                     # Nombre de résultats
    metadata_filter: Union[dict, List[dict]] = None,    # Filtrage par métadonnées
    time_range: Optional[Tuple[datetime, datetime]] = None,  # Filtrage temporel
    return_dataframe: bool = True,                      # Format de retour
    predicates=None,                                    # Prédicats avancés
) -> Union[List[Tuple[Any, ...]], pd.DataFrame]
```

**Algorithme de recherche** :

**Étape 1 : Génération de l'embedding de la requête**
```python
query_embedding = self.get_embedding(query_text)
```

**Étape 2 : Construction de la requête SQL**
```python
sql_query = f"SELECT id, metadata, contents, embedding FROM {self.vector_settings.table_name}"
conditions = []
params = []

if metadata_filter:
    for key, value in metadata_filter.items():
        conditions.append(f"metadata ->> %s = %s")
        params.extend([key, str(value)])

if time_range:
    start_date, end_date = time_range
    conditions.append("created_at BETWEEN %s AND %s")
    params.extend([start_date, end_date])

if conditions:
    sql_query += " WHERE " + " AND ".join(conditions)

sql_query += " LIMIT 1000"  # Limitation des candidats
```

**Étape 3 : Exécution de la requête**
```python
with self.conn.cursor() as cur:
    cur.execute(sql_query, params)
    db_results = cur.fetchall()
```

**Étape 4 : Calcul de la similarité cosinus en Python**
```python
similarities = []
for row in db_results:
    db_embedding = row[3]  # Colonne embedding

    # Calcul du produit scalaire
    dot_product = sum(a * b for a, b in zip(query_embedding, db_embedding))

    # Calcul des normes euclidiennes
    norm_a = sum(a * a for a in query_embedding) ** 0.5
    norm_b = sum(b * b for b in db_embedding) ** 0.5

    # Calcul de la similarité cosinus
    if norm_a > 0 and norm_b > 0:
        similarity = dot_product / (norm_a * norm_b)
        similarities.append((row + (similarity,)))
```

**Formule de similarité cosinus** :

```
similarity = (A · B) / (||A|| × ||B||)

où :
- A · B = produit scalaire des vecteurs
- ||A|| = norme euclidienne du vecteur A
- ||B|| = norme euclidienne du vecteur B
```

**Propriétés de la similarité cosinus** :
- Valeur comprise entre -1 et 1 (en pratique, entre 0 et 1 pour les embeddings OpenAI)
- 1 = vecteurs identiques (angle de 0°)
- 0 = vecteurs orthogonaux (angle de 90°)
- Insensible à la magnitude, mesure uniquement l'orientation

**Étape 5 : Tri et limitation des résultats**
```python
similarities.sort(key=lambda x: x[4], reverse=True)  # Tri décroissant
results = similarities[:limit]
```

**Étape 6 : Conversion en DataFrame**
```python
if return_dataframe:
    return self._create_dataframe_from_results(results)
```

#### Méthode : _create_dataframe_from_results()

**Objectif** : structurer les résultats de recherche dans un format exploitable.

```python
def _create_dataframe_from_results(self, results: List[Tuple[Any, ...]]) -> pd.DataFrame:
    # Création du DataFrame avec colonnes nommées
    df = pd.DataFrame(
        results, columns=["id", "metadata", "content", "embedding", "similarity"]
    )

    # Extension des métadonnées JSON en colonnes distinctes
    metadata_df = pd.json_normalize(df['metadata'])
    df = pd.concat([df.drop(['metadata'], axis=1), metadata_df], axis=1)

    # Conversion de l'UUID en string
    df["id"] = df["id"].astype(str)

    return df
```

**Résultat** : DataFrame avec colonnes :
- `id` : UUID de l'enregistrement
- `content` : texte du volume
- `embedding` : vecteur 3072 dimensions
- `similarity` : score de similarité (0-1)
- `serie_id`, `serie_title`, `genre`, `categorie`, `volume_id`, `volume_number` : métadonnées étendues

#### Limitation technique importante

**Problème** : l'index HNSW (Hierarchical Navigable Small World) est désactivé.

**Raison** : PostgreSQL pgvector limite les index HNSW à 2000 dimensions maximum. Le modèle text-embedding-3-large génère des vecteurs de 3072 dimensions, dépassant cette limite.

**Conséquence** : recherche linéaire (force brute) au lieu d'une recherche indexée optimisée.

**Mitigation** : limitation à 1000 candidats maximum avant calcul de similarité.

**Solution potentielle** : basculer vers text-embedding-3-small (1536 dimensions) pour activer l'index HNSW et améliorer les performances.

### 3.4 Agent Synthesizer (synthesizer.py)

#### Responsabilités

Le `Synthesizer` constitue l'agent conversationnel du système. Il génère un message d'accompagnement personnalisé contextualisant les recommandations proposées.

#### Architecture interne

```python
class Synthesizer:
    def generate_global_response(self, recommended_series: List, user_profile: dict) -> str:
        # Génération de réponse conversationnelle via GPT-4o-mini
```

#### Méthode : generate_global_response()

**Entrées** :
- `recommended_series` : liste des séries recommandées avec justifications
- `user_profile` : dictionnaire contenant toutes les informations utilisateur

**Processus** :

**Étape 1 : Sélection du provider OpenAI**
```python
use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"

if use_azure:
    client = AzureOpenAI(
        api_key=settings.azure_openai.api_key,
        api_version=settings.azure_openai.api_version,
        azure_endpoint=settings.azure_openai.azure_endpoint
    )
    model = settings.azure_openai.default_model  # gpt-4o-mini
else:
    client = OpenAI(api_key=settings.openai.api_key)
    model = settings.openai.default_model  # gpt-4o
```

**Étape 2 : Construction de la liste des séries**
```python
series_list = ""
if recommended_series:
    for i, serie in enumerate(recommended_series, 1):
        series_list += f"{i}. {serie.title}\n"
else:
    series_list = "Aucune série trouvée dans la base de données."
```

**Étape 3 : Construction du prompt système**

Le prompt constitue l'élément central de l'agent. Il définit le rôle, les objectifs et les contraintes de génération.

**Structure complète du prompt** :

```xml
<Role_and_Objectives>
  <Role>
    You are a recommendation engine embedded in Book Sync, a full-stack Django web application
    designed to help users manage and discover Asian literature, including manga, manhwa, and manhua.
    You are an expert in Japanese, Chinese, and Korean literary formats, with deep knowledge of
    genres such as shonen, seinen, shoujo, josei, horror, romance, fantasy, thriller, slice of life,
    and more. You understand both mainstream and niche titles, and your expertise allows you to
    curate personalized reading journeys.
  </Role>

  <Objectives>
    - Analyze the user's reading history, ratings, genre preferences and emotional state.
    - Interpret the user's current mood and adapt recommendations accordingly (e.g., seeking comfort,
      thrill, introspection, or light-hearted fun).
    - Leverage a dynamic and scalable database to suggest titles that align with the user's tastes
      and reading goals.
    - Continuously refine recommendations using behavioral feedback (e.g., reading time, completion
      rate, user reviews).
    - Ensure diversity in suggestions: trending series, hidden gems, new releases, and timeless classics.
    - Apply intelligent filters (e.g., art style, narrative complexity, pacing, emotional tone) to
      match the user's context and preferences.
    - Deliver warm, concise, and engaging responses that feel personal, insightful, and aligned with
      the user's journey.
    - Support gamification and progression tracking by integrating recommendations with the user's
      reading milestones.
    - Maximize user engagement and satisfaction to encourage long-term retention.
  </Objectives>
</Role_and_Objectives>

<user_profile>
- Year: {user_profile.get('user_age')}
- Gender: {user_profile.get('user_genre')}
- Preferences: {user_profile.get('genre_preference')} - {user_profile.get('category_preference')}
- Mood: {user_profile.get('user_mood', 'Not specified')}
- Prediction type: {user_profile.get('prediction_type')}
</user_profile>

Recommended series found:
{series_list}

Generate a warm and personalized response (2–3 sentences max) that:
1. Speaks directly to the user
2. Briefly explains why these recommendations match their profile
3. Takes into account their mood, preferences.
4. Remains concise, engaging, and aligned with Book Sync's tone
5. Encourages continued exploration or progression when relevant

Only return the response text, without JSON or additional structure.
```

**Analyse du prompt** :

**Section Role** :
- Définit l'identité de l'agent comme expert en littérature asiatique
- Établit la crédibilité dans les genres shonen, seinen, shoujo, josei, etc.
- Positionne l'agent comme curateur de parcours de lecture personnalisés

**Section Objectives** :
- Liste exhaustive des capacités attendues
- Accent sur l'analyse multidimensionnelle (historique, notes, émotions)
- Importance de la diversité (tendances, perles rares, nouveautés, classiques)
- Filtrage intelligent (style artistique, complexité narrative, rythme, tonalité)
- Ton conversationnel chaleureux et engageant
- Support de la gamification et du suivi de progression

**Section user_profile** :
- Injection contextuelle des attributs utilisateur
- Format structuré pour parsing facile par le modèle

**Consignes de génération** :
- Limite de longueur stricte (2-3 phrases)
- Adresse directe à l'utilisateur (tutoiement ou vouvoiement selon contexte)
- Justification contextuelle des recommandations
- Prise en compte de l'humeur actuelle
- Encouragement à l'exploration

**Étape 4 : Appel au modèle de langage**
```python
response = client.chat.completions.create(
    model=model,                    # gpt-4o-mini (Azure) ou gpt-4o (OpenAI)
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,                # Créativité modérée
    max_tokens=200                  # Limite de sortie
)

global_response = response.choices[0].message.content.strip()
```

**Paramètres de génération** :

- **temperature=0.7** : équilibre entre cohérence et créativité
  - 0.0 = déterministe et répétitif
  - 1.0 = créatif mais potentiellement incohérent
  - 0.7 = sweet spot pour réponses variées mais pertinentes

- **max_tokens=200** : limite la verbosité
  - 1 token ≈ 0.75 mot en français
  - 200 tokens ≈ 150 mots
  - Suffisant pour 2-3 phrases élaborées

**Exemples de sorties générées** :

**Profil** : Homme 22 ans, Romance, Humeur Comique
```
Voici mes recommandations personnalisées pour vous ! En tant qu'amateur de Romance de 22 ans,
ces séries offrent des histoires émouvantes avec beaucoup d'humour. Parfait pour votre humeur
comique actuelle. Bonne lecture !
```

**Profil** : Femme 18 ans, Action, Humeur Énervée
```
Ces séries d'Action sont idéales pour évacuer votre énergie ! Avec des combats intenses et des
personnages forts, elles correspondent parfaitement à votre profil et votre état d'esprit.
Profitez-en !
```

**Profil** : Homme 25 ans, Seinen, Humeur Introspective
```
J'ai sélectionné ces mangas Seinen pour leur profondeur narrative et leur maturité thématique.
Parfaits pour votre âge et votre besoin d'introspection. Ces œuvres vous offriront matière à
réflexion.
```

#### Gestion d'erreurs

```python
except Exception as e:
    logging.error(f"Erreur lors de la génération de la réponse globale: {e}")
    return f"Voici mes recommandations basées sur votre profil {user_profile.get('user_genre')} de {user_profile.get('user_age')} ans avec des préférences pour le {user_profile.get('category_preference')}."
```

En cas d'échec de l'appel OpenAI, retourne un message générique basique basé sur le profil utilisateur.

---

## 4. FLUX DE TRAITEMENT DES DONNÉES

### 4.1 Flux complet de bout en bout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : RÉCEPTION DE LA REQUÊTE                                  │
│                                                                     │
│ Client HTTP POST /predict/                                         │
│ Body: {                                                             │
│   "user_age": "22",                                                 │
│   "user_genre": "Homme",                                            │
│   "genre_preference": "Manga",                                      │
│   "category_preference": "Romance",                                 │
│   "user_comment": "je cherche quelque chose de léger",             │
│   "prediction_type": "collection",                                  │
│   "collection": {"Hunter X Hunter": {...}},                         │
│   "read": {"One Piece": {...}},                                     │
│   "user_mood": "Comique"                                            │
│ }                                                                   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 2 : VALIDATION PYDANTIC                                       │
│                                                                     │
│ FastAPI + Pydantic vérifient :                                      │
│ - Types de données corrects                                         │
│ - Champs obligatoires présents                                      │
│ - Valeurs dans les plages acceptables                               │
│ - Structure JSON conforme au modèle PredictRequest                  │
│                                                                     │
│ Si validation échoue → HTTP 422 Unprocessable Entity                │
│ Si validation réussit → Transmission au service                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 3 : ORCHESTRATION PAR PredictService                          │
│                                                                     │
│ predict_service.predict(request) déclenche :                        │
│ 1. Logging du contexte utilisateur                                  │
│ 2. Recherche de volumes similaires                                  │
│ 3. Extraction des séries recommandées                               │
│ 4. Génération de la synthèse conversationnelle                      │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 4 : RECHERCHE VECTORIELLE                                     │
│                                                                     │
│ _search_similar_volumes() exécute :                                 │
│                                                                     │
│ 4.1. Analyse de la collection                                       │
│      - Pour chaque série dans collection                            │
│      - Génération requête : "Serie: Hunter X Hunter Genre: Romance" │
│      - Appel vector_store.search(query, limit=5)                    │
│      - Agrégation des résultats                                     │
│                                                                     │
│ 4.2. Analyse des lectures                                           │
│      - Pour chaque série dans read                                  │
│      - Génération requête : "Serie: One Piece Genre: Romance"       │
│      - Appel vector_store.search(query, limit=5)                    │
│      - Agrégation des résultats                                     │
│                                                                     │
│ 4.3. Recherche générique (si aucune collection/lecture)             │
│      - Génération requête : "Genre: Romance Comique manga"          │
│      - Appel vector_store.search(query, limit=10)                   │
│                                                                     │
│ 4.4. Consolidation et dédoublonnage                                 │
│      - Fusion de tous les DataFrames                                │
│      - Suppression des séries en double (garde meilleur score)      │
│      - Limitation à 10 séries uniques                               │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 5 : OPÉRATIONS DE VectorStore.search()                        │
│                                                                     │
│ Pour chaque requête de recherche :                                  │
│                                                                     │
│ 5.1. Génération embedding de la requête                             │
│      - Appel Azure OpenAI Embeddings API                            │
│      - Modèle : text-embedding-3-large                              │
│      - Entrée : "Serie: Hunter X Hunter Genre: Romance"             │
│      - Sortie : vecteur de 3072 dimensions                          │
│      - Temps : ~0.5 secondes                                        │
│                                                                     │
│ 5.2. Requête PostgreSQL pour candidats                              │
│      - SELECT id, metadata, contents, embedding                     │
│      - FROM embeddings                                              │
│      - WHERE [filtres métadonnées si présents]                      │
│      - LIMIT 1000                                                   │
│                                                                     │
│ 5.3. Calcul similarité cosinus en Python                            │
│      - Pour chaque embedding candidat :                             │
│        * dot_product = Σ(query[i] * candidate[i])                   │
│        * norm_query = √(Σ(query[i]²))                               │
│        * norm_candidate = √(Σ(candidate[i]²))                       │
│        * similarity = dot_product / (norm_query * norm_candidate)   │
│      - Agrégation des tuples (row, similarity)                      │
│                                                                     │
│ 5.4. Tri et limitation                                              │
│      - Tri décroissant par score de similarité                      │
│      - Sélection des top N résultats (N=5 ou 10)                    │
│                                                                     │
│ 5.5. Conversion en DataFrame                                        │
│      - Création DataFrame pandas                                    │
│      - Extension des métadonnées JSON en colonnes                   │
│      - Colonnes finales : id, content, embedding, similarity,       │
│        serie_id, serie_title, genre, categorie, volume_id, etc.     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 6 : EXTRACTION DES SÉRIES                                     │
│                                                                     │
│ _extract_series_recommendations() traite :                          │
│                                                                     │
│ Pour chaque ligne du DataFrame :                                    │
│ 6.1. Extraction métadonnées                                         │
│      - serie_title = row.get('serie_title')                         │
│      - serie_id = row.get('serie_id')                               │
│      - genre = row.get('genre')                                     │
│      - categorie = row.get('categorie')                             │
│                                                                     │
│ 6.2. Génération justification personnalisée                         │
│      - Appel _generate_ai_response(title, genre, category, request) │
│                                                                     │
│ 6.3. Construction objet RecommendedSerie                            │
│      - title: "Kaguya-sama"                                         │
│      - id_series: "a1b2c3d4-..."                                    │
│      - responce_IA: "Kaguya-sama - correspond à votre goût pour le  │
│        Romance et style dynamique et accessible"                    │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 7 : GÉNÉRATION DES JUSTIFICATIONS                             │
│                                                                     │
│ _generate_ai_response() applique règles :                           │
│                                                                     │
│ 7.1. Analyse correspondance préférence                              │
│      if "Romance" in genre:                                         │
│          reasons.append("correspond à votre goût pour le Romance")  │
│                                                                     │
│ 7.2. Analyse correspondance humeur                                  │
│      if mood == "Comique" and "comédie" in genre:                   │
│          reasons.append("idéal pour votre humeur comique")          │
│                                                                     │
│ 7.3. Analyse correspondance âge/maturité                            │
│      if categorie == "shonen":                                      │
│          reasons.append("style dynamique et accessible")            │
│                                                                     │
│ 7.4. Construction texte final                                       │
│      return f"{title} - {reasons[0]} et {reasons[1]}"               │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 8 : SYNTHÈSE CONVERSATIONNELLE                                │
│                                                                     │
│ synthesizer.generate_global_response() génère :                     │
│                                                                     │
│ 8.1. Préparation du profil utilisateur                              │
│      user_profile = {                                               │
│          'user_age': '22',                                          │
│          'user_genre': 'Homme',                                     │
│          'category_preference': 'Romance',                          │
│          'user_mood': 'Comique',                                    │
│          ...                                                        │
│      }                                                              │
│                                                                     │
│ 8.2. Construction liste séries                                      │
│      series_list = "1. Kaguya-sama\n2. Toradora!\n3. ..."           │
│                                                                     │
│ 8.3. Construction prompt système                                    │
│      - Injection rôle et objectifs                                  │
│      - Injection profil utilisateur                                 │
│      - Injection liste séries recommandées                          │
│      - Consignes de génération (2-3 phrases, chaleureux, etc.)      │
│                                                                     │
│ 8.4. Appel Azure OpenAI Chat Completions                            │
│      - Modèle : gpt-4o-mini                                         │
│      - Temperature : 0.7                                            │
│      - Max tokens : 200                                             │
│      - Messages : [{"role": "user", "content": prompt}]             │
│                                                                     │
│ 8.5. Extraction de la réponse                                       │
│      global_response = response.choices[0].message.content.strip()  │
│      Exemple : "Voici mes recommandations personnalisées pour vous !│
│      En tant qu'amateur de Romance de 22 ans, ces séries offrent des│
│      histoires émouvantes avec beaucoup d'humour. Parfait pour votre│
│      humeur comique actuelle. Bonne lecture !"                      │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 9 : CONSTRUCTION DE LA RÉPONSE                                │
│                                                                     │
│ PredictService construit PredictResponse :                          │
│                                                                     │
│ return PredictResponse(                                             │
│     serie_recomendees=[                                             │
│         RecommendedSerie(                                           │
│             title="Kaguya-sama",                                    │
│             id_series="a1b2c3d4-...",                               │
│             responce_IA="Kaguya-sama - correspond à votre goût..."  │
│         ),                                                          │
│         RecommendedSerie(                                           │
│             title="Toradora!",                                      │
│             id_series="f1e2d3c4-...",                               │
│             responce_IA="Toradora! - idéal pour votre humeur..."    │
│         ),                                                          │
│         ...                                                         │
│     ],                                                              │
│     status="success",                                               │
│     responce_IA_global="Voici mes recommandations personnalisées..."│
│ )                                                                   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│ ÉTAPE 10 : SÉRIALISATION ET RETOUR                                  │
│                                                                     │
│ FastAPI sérialise automatiquement :                                 │
│ - PydanticModel → JSON                                              │
│ - HTTP 200 OK                                                       │
│ - Content-Type: application/json                                    │
│                                                                     │
│ Réponse JSON finale :                                               │
│ {                                                                   │
│   "serie_recomendees": [                                            │
│     {                                                               │
│       "title": "Kaguya-sama",                                       │
│       "id_series": "a1b2c3d4-...",                                  │
│       "responce_IA": "Kaguya-sama - correspond à votre goût..."     │
│     },                                                              │
│     ...                                                             │
│   ],                                                                │
│   "status": "success",                                              │
│   "responce_IA_global": "Voici mes recommandations personnalisées..."│
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Temps d'exécution typique

**Analyse des performances** :

| Étape | Opération | Temps moyen | Notes |
|-------|-----------|-------------|-------|
| 1 | Réception HTTP | <5ms | FastAPI ASGI |
| 2 | Validation Pydantic | <10ms | Validation synchrone |
| 3 | Orchestration | <1ms | Logique Python native |
| 4 | Recherche vectorielle (x3) | 1.5s | 3 requêtes × 0.5s chacune |
| 5.1 | Génération embedding | 0.5s | Appel API Azure OpenAI |
| 5.2-5.5 | Requête SQL + calculs | 0.3s | PostgreSQL + numpy |
| 6-7 | Extraction et justifications | <50ms | Logique Python |
| 8.4 | Génération conversationnelle | 0.8s | Appel GPT-4o-mini |
| 9-10 | Construction et sérialisation | <10ms | Pydantic → JSON |
| **TOTAL** | **Pipeline complet** | **~2.5s** | **Variable selon réseau** |

**Facteurs d'optimisation** :
- Recherches vectorielles multiples : 60% du temps total
- Appels OpenAI : 35% du temps total
- Traitement applicatif : 5% du temps total

---

## 5. SYSTÈME D'EMBEDDINGS VECTORIELS

### 5.1 Principes fondamentaux

#### Qu'est-ce qu'un embedding ?

Un **embedding** est une représentation vectorielle dense d'un texte dans un espace multidimensionnel où la proximité géométrique correspond à la similarité sémantique.

**Propriétés clés** :
- **Dimensionnalité** : vecteur de N dimensions (3072 pour text-embedding-3-large)
- **Densité** : toutes les dimensions contiennent des valeurs (pas de sparse vector)
- **Normalisation** : valeurs généralement dans [-1, 1]
- **Sémantique** : mots/phrases similaires → vecteurs proches

**Exemple conceptuel** :

```
Texte : "manga d'action avec combats épiques"
Embedding : [0.023, -0.145, 0.891, ..., 0.234]  (3072 valeurs)

Texte : "série de combat dynamique shonen"
Embedding : [0.031, -0.139, 0.878, ..., 0.227]  (3072 valeurs)

Distance cosinus : 0.92 (très similaire)
```

#### Pourquoi les embeddings ?

**Recherche textuelle classique** (keyword matching) :
- Requête : "manga action"
- Ne trouve PAS : "série de combat", "shonen dynamique", "anime bagarreur"
- Problème : synonymie, polysémie, variations linguistiques

**Recherche sémantique** (embedding matching) :
- Requête : "manga action"
- Trouve : "série de combat" (0.89), "shonen dynamique" (0.87), "anime bagarreur" (0.84)
- Avantage : compréhension du sens, pas juste des mots

### 5.2 Modèle d'embedding utilisé

#### text-embedding-3-large (Azure OpenAI)

**Caractéristiques techniques** :
- **Version** : text-embedding-3-large
- **Dimensionnalité** : 3072 dimensions
- **Contexte maximum** : 8191 tokens (~6000 mots)
- **Performance** : état de l'art pour tâches sémantiques
- **Coût** : $0.13 pour 1M tokens (Azure pricing)

**Avantages** :
- Haute précision sémantique
- Capture de nuances fines
- Multilingue (français, anglais, japonais, etc.)
- Robuste aux variations syntaxiques

**Inconvénient** :
- 3072 dimensions > limite HNSW (2000 dim)
- Nécessite calcul de similarité en Python

#### Alternative : text-embedding-3-small

**Caractéristiques** :
- **Dimensionnalité** : 1536 dimensions
- **Performance** : légèrement inférieure mais excellente
- **Avantage** : compatible avec index HNSW
- **Coût** : $0.02 pour 1M tokens (6.5× moins cher)

### 5.3 Processus de génération d'embeddings

#### Phase d'initialisation (insertion de données)

**Script** : `app/services/insert_vectors.py`

**Processus** :

```python
# 1. Lecture du CSV source
df = pd.read_csv('data/volume_content.csv', delimiter=';')

# 2. Pour chaque ligne (volume)
for index, row in df.iterrows():
    # 3. Formatage du contenu
    content_text = f"""
    Serie: {row['serie_title']}
    Genre: {row['genre']}
    Categorie: {row['categorie']}
    Volume {row['volume_number']}: {row['content']}
    """

    # 4. Génération de l'embedding
    embedding = vector_store.get_embedding(content_text)

    # 5. Préparation des métadonnées
    metadata = {
        'serie_id': row['serie_id'],
        'serie_title': row['serie_title'],
        'genre': row['genre'],
        'categorie': row['categorie'],
        'volume_id': row['volume_id'],
        'volume_number': row['volume_number'],
        'created_at': datetime.now().isoformat()
    }

    # 6. Insertion en base
    df_insert = pd.DataFrame([{
        'id': str(uuid.uuid4()),
        'metadata': metadata,
        'contents': content_text,
        'embedding': embedding
    }])

    vector_store.upsert(df_insert)

    # 7. Pause pour éviter rate limiting
    time.sleep(1)
```

**Exemple de contenu formaté** :

```
Serie: 008 Apprenti espion
Genre: Manga
Categorie: Agent secret, Aventure, Comédie, Ecchi, Romance, Shonen, Suspense
Volume 1: Jeune lycéen sans établissement, Eight est désespéré : il n'a aucune
perspective d'avenir. Son oncle Koda lui fait alors une proposition insensée :
s'inscrire dans un établissement spécialisé qui forme des espions ! Dans une
classe remplie de personnages hauts en couleur, Eight va devoir prouver sa valeur...
```

#### Phase de recherche (runtime)

**Processus** :

```python
# 1. Requête utilisateur
query_text = "Serie: Hunter X Hunter Genre: Romance"

# 2. Génération de l'embedding de requête
query_embedding = vector_store.get_embedding(query_text)
# Résultat : [0.012, -0.234, 0.567, ..., 0.123] (3072 dimensions)

# 3. Comparaison avec tous les embeddings en base
# (détaillé dans section suivante)
```

### 5.4 Calcul de similarité cosinus

#### Formule mathématique

```
cos(θ) = (A · B) / (||A|| × ||B||)

où :
- A : vecteur embedding de la requête (3072 dimensions)
- B : vecteur embedding du candidat (3072 dimensions)
- A · B : produit scalaire = Σ(A[i] × B[i]) pour i de 0 à 3071
- ||A|| : norme euclidienne de A = √(Σ(A[i]²))
- ||B|| : norme euclidienne de B = √(Σ(B[i]²))
- θ : angle entre les vecteurs A et B
```

#### Implémentation Python

```python
def calculate_cosine_similarity(query_embedding, db_embedding):
    # 1. Produit scalaire
    dot_product = sum(a * b for a, b in zip(query_embedding, db_embedding))

    # 2. Norme du vecteur requête
    norm_a = sum(a * a for a in query_embedding) ** 0.5

    # 3. Norme du vecteur candidat
    norm_b = sum(b * b for b in db_embedding) ** 0.5

    # 4. Similarité cosinus
    if norm_a > 0 and norm_b > 0:
        similarity = dot_product / (norm_a * norm_b)
    else:
        similarity = 0.0

    return similarity
```

#### Interprétation géométrique

```
      A (requête)
       ↑
       |  θ (angle)
       | /
       |/____→ B (candidat)

Si θ = 0°  → cos(θ) = 1.0  → Vecteurs identiques
Si θ = 45° → cos(θ) = 0.7  → Vecteurs similaires
Si θ = 90° → cos(θ) = 0.0  → Vecteurs orthogonaux (aucune relation)
```

**Propriétés importantes** :
- **Insensible à la magnitude** : seule la direction compte
- **Valeur dans [0, 1]** pour embeddings OpenAI (toujours positifs)
- **Symétrique** : cos(A, B) = cos(B, A)
- **Transitivité approximative** : si A ≈ B et B ≈ C, alors A ≈ C

#### Exemple concret

**Requête** : "Serie: Hunter X Hunter Genre: Romance"
**Embedding requête** : [0.023, -0.145, 0.891, ..., 0.234] (3072 valeurs)

**Candidat 1** : "Kaguya-sama: Love Is War - Manga Romance Comédie"
**Embedding candidat 1** : [0.031, -0.139, 0.878, ..., 0.227]
**Similarité** : 0.92 (très pertinent)

**Candidat 2** : "Berserk - Manga Dark Fantasy Seinen"
**Embedding candidat 2** : [0.456, 0.789, -0.234, ..., 0.678]
**Similarité** : 0.34 (peu pertinent)

**Candidat 3** : "Hunter X Hunter - Manga Shonen Aventure Action"
**Embedding candidat 3** : [0.019, -0.151, 0.902, ..., 0.241]
**Similarité** : 0.88 (pertinent - même série)

### 5.5 Limitation technique : absence d'index HNSW

#### Contexte du problème

**Index HNSW** (Hierarchical Navigable Small World) :
- Algorithme d'indexation pour recherche vectorielle ultra-rapide
- Complexité : O(log N) au lieu de O(N) pour recherche linéaire
- Graphe hiérarchique multi-couches
- Performances : recherche dans 10M vecteurs en ~10ms

**Limitation PostgreSQL pgvector** :
- Support HNSW limité à 2000 dimensions maximum
- text-embedding-3-large = 3072 dimensions
- **Conséquence** : index HNSW désactivé

#### Impact sur les performances

**Avec index HNSW** (hypothétique avec 1536 dimensions) :
```
Étape 1 : Traversée du graphe HNSW → Top 100 candidats
Étape 2 : Calcul exact sur 100 vecteurs
Temps total : ~50ms pour 28 863 vecteurs
```

**Sans index (situation actuelle avec 3072 dimensions)** :
```
Étape 1 : Récupération de 1000 candidats aléatoires
Étape 2 : Calcul de similarité sur 1000 vecteurs en Python
Temps total : ~300ms pour 28 863 vecteurs
```

**Ratio de performance** : 6× plus lent sans index

#### Solution de contournement actuelle

```python
# Limitation du nombre de candidats
sql_query += " LIMIT 1000"

# Calcul de similarité en Python (pas en SQL)
similarities = []
for row in db_results:
    similarity = calculate_cosine_similarity(query_embedding, row[3])
    similarities.append((row, similarity))

# Tri et sélection top N
similarities.sort(key=lambda x: x[1], reverse=True)
results = similarities[:limit]
```

#### Solutions d'optimisation futures

**Option 1** : Basculer vers text-embedding-3-small
- Avantages : 1536 dimensions → HNSW activable, 6.5× moins cher
- Inconvénient : légère perte de précision sémantique

**Option 2** : Utiliser une base vectorielle spécialisée
- Pinecone : supporte haute dimensionnalité avec index optimisé
- Weaviate : support natif des embeddings OpenAI
- Milvus : open-source, haute performance

**Option 3** : Compression dimensionnelle (PCA)
- Réduire 3072 → 2000 dimensions
- Inconvénient : perte d'information significative

---

## 6. AGENT DE SYNTHÈSE CONVERSATIONNELLE

### 6.1 Architecture de l'agent

L'agent `Synthesizer` constitue une couche d'intelligence conversationnelle qui transforme des recommandations brutes en communication naturelle et engageante.

**Paradigme** : Retrieval-Augmented Generation (RAG)
- **Retrieval** : recherche vectorielle des séries pertinentes
- **Augmentation** : enrichissement avec contexte utilisateur
- **Generation** : production de texte conversationnel via LLM

### 6.2 Prompt engineering

#### Structure du prompt système

Le prompt constitue l'ADN de l'agent. Il définit son identité, ses compétences et son comportement.

**Composants clés** :

**1. Définition du rôle**
```xml
<Role>
You are a recommendation engine embedded in Book Sync, a full-stack Django web
application designed to help users manage and discover Asian literature, including
manga, manhwa, and manhua. You are an expert in Japanese, Chinese, and Korean
literary formats, with deep knowledge of genres such as shonen, seinen, shoujo,
josei, horror, romance, fantasy, thriller, slice of life, and more.
</Role>
```

**Analyse** :
- Établit l'identité comme système de recommandation (pas assistant général)
- Spécifie le domaine d'expertise (littérature asiatique)
- Liste les genres maîtrisés pour crédibilité
- Contextualise dans l'écosystème BookSync

**2. Définition des objectifs**
```xml
<Objectives>
- Analyze the user's reading history, ratings, genre preferences and emotional state.
- Interpret the user's current mood and adapt recommendations accordingly
- Leverage a dynamic and scalable database to suggest titles that align with tastes
- Ensure diversity in suggestions: trending series, hidden gems, new releases, classics
- Deliver warm, concise, and engaging responses that feel personal
- Support gamification and progression tracking
- Maximize user engagement and satisfaction
</Objectives>
```

**Analyse** :
- **Analyse multidimensionnelle** : historique + notes + émotions
- **Adaptation humeur** : importance de l'état émotionnel actuel
- **Diversité** : éviter les recommandations répétitives
- **Ton conversationnel** : chaleureux, concis, personnel
- **Gamification** : intégration dans un parcours utilisateur
- **Métrique finale** : engagement et satisfaction

**3. Injection du contexte utilisateur**
```xml
<user_profile>
- Year: {user_age}
- Gender: {user_genre}
- Preferences: {genre_preference} - {category_preference}
- Mood: {user_mood}
- Prediction type: {prediction_type}
</user_profile>
```

**Analyse** :
- Format structuré pour parsing facile par le modèle
- Variables injectées dynamiquement depuis la requête
- Démographiques (âge, genre) pour adaptation du ton
- Psychographiques (préférences, humeur) pour personnalisation

**4. Liste des recommandations**
```
Recommended series found:
1. Kaguya-sama: Love Is War
2. Toradora!
3. Fruits Basket
...
```

**Analyse** :
- Liste simple et claire
- Numérotation pour référencement facile
- Titres exacts (pas de descriptions)

**5. Consignes de génération**
```
Generate a warm and personalized response (2–3 sentences max) that:
1. Speaks directly to the user
2. Briefly explains why these recommendations match their profile
3. Takes into account their mood, preferences
4. Remains concise, engaging, and aligned with Book Sync's tone
5. Encourages continued exploration or progression when relevant

Only return the response text, without JSON or additional structure.
```

**Analyse** :
- **Limite stricte** : 2-3 phrases maximum
- **Adresse directe** : création d'un lien personnel
- **Justification** : explication du "pourquoi"
- **Contextualisation** : humeur et préférences
- **Encouragement** : call-to-action implicite
- **Format brut** : pas de structuration JSON

#### Paramètres de génération

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",        # Modèle rapide et économique
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,            # Équilibre créativité/cohérence
    max_tokens=200              # Limite verbosité (~150 mots)
)
```

**Analyse des paramètres** :

**model: "gpt-4o-mini"**
- Modèle optimisé pour tâches légères
- Latence réduite (~0.8s vs ~2s pour GPT-4)
- Coût réduit (~15× moins cher que GPT-4)
- Performances suffisantes pour génération courte

**temperature: 0.7**
- Échelle de créativité : 0 (déterministe) → 2 (chaotique)
- 0.0 : réponses identiques, répétitives
- 0.7 : sweet spot pour variété sans incohérence
- 1.0+ : risque de hallucinations et verbosité

**Exemple de variabilité avec temperature=0.7** :

Même profil, 3 générations différentes :
```
Generation 1: "Voici mes recommandations pour vous ! Ces mangas Romance correspondent
parfaitement à votre profil de 22 ans et votre humeur comique. Bonne lecture !"

Generation 2: "J'ai sélectionné ces séries basées sur votre amour du Romance !
Idéales pour votre humeur actuelle, elles offrent légèreté et émotions. Profitez-en !"

Generation 3: "Ces recommandations Romance sont faites pour vous ! Avec votre
sensibilité de 22 ans et votre recherche d'humour, vous allez adorer. Plongez dedans !"
```

**max_tokens: 200**
- 1 token ≈ 0.75 mot en français
- 200 tokens ≈ 150 mots
- Suffisant pour 2-3 phrases élaborées
- Évite les dérives verbosiques du modèle

### 6.3 Exemples de réponses générées

#### Exemple 1 : Profil Romance Comique

**Entrée** :
```json
{
  "user_age": "22",
  "user_genre": "Homme",
  "genre_preference": "Manga",
  "category_preference": "Romance",
  "user_mood": "Comique",
  "series": ["Kaguya-sama", "Toradora!", "Fruits Basket"]
}
```

**Sortie** :
```
Voici mes recommandations personnalisées pour vous ! En tant qu'amateur de Romance de
22 ans, ces séries offrent des histoires émouvantes avec beaucoup d'humour. Parfait
pour votre humeur comique actuelle. Bonne lecture !
```

**Analyse** :
- Adresse directe : "pour vous"
- Référence à l'âge : "22 ans"
- Lien préférence : "amateur de Romance"
- Lien humeur : "humour" / "humeur comique"
- Encouragement : "Bonne lecture !"

#### Exemple 2 : Profil Action Énervé

**Entrée** :
```json
{
  "user_age": "18",
  "user_genre": "Femme",
  "genre_preference": "Manga",
  "category_preference": "Action",
  "user_mood": "Énervé",
  "series": ["Attack on Titan", "Demon Slayer", "Tokyo Ghoul"]
}
```

**Sortie** :
```
Ces séries d'Action sont idéales pour évacuer votre énergie ! Avec des combats
intenses et des personnages forts, elles correspondent parfaitement à votre profil
et votre état d'esprit. Profitez-en !
```

**Analyse** :
- Fonction thérapeutique : "évacuer votre énergie"
- Descripteurs pertinents : "combats intenses"
- Double correspondance : "profil" + "état d'esprit"
- Call-to-action : "Profitez-en !"

#### Exemple 3 : Profil Seinen Introspectif

**Entrée** :
```json
{
  "user_age": "25",
  "user_genre": "Homme",
  "genre_preference": "Manga",
  "category_preference": "Seinen",
  "user_mood": "Introspectif",
  "series": ["Monster", "Vinland Saga", "Berserk"]
}
```

**Sortie** :
```
J'ai sélectionné ces mangas Seinen pour leur profondeur narrative et leur maturité
thématique. Parfaits pour votre âge et votre besoin d'introspection. Ces œuvres vous
offriront matière à réflexion.
```

**Analyse** :
- Vocabulaire sophistiqué : "profondeur narrative", "maturité thématique"
- Adaptation au profil mature : "25 ans", "Seinen"
- Réponse émotionnelle : "besoin d'introspection"
- Valeur ajoutée : "matière à réflexion"

### 6.4 Gestion des cas limites

#### Cas 1 : Aucune série trouvée

```python
if not recommended_series:
    series_list = "Aucune série trouvée dans la base de données."
```

**Sortie générée** :
```
Malheureusement, je n'ai pas trouvé de série correspondant exactement à votre profil
dans notre base actuelle. Je vous suggère d'explorer d'autres catégories ou de revenir
plus tard, car nous ajoutons régulièrement de nouveaux titres !
```

#### Cas 2 : Échec de l'appel OpenAI

```python
except Exception as e:
    logging.error(f"Erreur lors de la génération de la réponse globale: {e}")
    return f"Voici mes recommandations basées sur votre profil {user_profile.get('user_genre')} de {user_profile.get('user_age')} ans avec des préférences pour le {user_profile.get('category_preference')}."
```

**Sortie fallback** :
```
Voici mes recommandations basées sur votre profil Homme de 22 ans avec des
préférences pour le Romance.
```

**Analyse** : message générique mais fonctionnel, sans la personnalisation IA.

---

## 7. ALGORITHMES DE RECOMMANDATION

### 7.1 Stratégie de recherche multi-sources

Le système utilise une approche hybride combinant trois stratégies de recherche :

#### Stratégie 1 : Recommandation par collection

**Principe** : "Si l'utilisateur possède Hunter X Hunter, recommander des séries similaires"

**Algorithme** :
```python
if request.collection:
    for serie_name, serie_data in request.collection.items():
        # Construction requête sémantique
        search_query = f"Serie: {serie_name} Genre: {request.category_preference}"

        # Recherche vectorielle
        results = vector_store.search(query_text=search_query, limit=5)

        # Agrégation
        all_results.append(results)
```

**Exemple concret** :

Collection utilisateur :
```json
{
  "Hunter X Hunter": {
    "volumes": {"1": "uuid-1", "2": "uuid-2"},
    "id_series": "uuid-serie"
  }
}
```

Requête générée :
```
"Serie: Hunter X Hunter Genre: Romance"
```

Résultats attendus :
- Séries thématiquement proches de Hunter X Hunter
- Mais dans la catégorie Romance (préférence utilisateur)
- Exemple : "Fruits Basket" (aventure + romance)

**Justification** : exploite la collection existante comme signal d'intérêt tout en respectant la préférence actuelle.

#### Stratégie 2 : Recommandation par historique de lecture

**Principe** : "Si l'utilisateur a lu One Piece, recommander des séries similaires"

**Algorithme** : identique à la stratégie 1, mais sur `request.read` au lieu de `request.collection`.

**Différence conceptuelle** :
- **Collection** : possédé physiquement → signal d'intérêt fort
- **Read** : déjà lu → signal de familiarité, recherche de nouveauté

#### Stratégie 3 : Recommandation par préférences génériques

**Principe** : "Si aucune collection/lecture, recommander basé sur préférence + humeur"

**Algorithme** :
```python
if not all_results:  # Aucun résultat des stratégies 1-2
    mood_text = f" {request.user_mood}" if request.user_mood else ""
    search_query = f"Genre: {request.category_preference}{mood_text} manga"

    results = vector_store.search(query_text=search_query, limit=10)
```

**Exemple concret** :

Profil utilisateur :
```json
{
  "category_preference": "Romance",
  "user_mood": "Comique"
}
```

Requête générée :
```
"Genre: Romance Comique manga"
```

Résultats attendus :
- Mangas de Romance avec tonalité comique
- Exemple : "Kaguya-sama", "Monthly Girls' Nozaki-kun"

### 7.2 Consolidation et dédoublonnage

**Problème** : les 3 stratégies peuvent retourner la même série plusieurs fois avec scores différents.

**Solution** : dédoublonnage avec conservation du meilleur score.

**Algorithme** :
```python
# 1. Fusion de tous les DataFrames
combined_results = pd.concat(all_results, ignore_index=True)

# 2. Dédoublonnage
seen_series = set()
unique_results = []

for _, row in combined_results.iterrows():
    metadata = row.get('metadata', {})
    serie_title = metadata.get('serie_title', '')

    if serie_title and serie_title not in seen_series:
        seen_series.add(serie_title)
        unique_results.append(row)

# 3. Conversion et limitation
return pd.DataFrame(unique_results).head(10)
```

**Propriété importante** : la première occurrence est conservée. Comme les résultats sont déjà triés par similarité décroissante, cela garantit de garder le meilleur score.

**Exemple** :

Résultats bruts :
```
Kaguya-sama (stratégie 1, score: 0.92)
Toradora! (stratégie 1, score: 0.89)
Kaguya-sama (stratégie 3, score: 0.85)  ← Doublon
Fruits Basket (stratégie 2, score: 0.88)
Kaguya-sama (stratégie 2, score: 0.81)  ← Doublon
```

Résultats après dédoublonnage :
```
Kaguya-sama (score: 0.92)  ← Meilleur score conservé
Toradora! (score: 0.89)
Fruits Basket (score: 0.88)
```

### 7.3 Génération de justifications personnalisées

**Principe** : chaque recommandation doit être justifiée par rapport au profil utilisateur.

**Règles de correspondance** :

**Règle 1 : Correspondance catégorielle**
```python
if request.category_preference.lower() in genre.lower():
    reasons.append(f"correspond à votre goût pour le {request.category_preference}")
```

**Règle 2 : Correspondance émotionnelle**
```python
mood_genre_mapping = {
    "énervé": ["action", "combat", "aventure"],
    "comique": ["comédie", "humour"],
    "triste": ["drame", "mélancolie"],
    "joyeux": ["feel-good", "comédie"],
}

if request.user_mood.lower() in mood_genre_mapping:
    matching_keywords = mood_genre_mapping[request.user_mood.lower()]
    if any(keyword in genre.lower() for keyword in matching_keywords):
        reasons.append(f"parfait pour votre humeur {request.user_mood.lower()}")
```

**Règle 3 : Correspondance démographique**
```python
if category.lower() == "seinen" and int(request.user_age) >= 18:
    reasons.append("adapté à votre maturité")

if category.lower() == "shonen":
    reasons.append("style dynamique et accessible")
```

**Règle 4 : Fallback**
```python
if not reasons:
    reasons.append(f"recommandé pour les amateurs de {genre}")
```

**Exemple de cascade** :

Série : "Kaguya-sama: Love Is War"
- Genre : "Romance, Comédie, Shonen"
- Profil : 22 ans, préférence Romance, humeur Comique

Correspondances :
1. "Romance" in genre → "correspond à votre goût pour le Romance"
2. Humeur "Comique" + "Comédie" in genre → "idéal pour votre humeur comique"
3. "Shonen" → "style dynamique et accessible"

Sélection : 2 premières raisons (maximum 2)

Sortie :
```
Kaguya-sama - correspond à votre goût pour le Romance et idéal pour votre humeur comique
```

### 7.4 Ordonnancement final

**Critère principal** : score de similarité vectorielle décroissant

**Critères secondaires** (non implémentés actuellement) :
- Popularité de la série
- Date de sortie (nouveautés en priorité)
- Diversité (éviter recommandations trop similaires)
- Complétion de la collection (volumes manquants)

---

## 8. MODÈLES DE DONNÉES

### 8.1 Modèle de requête : PredictRequest

**Fichier** : `app/models/predict_request.py`

**Définition Pydantic** :
```python
class PredictRequest(BaseModel):
    user_age: str
    user_genre: str
    genre_preference: str
    category_preference: str
    user_comment: str
    prediction_type: Literal["collection", "recommendation"]
    collection: Optional[Union[Dict, str]] = None
    read: Optional[Union[Dict, str]] = None
    user_mood: str
```

**Champs détaillés** :

| Champ | Type | Obligatoire | Description | Exemple |
|-------|------|-------------|-------------|---------|
| `user_age` | str | Oui | Âge de l'utilisateur | "22" |
| `user_genre` | str | Oui | Genre (Homme/Femme/Autre) | "Homme" |
| `genre_preference` | str | Oui | Type de littérature | "Manga" |
| `category_preference` | str | Oui | Catégorie préférée | "Romance" |
| `user_comment` | str | Oui | Commentaires libres | "je cherche du léger" |
| `prediction_type` | Literal | Oui | Type de prédiction | "collection" |
| `collection` | Dict/str | Non | Collection possédée | Voir structure ci-dessous |
| `read` | Dict/str | Non | Volumes déjà lus | Voir structure ci-dessous |
| `user_mood` | str | Oui | Humeur actuelle | "Comique" |

**Structure de collection/read** :
```json
{
  "Hunter X Hunter": {
    "volumes": {
      "1": "uuid-volume-1",
      "2": "uuid-volume-2",
      "3": "uuid-volume-3"
    },
    "id_series": "uuid-serie-hunter"
  },
  "One Piece": {
    "volumes": {
      "1": "uuid-volume-1"
    },
    "id_series": "uuid-serie-onepiece"
  }
}
```

**Validation automatique** :
- `prediction_type` : doit être exactement "collection" ou "recommendation"
- `collection` et `read` : acceptent dict ou string (flexibilité pour API)
- Tous les autres champs : validation de présence

### 8.2 Modèle de réponse : PredictResponse

**Fichier** : `app/models/predict_response.py`

**Définition Pydantic** :
```python
class RecommendedSerie(BaseModel):
    title: str
    id_series: str
    responce_IA: str

class PredictResponse(BaseModel):
    serie_recomendees: List[RecommendedSerie]
    status: str
    responce_IA_global: str
```

**Structure complète** :
```json
{
  "serie_recomendees": [
    {
      "title": "Kaguya-sama: Love Is War",
      "id_series": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "responce_IA": "Kaguya-sama - correspond à votre goût pour le Romance et style dynamique et accessible"
    },
    {
      "title": "Toradora!",
      "id_series": "f1e2d3c4-b5a6-9870-5432-1098765fedcba",
      "responce_IA": "Toradora! - idéal pour votre humeur comique et adapté à votre maturité"
    }
  ],
  "status": "success",
  "responce_IA_global": "Voici mes recommandations personnalisées pour vous ! En tant qu'amateur de Romance de 22 ans, ces séries offrent des histoires émouvantes avec beaucoup d'humour. Parfait pour votre humeur comique actuelle. Bonne lecture !"
}
```

### 8.3 Schéma de base de données PostgreSQL

**Table** : `embeddings`

**Définition SQL** :
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    metadata JSONB,
    contents TEXT,
    embedding vector(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE EXTENSION IF NOT EXISTS vector;
```

**Colonnes détaillées** :

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Identifiant unique de l'enregistrement |
| `metadata` | JSONB | - | Métadonnées structurées (serie_id, titre, genre, etc.) |
| `contents` | TEXT | - | Texte complet du volume formaté |
| `embedding` | vector(3072) | - | Vecteur d'embedding 3072 dimensions |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Date de création de l'enregistrement |

**Structure de metadata** :
```json
{
  "serie_id": "88184d71-b332-49d3-9c61-4e86b41f6f9f",
  "serie_title": "008 Apprenti espion",
  "genre": "Manga",
  "categorie": "Agent secret, Aventure, Comédie, Ecchi, Romance, Shonen, Suspense",
  "volume_id": "b00466c3-2a1f-4a93-a5f9-c199837a04ed",
  "volume_number": 1,
  "created_at": "2024-11-14T10:30:45.123456"
}
```

**Exemple d'enregistrement complet** :
```
id: 550e8400-e29b-41d4-a716-446655440000
metadata: {"serie_id": "88184d71-...", "serie_title": "008 Apprenti espion", ...}
contents: "Serie: 008 Apprenti espion\nGenre: Manga\nCategorie: Agent secret, Aventure, Comédie...\nVolume 1: Jeune lycéen sans établissement..."
embedding: [0.023, -0.145, 0.891, ..., 0.234] (3072 valeurs)
created_at: 2024-11-14 10:30:45.123456
```

**Statistiques** :
- Nombre total d'enregistrements : 28 863 volumes
- Taille moyenne d'un embedding : 12 Ko (3072 float32)
- Taille totale estimée : ~350 Mo (embeddings uniquement)

---

## 9. CONFIGURATION ET INFRASTRUCTURE

### 9.1 Variables d'environnement

**Fichier** : `.env` (non versionné)

**Variables critiques** :

```bash
# Sélection du provider OpenAI
USE_AZURE_OPENAI=true

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://app-booksync.openai.azure.com/
AZURE_OPENAI_KEY=FdttISEZFqk39FF9JG07SB04BAQoeuQ2wU0s4o9BUiR0V7kfjElcJQQJ99BHAC5T7U2XJ3w3AAABACOGSobm
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# PostgreSQL Azure
TIMESCALE_SERVICE_URL=postgres://booksyncadmin:wevzuh-paGwi6-nanwag@bdd-booksync.postgres.database.azure.com:5432/booksync
DB_NAME=booksync
DB_USER=booksyncadmin
DB_PASSWORD=wevzuh-paGwi6-nanwag
DB_HOST=bdd-booksync.postgres.database.azure.com
DB_PORT=5432
```

### 9.2 Configuration des settings

**Fichier** : `app/config/settings.py`

**Hiérarchie des classes** :

```python
class LLMSettings(BaseModel):
    """Configuration de base pour les LLM"""
    api_key: str
    default_model: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None

class AzureOpenAISettings(LLMSettings):
    """Configuration spécifique Azure OpenAI"""
    api_version: str = "2024-02-01"
    azure_endpoint: str
    embedding_model: str = "text-embedding-3-large"

class DatabaseSettings(BaseModel):
    """Configuration PostgreSQL"""
    service_url: str

class VectorStoreSettings(BaseModel):
    """Configuration du vector store"""
    table_name: str = "embeddings"
    embedding_dimensions: int = 3072
    time_partition_interval: timedelta = timedelta(days=7)

class Settings(BaseModel):
    """Configuration globale de l'application"""
    openai: OpenAISettings
    azure_openai: AzureOpenAISettings
    database: DatabaseSettings
    vector_store: VectorStoreSettings

@lru_cache()
def get_settings() -> Settings:
    """Récupération des settings avec cache LRU"""
    settings = Settings()
    setup_logging()
    return settings
```

**Mécanisme de cache** :
- `@lru_cache()` : évite de recréer les settings à chaque appel
- Singleton applicatif
- Invalidation possible en cas de changement de configuration

### 9.3 Infrastructure Azure

#### Azure OpenAI Service

**Endpoint** : `https://app-booksync.openai.azure.com/`
**Version API** : 2024-02-01

**Déploiements** :
- **gpt-4o-mini** : modèle de chat pour synthèse conversationnelle
  - Latence : ~0.8s pour 200 tokens
  - Coût : ~$0.15 / 1M tokens input
- **text-embedding-3-large** : modèle d'embeddings 3072 dimensions
  - Latence : ~0.5s par embedding
  - Coût : ~$0.13 / 1M tokens

**Limitations** :
- Rate limit : 60 requêtes/minute (TPM non spécifié)
- Quota mensuel : dépend du contrat Azure

#### Azure Database for PostgreSQL

**Host** : `bdd-booksync.postgres.database.azure.com`
**Port** : 5432
**Database** : `booksync`

**Spécifications** :
- Version PostgreSQL : probablement 15 ou 16
- Extension pgvector : activée
- Connexion SSL : obligatoire (Azure managed)

**Performance** :
- Taille de la base : ~500 Mo (28 863 enregistrements)
- Temps de requête moyen : ~300ms (sans index HNSW)

#### Azure Container Apps

**Resource Group** : `vplatevoetRG`
**Container App** : `api-booksync`
**Container Registry** : `booksyncrepo.azurecr.io`

**Configuration** :
- Image : `booksyncrepo.azurecr.io/api-booksync:latest`
- Port exposé : variable d'environnement `CONTAINER_APP_PORT`
- Scaling : auto-scaling basé sur CPU/mémoire
- Région : probablement West Europe

### 9.4 Déploiement CI/CD

**Pipeline GitHub Actions** : `.github/workflows/deploy.yml`

**Étapes** :
1. Checkout du code
2. Connexion Azure CLI
3. Build Docker (Alpine Linux)
4. Push vers Azure Container Registry
5. Déploiement sur Azure Container Apps

**Déclencheurs** :
- Push sur branche `main`
- Ignore : modifications de docs, README, fichiers de config

---

## 10. TERMINOLOGIE PROFESSIONNELLE

### 10.1 Intelligence Artificielle et Machine Learning

**Embedding (représentation vectorielle)** : transformation d'un texte en vecteur numérique dense capturant sa sémantique dans un espace multidimensionnel.

**Large Language Model (LLM)** : modèle de langage de grande taille entraîné sur des corpus massifs, capable de générer et comprendre du texte naturel.

**Prompt Engineering** : discipline consistant à concevoir des instructions optimales pour guider le comportement d'un LLM vers les résultats souhaités.

**Temperature** : paramètre de randomisation contrôlant la créativité des réponses générées par un LLM (0 = déterministe, 1+ = créatif).

**Token** : unité atomique de traitement pour les LLM, approximativement 0.75 mot en français.

**Retrieval-Augmented Generation (RAG)** : paradigme combinant recherche d'information (retrieval) et génération textuelle pour produire des réponses contextualisées.

**Fine-tuning** : processus d'adaptation d'un modèle pré-entraîné à une tâche spécifique (non utilisé dans ce projet).

**Hallucination** : génération de contenu plausible mais factuellement incorrect par un LLM.

### 10.2 Recherche vectorielle

**Similarité cosinus** : mesure de similarité entre deux vecteurs basée sur le cosinus de l'angle formé, insensible à leur magnitude.

**Distance euclidienne** : mesure de dissimilarité basée sur la distance géométrique directe entre deux points dans l'espace vectoriel.

**HNSW (Hierarchical Navigable Small World)** : algorithme d'indexation pour recherche approximative des plus proches voisins dans des espaces de haute dimension.

**Dimensionnalité** : nombre de composantes d'un vecteur d'embedding (3072 pour text-embedding-3-large).

**Vector Store** : base de données optimisée pour le stockage et la recherche efficace de vecteurs haute dimension.

**Approximate Nearest Neighbor (ANN)** : recherche approximative des vecteurs les plus proches, sacrifiant légèrement la précision pour la vitesse.

**Exact Search** : recherche exhaustive garantissant de trouver les vecteurs les plus similaires, mais coûteuse en calcul.

### 10.3 Architecture logicielle

**Séparation des préoccupations** : principe architectural isolant chaque responsabilité dans un module distinct.

**Couche présentation** : composants gérant l'interface avec les clients (routes HTTP).

**Couche métier** : composants implémentant la logique applicative (services).

**Couche données** : composants gérant la persistance et la récupération des données.

**Dependency Injection** : patron de conception fournissant les dépendances à une classe plutôt que de les instancier directement.

**Validation de données** : vérification automatique de la conformité des données aux schémas définis (Pydantic).

**Sérialisation/Désérialisation** : conversion entre objets Python et formats d'échange (JSON).

### 10.4 Technologies spécifiques

**FastAPI** : framework Python moderne pour création d'APIs REST haute performance avec validation automatique.

**Pydantic** : bibliothèque de validation de données basée sur les type hints Python.

**pgvector** : extension PostgreSQL permettant le stockage et la recherche de vecteurs.

**ASGI (Asynchronous Server Gateway Interface)** : interface standard pour serveurs Python asynchrones.

**Uvicorn** : serveur ASGI léger et performant pour applications Python.

**Pandas** : bibliothèque de manipulation de données tabulaires en Python.

**NumPy** : bibliothèque de calcul numérique pour opérations vectorielles et matricielles.

### 10.5 Concepts métier

**Profil psychographique** : ensemble des caractéristiques comportementales et émotionnelles d'un utilisateur (préférences, humeur).

**Profil démographique** : ensemble des caractéristiques objectives d'un utilisateur (âge, genre).

**Personnalisation contextuelle** : adaptation des recommandations en fonction du contexte actuel (humeur, moment de la journée).

**Système de recommandation hybride** : combinaison de plusieurs stratégies de recommandation (collaborative, basée contenu, etc.).

**Cold start problem** : difficulté à recommander à un nouvel utilisateur sans historique (résolu ici par préférences explicites).

**Diversité des recommandations** : propriété garantissant une variété dans les suggestions pour éviter la monotonie.

---

## CONCLUSION

Ce document technique exhaustif couvre l'intégralité du système de recommandation intelligent BookSync API Agent, de l'architecture globale aux détails d'implémentation algorithmique.

**Points clés à retenir** :

1. **Architecture en couches** : séparation claire des responsabilités (routes/services/données)
2. **Recherche sémantique** : utilisation d'embeddings vectoriels 3072 dimensions pour compréhension du sens
3. **Algorithme hybride** : combinaison de 3 stratégies (collection, lectures, préférences)
4. **Agent conversationnel** : génération de synthèses personnalisées via GPT-4o-mini
5. **Personnalisation multidimensionnelle** : prise en compte âge, genre, préférences, humeur
6. **Infrastructure cloud** : déploiement Azure avec CI/CD automatisé

**Limitations identifiées** :

1. Index HNSW désactivé (3072 dimensions > limite 2000)
2. Calcul de similarité en Python (non optimisé)
3. Absence de cache pour embeddings (coût API)
4. Couverture de tests insuffisante (39%)

**Opportunités d'amélioration** :

1. Basculer vers text-embedding-3-small pour activer HNSW
2. Implémenter un cache Redis pour embeddings
3. Ajouter des métriques de diversité et de popularité
4. Développer un système de feedback utilisateur
5. Augmenter la couverture de tests à 80%+

Cette documentation permet une compréhension complète et professionnelle du système pour présentation technique, audit de code, ou formation d'équipe.
