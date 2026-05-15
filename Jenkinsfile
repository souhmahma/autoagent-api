// ╔══════════════════════════════════════════════════════════════════╗
// ║              AutoAgent API — Jenkinsfile                         ║
// ╚══════════════════════════════════════════════════════════════════╝

pipeline {

    // ── Agent global : Docker-in-Docker ─────────────────────────────
    agent {
        docker {
            image 'docker:26'
            args  '--privileged -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    // ── Variables globales Statiques ────────────────────────────────
    environment {
        PYTHON_VERSION   = '3.11'
        REGISTRY_URL     = "${env.REGISTRY_URL ?: 'registry.example.com/autoagent-api'}"
        IMAGE_BACKEND    = "${REGISTRY_URL}/backend"
        IMAGE_FRONTEND   = "${REGISTRY_URL}/frontend"

        // Credentials Jenkins injectés de manière isolée
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

        // ── Stage 0 : Checkout & Init Dynamique ─────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    // Calcul dynamique et injection sécurisée dans l'environnement global du build
                    def gitCommit = env.GIT_COMMIT ?: sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.SHORT_SHA = gitCommit.take(8)
                    
                    def currentBranch = env.GIT_BRANCH ?: env.BRANCH_NAME ?: 'unknown'
                    echo "Branch détectée : ${currentBranch} | SHA calculé : ${env.SHORT_SHA}"
                }
            }
        }

        // ── Stage 1 : Lint ──────────────────────────────────────────
        stage('Lint') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    pip install --quiet flake8 black isort
                    echo "── flake8 ──────────────────────────────"
                    flake8 app/ --max-line-length=100 --exclude=__pycache__
                    echo "── black ───────────────────────────────"
                    black --check app/ --line-length 100
                    echo "── isort ───────────────────────────────"
                    isort --check-only app/ --profile black
                '''
            }
        }

        // ── Stage 2 : Tests ─────────────────────────────────────────
        stage('Tests') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }
            environment {
                PIP_CACHE_DIR = "${WORKSPACE}/.cache/pip"
            }
            steps {
                sh 'pip install --quiet -r app/requirements.txt -r requirements-test.txt'

                sh '''
                    echo "── Unit tests ──────────────────────────"
                    DATABASE_URL="sqlite:///./test_unit.db" \
                    pytest tests/unit/ -v \
                        --cov=app \
                        --cov-report=xml:coverage-unit.xml \
                        --cov-report=term-missing \
                        -m "not integration and not e2e"
                '''

                sh '''
                    echo "── Integration tests ───────────────────"
                    DATABASE_URL="sqlite:///./test_integration.db" \
                    pytest tests/integration/ -v \
                        --cov=app \
                        --cov-report=xml:coverage-integration.xml \
                        --cov-report=term-missing
                '''

                sh '''
                    echo "── E2E tests ───────────────────────────"
                    DATABASE_URL="sqlite:///./test_e2e.db" \
                    pytest tests/e2e/ -v
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: '**/test-results/*.xml'
                    publishCoverage adapters: [
                        coberturaAdapter('coverage-unit.xml'),
                        coberturaAdapter('coverage-integration.xml')
                    ]
                }
            }
        }

        // ── Stage 3 : Security ──────────────────────────────────────
        stage('Security') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    pip install --quiet bandit
                    echo "── bandit ───────────────────────────────"
                    bandit -r app/ -ll --exclude app/tests -f json -o bandit-report.json || true
                    bandit -r app/ -ll --exclude app/tests
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                }
            }
        }

        // ── Stage 4 : Build & Push images ───────────────────────────
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
                    sh "docker pull ${IMAGE_BACKEND}:latest 2>/dev/null || true"
                    def backendTagArgs = backendTags.collect { "--tag ${it}" }.join(' ')
                    sh """
                        docker build \\
                            --file app/Dockerfile \\
                            --cache-from ${IMAGE_BACKEND}:latest \\
                            --build-arg BUILDKIT_INLINE_CACHE=1 \\
                            ${backendTagArgs} \\
                            .
                    """
                    backendTags.each { sh "docker push ${it}" }

                    // Build Frontend
                    echo "Building frontend → ${frontendTags}"
                    sh "docker pull ${IMAGE_FRONTEND}:latest 2>/dev/null || true"
                    def frontendTagArgs = frontendTags.collect { "--tag ${it}" }.join(' ')
                    sh """
                        docker build \\
                            --file frontend/Dockerfile \\
                            --cache-from ${IMAGE_FRONTEND}:latest \\
                            --build-arg BUILDKIT_INLINE_CACHE=1 \\
                            ${frontendTagArgs} \\
                            .
                    """
                    frontendTags.each { sh "docker push ${it}" }

                    env.BACKEND_IMAGE_TAG  = backendTags.find { it.contains(sha) } ?: backendTags[0]
                    env.FRONTEND_IMAGE_TAG = frontendTags.find { it.contains(sha) } ?: frontendTags[0]
                }
            }
        }

        // ── Stage 5 : Verify (smoke test) ───────────────────────────
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
                        sh """
                            docker exec smoke-backend-${BUILD_NUMBER} \\
                                python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \\
                            || (docker logs smoke-backend-${BUILD_NUMBER} && exit 1)
                        """
                        echo "✓ Backend health OK"

                        sh """
                            docker run -d --name smoke-frontend-${BUILD_NUMBER} \\
                                -p 8080:80 \\
                                ${env.FRONTEND_IMAGE_TAG}
                        """
                        sh 'sleep 5'
                        sh """
                            docker exec smoke-frontend-${BUILD_NUMBER} \\
                                wget -qO- http://localhost:80 > /dev/null \\
                            || (docker logs smoke-frontend-${BUILD_NUMBER} && exit 1)
                        """
                        echo "✓ Frontend health OK"

                    } finally {
                        sh "docker rm -f smoke-backend-${BUILD_NUMBER} smoke-frontend-${BUILD_NUMBER} 2>/dev/null || true"
                    }
                }
            }
        }
    }

    // ── POST — Actions de clôture isolées ───────────────────────────
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
            script {
                try {
                    cleanWs()
                } catch (Exception e) {
                    echo "Note: Nettoyage du workspace ignoré ou géré hors contexte Node."
                }
            }
        }
    }
}
