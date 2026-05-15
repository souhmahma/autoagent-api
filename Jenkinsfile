// ╔══════════════════════════════════════════════════════════════════╗
// ║              AutoAgent API — Jenkinsfile                         ║
// ╚══════════════════════════════════════════════════════════════════╝

pipeline {

    // On utilise l'agent par défaut de Jenkins pour éviter le bug de montage de volume
    agent any

    environment {
        PYTHON_VERSION   = '3.11'
        REGISTRY_URL     = "${env.REGISTRY_URL ?: 'registry.example.com/autoagent-api'}"
        IMAGE_BACKEND    = "${REGISTRY_URL}/backend"
        IMAGE_FRONTEND   = "${REGISTRY_URL}/frontend"

        // Credentials Jenkins
        SECRET_KEY       = credentials('secret-key')
        ADMIN_USERNAME   = credentials('admin-username')
        ADMIN_PASSWORD   = credentials('admin-password')
        ADMIN_EMAIL      = credentials('admin-email')
        GEMINI_API_KEY   = credentials('gemini-api-key')
    }

    options {
        timeout(time: 45, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '5'))
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/1 * * * *')
    }

    stages {

        // ── Stage 0 : Checkout ──────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    def gitCommit = env.GIT_COMMIT ?: sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.SHORT_SHA = gitCommit.take(8)
                    def currentBranch = env.GIT_BRANCH ?: env.BRANCH_NAME ?: 'unknown'
                    echo "Branch : ${currentBranch} | SHA : ${env.SHORT_SHA}"
                }
            }
        }

        // ── Stage 1 : Lint & Tests via Docker Local ────────────────
        // Au lieu de demander à Jenkins de gérer l'agent Docker, on lance un conteneur éphémère à la main
        stage('Lint & Tests') {
            steps {
                echo "Exécution des tests et du linting dans un conteneur isolé..."
                sh """
                    docker run --rm -v ${WORKSPACE}:/workspace -w /workspace python:3.11-slim sh -c "
                        pip install --quiet flake8 black isort pytest pytest-cov &&
                        echo '── Linting ──' &&
                        flake8 app/ --max-line-length=100 --exclude=__pycache__ &&
                        black --check app/ --line-length 100 &&
                        isort --check-only app/ --profile black &&
                        echo '── Unit & Integration Tests ──' &&
                        DATABASE_URL='sqlite:///./test.db' pytest tests/ -v --cov=app --cov-report=xml:coverage.xml
                    "
                """
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: '**/test-results/*.xml'
                    // facultatif selon tes plugins installés :
                    // publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        // ── Stage 2 : Security ──────────────────────────────────────
        stage('Security') {
            steps {
                sh """
                    docker run --rm -v ${WORKSPACE}:/workspace -w /workspace python:3.11-slim sh -c "
                        pip install --quiet bandit &&
                        bandit -r app/ -ll --exclude app/tests
                    "
                """
            }
        }

        // ── Stage 3 : Build & Push images ───────────────────────────
        stage('Build & Push') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    buildingTag()
                    changeRequest()
                }
            }
            steps {
                script {
                    def backendTags  = []
                    def frontendTags = []
                    def currentBranch = env.GIT_BRANCH ?: env.BRANCH_NAME ?: 'unknown'
                    def sha = env.SHORT_SHA ?: 'unknown'

                    if (env.TAG_NAME) {
                        backendTags  = ["${IMAGE_BACKEND}:${env.TAG_NAME}", "${IMAGE_BACKEND}:latest"]
                        frontendTags = ["${IMAGE_FRONTEND}:${env.TAG_NAME}", "${IMAGE_FRONTEND}:latest"]
                    } else if (currentBranch == 'origin/main' || currentBranch == 'main') {
                        backendTags  = ["${IMAGE_BACKEND}:latest", "${IMAGE_BACKEND}:${sha}"]
                        frontendTags = ["${IMAGE_FRONTEND}:latest", "${IMAGE_FRONTEND}:${sha}"]
                    } else if (currentBranch ==~ /.*develop.*/) {
                        backendTags  = ["${IMAGE_BACKEND}:develop", "${IMAGE_BACKEND}:${sha}"]
                        frontendTags = ["${IMAGE_FRONTEND}:develop", "${IMAGE_FRONTEND}:${sha}"]
                    } else {
                        def safeBranch = currentBranch.replaceAll('[^a-zA-Z0-9._-]', '-')
                        backendTags  = ["${IMAGE_BACKEND}:${safeBranch}"]
                        frontendTags = ["${IMAGE_FRONTEND}:${safeBranch}"]
                    }

                    withCredentials([usernamePassword(
                        credentialsId: 'registry-creds',
                        usernameVariable: 'REG_USER',
                        passwordVariable: 'REG_PASS'
                    )]) {
                        sh "docker login ${REGISTRY_URL.split('/')[0]} -u \$REG_USER -p \$REG_PASS"
                    }

                    // Build Backend
                    echo "Building backend → ${backendTags}"
                    def backendTagArgs = backendTags.collect { "--tag ${it}" }.join(' ')
                    sh "docker build --file app/Dockerfile ${backendTagArgs} ."
                    backendTags.each { sh "docker push ${it}" }

                    // Build Frontend
                    echo "Building frontend → ${frontendTags}"
                    def frontendTagArgs = frontendTags.collect { "--tag ${it}" }.join(' ')
                    sh "docker build --file frontend/Dockerfile ${frontendTagArgs} ."
                    frontendTags.each { sh "docker push ${it}" }

                    env.BACKEND_IMAGE_TAG  = backendTags[0]
                    env.FRONTEND_IMAGE_TAG = frontendTags[0]
                }
            }
        }

        // ── Stage 4 : Verify (smoke test) ───────────────────────────
        stage('Verify') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    buildingTag()
                    changeRequest()
                }
            }
            steps {
                script {
                    try {
                        sh """
                            docker run -d --name smoke-backend-${BUILD_NUMBER} \\
                                -p 8001:8000 \\
                                -e DATABASE_URL="sqlite:///./smoke.db" \\
                                -e SECRET_KEY="${SECRET_KEY}" \\
                                -e ADMIN_USERNAME="${ADMIN_USERNAME}" \\
                                -e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \\
                                -e ADMIN_EMAIL="${ADMIN_EMAIL}" \\
                                -e GEMINI_API_KEY="${GEMINI_API_KEY}" \\
                                ${env.BACKEND_IMAGE_TAG}
                        """
                        sh 'sleep 8'
                        sh "docker exec smoke-backend-${BUILD_NUMBER} python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\""
                        echo "✓ Backend health OK"

                        sh """
                            docker run -d --name smoke-frontend-${BUILD_NUMBER} \\
                                -p 8080:80 \\
                                ${env.FRONTEND_IMAGE_TAG}
                        """
                        sh 'sleep 5'
                        sh "docker exec smoke-frontend-${BUILD_NUMBER} wget -qO- http://localhost:80 > /dev/null"
                        echo "✓ Frontend health OK"

                    } finally {
                        sh "docker rm -f smoke-backend-${BUILD_NUMBER} smoke-frontend-${BUILD_NUMBER} 2>/dev/null || true"
                    }
                }
            }
        }
    }

    // ── POST ────────────────────────────────────────────────────────
    post {
        success {
            script {
                def branch = env.GIT_BRANCH ?: env.BRANCH_NAME ?: 'unknown'
                def sha = env.SHORT_SHA ?: 'unknown'
                echo "✅ Pipeline terminée avec succès — ${branch} @ ${sha}"
            }
        }
        failure {
            script {
                def branch = env.GIT_BRANCH ?: env.BRANCH_NAME ?: 'unknown'
                def sha = env.SHORT_SHA ?: 'unknown'
                echo "❌ Pipeline échouée — ${branch} @ ${sha}"
            }
        }
        always {
            cleanWs()
        }
    }
}
