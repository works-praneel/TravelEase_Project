pipeline {
    agent any

    environment {
        AWS_REGION     = 'eu-north-1'
        ECR_REGISTRY   = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME   = 'TravelEaseCluster'
        TERRAFORM_DIR  = 'terraform'
    }

    triggers {
        pollSCM('H/2 * * * *') // Poll every 2 minutes
    }

    stages {

        // -----------------------------
        // 1. Checkout Code
        // -----------------------------
        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        // -----------------------------
        // 2. AWS & ECR Login
        // -----------------------------
        stage('Login to AWS & ECR') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'BNmnx0bIy24ahJTSUi6MIEpYUVmCTV8dyMBfH6cq',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    bat """
                    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                    aws configure set region %AWS_REGION%
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    """
                }
            }
        }

        // -----------------------------
        // 3. Infrastructure (Terraform)
        // -----------------------------
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

        // -----------------------------
        // 4. Fetch Terraform Outputs
        // -----------------------------
        stage('Fetch Terraform Outputs') {
            steps {
                script {
                    try {
                        def outputs = readJSON file: "${TERRAFORM_DIR}/tf_outputs.json"
                        env.ALB_DNS        = outputs.load_balancer_dns.value
                        env.S3_BUCKET_NAME = outputs.frontend_bucket_name.value
                        env.FRONTEND_URL   = "http://${outputs.load_balancer_dns.value}"
                        env.FRONTEND_SITE  = outputs.frontend_website_url.value
                    } catch (Exception e) {
                        env.ALB_DNS        = powershell(returnStdout: true, script: "terraform -chdir=${TERRAFORM_DIR} output -raw load_balancer_dns").trim()
                        env.S3_BUCKET_NAME = powershell(returnStdout: true, script: "terraform -chdir=${TERRAFORM_DIR} output -raw frontend_bucket_name").trim()
                        env.FRONTEND_SITE  = powershell(returnStdout: true, script: "terraform -chdir=${TERRAFORM_DIR} output -raw frontend_website_url").trim()
                        env.FRONTEND_URL   = "http://${env.ALB_DNS}"
                    }

                    echo "--------------------------------------"
                    echo " Backend ALB DNS: ${env.ALB_DNS}"
                    echo " Frontend S3 Bucket: ${env.S3_BUCKET_NAME}"
                    echo " Frontend Website: ${env.FRONTEND_SITE}"
                    echo "--------------------------------------"
                }
            }
        }

        // -----------------------------
        // 5. Inject YouTube API Key
        // -----------------------------
        stage('Inject YouTube API Key') {
            steps {
                withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                    bat '''
                    echo Injecting YouTube API Key into build environment...
                    setx YOUTUBE_API_KEY "%YOUTUBE_API_KEY%"
                    '''
                }
            }
        }

        // -----------------------------
        // 6. Update Frontend & Deploy
        // -----------------------------
        stage('Update Frontend URL and Deploy') {
            steps {
                script {
                    echo "🚀 Updating frontend URLs and deploying to S3..."
                    bat """
                    "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" update_frontend_and_deploy.py .
                    """
                }
            }
        }

        // -----------------------------
        // 7. Build & Push Docker Images
        // -----------------------------
        stage('Build & Push Docker Images') {
            steps {
                script {
                    def services = [
                        'booking-service'   : 'Booking_Service',
                        'flight-service'    : 'Flight_Service',
                        'payment-service'   : 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse/backend'
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

        // -----------------------------
        // 8. Rebuild CrowdPulse (YouTube Enabled)
        // -----------------------------
        stage('Rebuild CrowdPulse Service (YouTube Enabled)') {
            steps {
                echo "🔄 Building and pushing updated CrowdPulse service with live YouTube + fallback support..."
                bat """
                docker build --build-arg YOUTUBE_API_KEY=%YOUTUBE_API_KEY% -t %ECR_REGISTRY%/crowdpulse-service:latest CrowdPulse/backend
                docker push %ECR_REGISTRY%/crowdpulse-service:latest
                """
            }
        }

        // -----------------------------
        // 9. Force ECS Redeployment
        // -----------------------------
        stage('Force ECS Redeployment') {
            steps {
                bat '''
                echo Redeploying ECS Services...
                aws ecs update-service --cluster %CLUSTER_NAME% --service booking-service   --force-new-deployment --region %AWS_REGION%
                aws ecs update-service --cluster %CLUSTER_NAME% --service flight-service    --force-new-deployment --region %AWS_REGION%
                aws ecs update-service --cluster %CLUSTER_NAME% --service payment-service   --force-new-deployment --region %AWS_REGION%
                aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --force-new-deployment --region %AWS_REGION%
                '''
            }
        }

        // -----------------------------
        // 10. Verify Frontend Upload
        // -----------------------------
        stage('Verify Frontend Upload') {
            steps {
                bat '''
                echo ✅ Verifying uploaded frontend files in S3...
                aws s3 ls s3://%S3_BUCKET_NAME%/
                '''
            }
        }

        // -----------------------------
        // 11. Deployment Summary
        // -----------------------------
        stage('Deployment Summary') {
            steps {
                echo "--------------------------------------"
                echo "✅ TravelEase Deployment Complete!"
                echo "All backend services, including CrowdPulse, are live with fallback-enabled vlogs."
                echo "--------------------------------------"
            }
        }

        // -----------------------------
        // 12. Show Deployed Website URL
        // -----------------------------
        stage('Show Deployed Website URL') {
            steps {
                echo "🌐 Deployed TravelEase Website:"
                bat 'powershell -Command "(Get-Content .\\terraform\\tf_outputs.json | ConvertFrom-Json | Select-Object -ExpandProperty frontend_website_url | Select-Object -ExpandProperty value)"'
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
