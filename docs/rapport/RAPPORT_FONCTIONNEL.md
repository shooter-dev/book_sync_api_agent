# RAPPORT FONCTIONNEL - BOOK SYNC

## Vue d'ensemble

**Book Sync** est une plateforme web de gestion de collections de livres avec un modèle économique gratuit et des recommandations personnalisées assisté par l'intelligence artificielle.
La plateforme permet aux utilisateurs de gérer leur bibliothèque personnelle tout en bénéficiant de suggestions adaptées à leurs préférences et habitudes de lecture.

## Objectif du projet

Le projet répond au besoin des lecteurs de centraliser et organiser leurs collections de livres numériques et physiques,
tout en découvrant des nouveaux titres grâce au systéme de recommendation IA. Book Sync propose une expérience personnalisée avec des fonctionnalités avancées pour les utilisateurs premium.

## Utilisateurs cibles

### Utilisateurs de base (gratuit)
- Lecteurs occasionnels souhaitant organiser leur collection
- Utilisateurs découvrant la plateforme
- Personnes cherchant des recommandations simples

### Utilisateurs premium (payant)
- Lecteurs assidus avec de grandes collections
- Utilisateurs souhaitant des analyses détaillées de leurs habitudes
- Personnes cherchant des recommandations IA avancées et personnalisées

## Fonctionnalités principales

### 1. Gestion des comptes utilisateurs

**Inscription et connexion :**
- Création de compte avec validation email
- Authentification sécurisée avec option "Se souvenir de moi"
- Gestion des mots de passe avec modification possible

**Profil utilisateur :**
- Informations personnelles (pseudo, email)
- **Définition d'âge unique** : L'âge ne peut être défini qu'une seule fois pour des raisons de sécurité mais il n'est obligatoire
- Gestion des préférences de contenu mature (16+ ans)
- Classification automatique adulte/mineur (18+ ans)

**Système d'abonnement :**
- Passage gratuit vers premium
- Annulation d'abonnement possible
- Contrôle d'accès basé sur les groupes Django

### 2. Gestion de collection personnelle

**Ajout et organisation :**
- Recherche de livres par titre de série ou ISBN
- Ajout/suppression de volumes à la collection personnelle
- Visualisation groupée par séries
- Suivi du pourcentage de complétion par série

**Navigation et consultation :**
- Interface détaillée par volume et série
- Navigation entre volumes d'une même série
- Affichage des métadonnées complètes (auteur, éditeur, genre, date)
- Gestion des couvertures et contenus visuels

**Statistiques de collection :**
- Nombre total de livres possédés
- Nombre de séries dans la collection
- Progression de complétion par série

### 3. Suivi de lecture (fonctionnalité premium)

**Tracking des lectures :**
- Marquage des volumes lus
- Historique de lecture avec dates
- Statistiques de lecture personnalisées

**Analyses premium :**
- Tendances de lecture
- Genres et types préférés
- Analyses temporelles des habitudes

### 4. Système de recommandations IA

**Préférences utilisateur :**
- Sélection des genres préférés (like/dislike)
- Choix des types de publications favoris
- Personnalisation fine des préférences

**Recommandations de base :**
- Suggestions basées sur les préférences déclarées
- Interface simple de recommandation

**Recommandations premium :**
- **Intégration API IA externe** pour analyses avancées
- Recommandations basées sur l'historique de collection
- Prise en compte de l'historique de lecture
- Analyses de contenu des volumes possédés
- Suggestions personnalisées avec justifications

**Paramètres de recommandation :**
- Prise en compte de l'âge utilisateur
- Sélection d'humeur pour recommandations contextuelles
- Commentaires libres pour affiner les suggestions
- Types de prédiction variés

### 5. Recherche et découverte

**Moteur de recherche intelligent :**
- Recherche par titre de série (recherche textuelle)
- Recherche par ISBN (détection automatique du format)
- Résultats filtrés et pertinents
- Interface popup pour recherche rapide

**Catalogue complet :**
- Base de données de 13 modèles interconnectés
- Informations complètes sur les séries, volumes, auteurs
- Métadonnées enrichies (genres, éditeurs, types)

### 6. Gestion du contenu mature

**Filtrage par âge :**
- Protection automatique des mineurs (< 16 ans)
- Paramètres de contenu mature pour 16+ ans
- Masquage/affichage des contenus explicites
- Respect des restrictions légales

**Contrôle parental :**
- Définition d'âge sécurisée (non modifiable)
- Classification automatique du contenu
- Interface adaptée par tranche d'âge

## Parcours utilisateur type

### Nouvel utilisateur
1. **Inscription** avec email et mot de passe
2. **Définition de l'âge** (unique et définitive)
3. **Configuration des préférences** de contenu mature si éligible
4. **Ajout de premiers livres** via recherche
5. **Définition des préférences** de genres/types
6. **Accès aux recommandations de base**

### Utilisateur expérimenté vers premium
1. **Analyse des besoins** avancés
2. **Souscription à l'abonnement premium**
3. **Accès aux fonctionnalités avancées** :
   - Analyses de lecture détaillées
   - Recommandations IA personnalisées
   - Statistiques approfondies
4. **Utilisation régulière** des outils premium

## Interface utilisateur

### Design et ergonomie
- **Interface responsive** adaptée mobile/desktop
- **Design moderne** avec système MangaCollec
- **Navigation intuitive** avec menus contextuels
- **Couleur signature** : Rouge #CF000A

### Pages principales
- **Accueil** : Vue d'ensemble et navigation
- **Collection** : Gestion de la bibliothèque personnelle
- **Recherche** : Découverte de nouveaux titres
- **Recommandations** : Suggestions personnalisées (premium)
- **Profil** : Gestion compte et préférences

## Modèle économique

### Version gratuite
- Gestion de collection illimitée
- Recommandations de base
- Fonctionnalités essentielles

### Version premium
- **Analyses de lecture avancées**
- **Recommandations IA personnalisées**
- **API IA externe** pour suggestions expertes
- **Support prioritaire**

## Sécurité et protection des données

### Protection des utilisateurs
- **Hachage des mots de passe** avec Django
- **Sessions sécurisées** avec expiration configurable
- **Protection CSRF** sur toutes les actions sensibles
- **Validation des entrées** utilisateur

### Respect de la vie privée
- **Âge défini une seule fois** pour éviter la manipulation
- **Contrôle granulaire** des préférences de contenu
- **Données anonymisées** pour les analyses IA
- **Conformité RGPD** dans la gestion des données

## Points forts fonctionnels

1. **Expérience utilisateur fluide** avec interface moderne
2. **Personnalisation avancée** grâce aux préférences utilisateur
3. **Intelligence artificielle intégrée** pour recommandations pertinentes
4. **Modèle freemium équilibré** avec valeur ajoutée claire
5. **Sécurité renforcée** pour protection des mineurs
6. **Scalabilité** avec architecture modulaire Django

## Roadmap fonctionnelle

### Améliorations court terme
- **Import/export** de collections existantes
- **Partage social** de lectures et recommandations
- **Notifications** pour nouveaux volumes de séries suivies

### Évolutions long terme
- **Application mobile native**
- **Intégration marchands** pour achat direct
- **Communauté** avec avis et discussions
- **IA conversationnelle** pour recommandations interactives

## Conclusion

Book Sync répond efficacement aux besoins des lecteurs modernes en combinant gestion de collection intuitive et recommandations IA intelligentes. Le modèle freemium permet une adoption large tout en monétisant les fonctionnalités avancées. La plateforme pose les bases d'un écosystème complet autour de la lecture personnalisée.