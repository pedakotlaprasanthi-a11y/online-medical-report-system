pipeline {
    agent any

    environment {
        IMAGE_NAME = 'medical-report-app'
        CONTAINER_NAME = 'medical-report-container'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install and Check') {
            steps {
                bat 'py -m pip install -r requirements.txt'
                bat 'py -m compileall -q app.py'
            }
        }
        stage('Build Docker Image') {
            steps { bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% .' }
        }
        stage('Deploy Container') {
            steps {
                script { bat(returnStatus: true, script: 'docker rm -f %CONTAINER_NAME%') }
                bat 'docker run -d --name %CONTAINER_NAME% -p 5000:5000 -v medical_uploads:/app/uploads %IMAGE_NAME%:%BUILD_NUMBER%'
            }
        }
    }
    post {
        success { echo 'Medical Report Management application deployed successfully.' }
        failure { echo 'Pipeline failed. Check the stage logs.' }
    }
}
