pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        TERRAFORM_DIR = 'terraform'
    }

    triggers {
        pollSCM('H/2 * * * *') // Poll every 2 minutes
    }

    stages {

        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Login to AWS & ECR') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'BNmnx0bIy24ahJTSUi6MIEpYUVmCTV8dyMBfH6cq',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    bat """
                    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                    aws configure set region %AWS_REGION%
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    """
                }
            }
        }

        stage('Apply Infrastructure (Terraform)') {
            steps {
                dir("${TERRAFORM_DIR}") {
                    bat '''
                    terraform init -input=false
                    terraform apply -auto-approve
                    terraform output -json > tf_outputs.json
                    '''
                }
            }
        }

        stage('Update Frontend URL and Deploy to S3') {
            steps {
                script {
                    echo "🚀 Auto-updating ALB URLs and deploying to S3..."
                    bat """
                    "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" update_frontend_and_deploy.py "%WORKSPACE%"
                    """
                }
            }
        }

        stage('Build & Push Docker Images') {
            steps {
                script {
                    def services = [
                        'booking-service': 'Booking_Service',
                        'flight-service': 'Flight_Service',
                        'payment-service': 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse\\backend'
                    ]

                    services.each { repoName, folder ->
                        echo "Building and pushing image for ${repoName}..."
                        bat """
                        docker build -t %ECR_REGISTRY%/${repoName}:latest ${folder}
                        docker push %ECR_REGISTRY%/${repoName}:latest
                        """
                    }
                }
            }
        }

        stage('Force ECS Service Redeploy') {
            steps {
                bat '''
                echo Redeploying ECS Services...
                aws ecs update-service --cluster %CLUSTER_NAME% --service booking-service --force-new-deployment --region %AWS_REGION%
                aws ecs update-service --cluster %CLUSTER_NAME% --service flight-service --force-new-deployment --region %AWS_REGION%
                aws ecs update-service --cluster %CLUSTER_NAME% --service payment-service --force-new-deployment --region %AWS_REGION%
                aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --force-new-deployment --region %AWS_REGION%
                '''
            }
        }

        stage('Populate Databases') {
            steps {
                bat '''
                echo Populating Smart Trips and Flight Databases...
                "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" populate_smart_trips_db.py
                "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" Flight_Service\\populate_flights_db.py
                echo ✅ Database population complete.
                '''
            }
        }

        stage('TravelEase Deployment Complete') {
            steps {
                echo "--------------------------------------"
                echo "✅ TravelEase Deployment Complete!"
                echo "All infrastructure, images, and databases are now up to date."
                echo "--------------------------------------"
            }
        }

        stage('Open Deployed Website') {
            steps {
                echo "🌐 Opening deployed TravelEase website..."
                bat """
                powershell -Command "Start-Process 'chrome.exe' (Get-Content .\\terraform\\tf_outputs.json | ConvertFrom-Json | Select-Object -ExpandProperty frontend_website_url | Select-Object -ExpandProperty value)"
                """
            }
        }
    }

    post {
        success {
            echo '✅ Deployment completed successfully.'
        }
        failure {
            echo '❌ Deployment failed. Check logs for details.'
        }
    }
}
