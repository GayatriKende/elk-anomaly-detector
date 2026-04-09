pipeline {
    agent any

    environment {
        DEPLOY_DIR = '/home/ubuntu/elk-anomaly-detector'
        SERVER_IP  = 'localhost'
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo 'Checking out code from Git...'
                checkout scm
            }
        }

        stage('Validate Files') {
            steps {
                echo 'Validating all required files exist...'
                sh '''
                    test -f docker-compose.yml       && echo "✓ docker-compose.yml"
                    test -f logstash/logstash.conf   && echo "✓ logstash.conf"
                    test -f filebeat/filebeat.yml    && echo "✓ filebeat.yml"
                    test -f app/app.py               && echo "✓ app.py"
                    test -f ml/anomaly_detector.py   && echo "✓ anomaly_detector.py"
                '''
            }
        }

        stage('Stop Old Containers') {
            steps {
                echo 'Stopping existing containers...'
                sh '''
                    cd ${DEPLOY_DIR}
                    docker-compose down --remove-orphans || true
                    sleep 5
                '''
            }
        }

        stage('Start ELK Stack') {
            steps {
                echo 'Starting Elasticsearch first...'
                sh '''
                    cd ${DEPLOY_DIR}
                    docker-compose up -d elasticsearch
                    echo "Waiting 45 seconds for Elasticsearch to start..."
                    sleep 45
                '''
            }
        }

        stage('Health Check - Elasticsearch') {
            steps {
                echo 'Checking Elasticsearch health...'
                sh '''
                    for i in 1 2 3 4 5; do
                        STATUS=$(curl -s http://localhost:9200/_cluster/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "down")
                        echo "Attempt $i: Elasticsearch status = $STATUS"
                        if [ "$STATUS" = "green" ] || [ "$STATUS" = "yellow" ]; then
                            echo "Elasticsearch is ready!"
                            break
                        fi
                        sleep 15
                    done
                '''
            }
        }

        stage('Start Remaining Services') {
            steps {
                echo 'Starting Kibana, Logstash, Filebeat, Flask App...'
                sh '''
                    cd ${DEPLOY_DIR}
                    docker-compose up -d kibana logstash
                    sleep 20
                    docker-compose up -d filebeat flask-app
                    sleep 10
                '''
            }
        }

        stage('Verify All Containers') {
            steps {
                echo 'Verifying all containers are running...'
                sh '''
                    cd ${DEPLOY_DIR}
                    docker-compose ps
                    echo ""
                    echo "Container count:"
                    docker-compose ps --services | wc -l
                '''
            }
        }

        stage('Run ML Anomaly Detection') {
            steps {
                echo 'Running ML anomaly detection...'
                sh '''
                    sleep 30
                    python3 ${DEPLOY_DIR}/ml/anomaly_detector.py || true
                '''
            }
        }
    }

    post {
        success {
            echo """
            ========================================
            Pipeline Completed Successfully!
            Kibana  : http://${SERVER_IP}:5601
            Jenkins : http://${SERVER_IP}:8080
            Flask   : http://${SERVER_IP}:5000
            ========================================
            """
        }
        failure {
            echo 'Pipeline FAILED. Check logs above for errors.'
            sh 'docker-compose -f /home/ubuntu/elk-anomaly-detector/docker-compose.yml logs --tail=20 || true'
        }
    }
}
