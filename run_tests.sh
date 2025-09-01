#!/bin/bash

# Script de lancement des tests unitaires avec coverage HTML
# Usage: ./run_tests.sh [OPTIONS]

set -e

# Configuration
PROJECT_NAME="Book Sync API"
VENV_PATH=".venv"
REPORTS_DIR="tests/reports"
HTMLCOV_DIR="htmlcov"

# Couleurs pour la sortie
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage avec couleurs
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction d'aide
show_help() {
    cat << EOF
🧪 ${PROJECT_NAME} - Tests Runner

Usage: $0 [OPTIONS]

OPTIONS:
    --unit          Run only unit tests (marker: @pytest.mark.unit)
    --integration   Run only integration tests (marker: @pytest.mark.integration)
    --api           Run only API tests (marker: @pytest.mark.api)
    --coverage      Generate coverage report only (skip HTML report)
    --no-html       Skip HTML coverage report generation
    --open          Open HTML reports after execution
    --clean         Clean previous reports before running
    --verbose       Extra verbose output
    --help          Show this help message

EXAMPLES:
    $0                          # Run all tests with full reporting
    $0 --unit                   # Run only unit tests
    $0 --clean --open           # Clean, run tests, and open reports
    $0 --no-html --coverage     # Generate only terminal coverage

OUTPUT:
    - Terminal coverage: Console output
    - HTML coverage: ${HTMLCOV_DIR}/index.html
    - Test report: ${REPORTS_DIR}/report.html
    - Coverage XML: coverage.xml

EOF
}

# Validation de l'environnement
validate_environment() {
    print_info "Validation de l'environnement..."
    
    # Vérifier l'environnement virtuel
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Environnement virtuel non trouvé: $VENV_PATH"
        exit 1
    fi
    
    # Vérifier pytest
    if ! python -c "import pytest" 2>/dev/null; then
        print_error "pytest non installé. Exécutez: pip install -r requirements.txt"
        exit 1
    fi
    
    # Créer les répertoires nécessaires
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$HTMLCOV_DIR"
    
    print_success "Environnement validé"
}

# Nettoyage des rapports précédents
clean_reports() {
    print_info "Nettoyage des rapports précédents..."
    rm -rf "$HTMLCOV_DIR"/*
    rm -rf "$REPORTS_DIR"/*
    rm -f coverage.xml .coverage
    print_success "Rapports nettoyés"
}

# Exécution des tests
run_tests() {
    local test_type="$1"
    local extra_args="$2"
    
    print_info "Lancement des tests: $test_type"
    echo "======================================="
    
    # Construction de la commande pytest
    local pytest_cmd="pytest"
    
    # Ajout des marqueurs selon le type de test
    case "$test_type" in
        "unit")
            pytest_cmd="$pytest_cmd -m unit"
            ;;
        "integration")
            pytest_cmd="$pytest_cmd -m integration"
            ;;
        "api")
            pytest_cmd="$pytest_cmd -m api"
            ;;
        "all")
            # Pas de filtre, tous les tests
            ;;
    esac
    
    # Ajout des arguments supplémentaires
    pytest_cmd="$pytest_cmd $extra_args"
    
    print_info "Commande: $pytest_cmd"
    echo ""
    
    # Exécution
    if eval "$pytest_cmd"; then
        print_success "Tests terminés avec succès"
        return 0
    else
        print_error "Certains tests ont échoué"
        return 1
    fi
}

# Ouverture des rapports
open_reports() {
    print_info "Ouverture des rapports..."
    
    if [ -f "$HTMLCOV_DIR/index.html" ]; then
        print_success "Ouverture du rapport de coverage"
        open "$HTMLCOV_DIR/index.html"
    fi
    
    if [ -f "$REPORTS_DIR/report.html" ]; then
        print_success "Ouverture du rapport de tests"
        open "$REPORTS_DIR/report.html"
    fi
}

# Variables par défaut
TEST_TYPE="all"
EXTRA_ARGS=""
CLEAN=false
OPEN_REPORTS=false
NO_HTML=false
COVERAGE_ONLY=false

# Parsing des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --api)
            TEST_TYPE="api"
            shift
            ;;
        --coverage)
            COVERAGE_ONLY=true
            shift
            ;;
        --no-html)
            NO_HTML=true
            EXTRA_ARGS="$EXTRA_ARGS --cov-report=term-missing --cov-report=xml"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --open)
            OPEN_REPORTS=true
            shift
            ;;
        --verbose)
            EXTRA_ARGS="$EXTRA_ARGS -vv"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Exécution principale
main() {
    echo "🧪 $PROJECT_NAME - Tests Runner"
    echo "======================================="
    echo ""
    
    # Validation
    validate_environment
    
    # Nettoyage si demandé
    if [ "$CLEAN" = true ]; then
        clean_reports
    fi
    
    # Exécution des tests
    if run_tests "$TEST_TYPE" "$EXTRA_ARGS"; then
        echo ""
        print_success "✨ Tests terminés avec succès!"
        
        # Affichage des rapports générés
        echo ""
        print_info "Rapports générés:"
        
        if [ "$NO_HTML" = false ]; then
            echo "  📊 Coverage HTML: $HTMLCOV_DIR/index.html"
            echo "  📋 Test Report:   $REPORTS_DIR/report.html"
        fi
        
        echo "  📈 Coverage XML:  coverage.xml"
        echo ""
        
        # Ouverture automatique si demandé
        if [ "$OPEN_REPORTS" = true ] && [ "$NO_HTML" = false ]; then
            open_reports
        fi
        
        exit 0
    else
        print_error "❌ Des tests ont échoué"
        exit 1
    fi
}

# Lancement du script
main