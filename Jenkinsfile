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
        // 7. Build & Push Docker Images (with Gmail + YouTube keys)
        // -----------------------------
        stage('Build & Push Docker Images') {
            steps {
                script {
                    def services = [
                        'booking-service'   : 'Booking_Service',
                        'flight-service'    : 'Flight_Service',
                        'payment-service'   : 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse\\backend'
                    ]

                    services.each { repoName, folder ->
                        echo "Building and pushing image for ${repoName}..."

                        if (repoName == 'booking-service') {
                            // Gmail credentials for Booking Service
                            withCredentials([
                                usernamePassword(
                                    credentialsId: 'gmail-user',
                                    usernameVariable: 'EMAIL_USER',
                                    passwordVariable: 'EMAIL_PASS'
                                )
                            ]) {
                                bat """
                                echo Building Booking Service with Gmail credentials...
                                docker build ^
                                    --build-arg EMAIL_USER=%EMAIL_USER% ^
                                    --build-arg EMAIL_PASS=%EMAIL_PASS% ^
                                    -t %ECR_REGISTRY%/${repoName}:latest ${folder}
                                docker push %ECR_REGISTRY%/${repoName}:latest
                                """
                            }
                        }

                        else if (repoName == 'crowdpulse-service') {
                            // YouTube API Key for live vlog support
                            withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                                bat """
                                echo Building CrowdPulse service with live YouTube integration...
                                docker build ^
                                    --build-arg YOUTUBE_API_KEY=%YOUTUBE_API_KEY% ^
                                    -t %ECR_REGISTRY%/${repoName}:latest ${folder}
                                docker push %ECR_REGISTRY%/${repoName}:latest
                                """
                            }
                        }

                        else {
                            bat """
                            docker build -t %ECR_REGISTRY%/${repoName}:latest ${folder}
                            docker push %ECR_REGISTRY%/${repoName}:latest
                            """
                        }
                    }
                }
            }
        }

        // -----------------------------
        // 8. Force ECS Redeployment
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
        // 8.1 Inject Gmail Credentials into ECS Booking Service
        // -----------------------------
        stage('Inject Gmail Credentials into ECS Booking Service') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'gmail-user',
                        usernameVariable: 'EMAIL_USER',
                        passwordVariable: 'EMAIL_PASS'
                    )
                ]) {
                    echo "🔐 Updating ECS Task Definition for Booking Service with Gmail credentials..."

                    bat '''
                    echo Fetching current Booking Service task definition...
                    for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services booking-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A
                    echo Found Task Definition: %TASK_DEF_ARN%

                    echo Exporting current task definition...
                    aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def.json

                    echo Injecting Gmail credentials...
                    powershell -Command "$json = Get-Content task_def.json | ConvertFrom-Json; $json.containerDefinitions[0].environment += @(@{name='EMAIL_USER'; value='%EMAIL_USER%'}, @{name='EMAIL_PASS'; value='%EMAIL_PASS%'}); $json | ConvertTo-Json -Depth 10 | Out-File new_task_def.json -Encoding utf8"

                    echo Registering new ECS task definition revision...
                    aws ecs register-task-definition --cli-input-json file://new_task_def.json > register_output.json

                    echo Forcing ECS redeployment with updated credentials...
                    for /f "delims=" %%B in ('aws ecs update-service --cluster %CLUSTER_NAME% --service booking-service --force-new-deployment --region %AWS_REGION% --query "service.taskDefinition" --output text') do echo Updated Task Definition: %%B
                    '''
                }
            }
        }

        // -----------------------------
        // 8.2 Inject YouTube API Key into ECS CrowdPulse Service
        // -----------------------------
        stage('Inject YouTube API Key into ECS CrowdPulse Service') {
            steps {
                withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                    echo "🎥 Updating ECS Task Definition for CrowdPulse with YouTube API Key..."

                    bat '''
                    echo Fetching current CrowdPulse task definition...
                    for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services crowdpulse-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A
                    echo Found Task Definition: %TASK_DEF_ARN%

                    echo Exporting current task definition...
                    aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def_crowdpulse.json

                    echo Injecting YouTube API Key...
                    powershell -Command "$json = Get-Content task_def_crowdpulse.json | ConvertFrom-Json; $json.containerDefinitions[0].environment += @(@{name='YOUTUBE_API_KEY'; value='%YOUTUBE_API_KEY%'}); $json | ConvertTo-Json -Depth 10 | Out-File new_task_def_crowdpulse.json -Encoding utf8"

                    echo Registering new ECS task definition revision...
                    aws ecs register-task-definition --cli-input-json file://new_task_def_crowdpulse.json > register_output_crowdpulse.json

                    echo Forcing ECS redeployment with updated YouTube key...
                    for /f "delims=" %%B in ('aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --force-new-deployment --region %AWS_REGION% --query "service.taskDefinition" --output text') do echo Updated Task Definition: %%B
                    '''
                }
            }
        }

        // -----------------------------
        // 9. Verify Frontend Upload
        // -----------------------------
        stage('Verify Frontend Upload') {
            steps {
                bat '''
                echo ✅ Verifying uploaded frontend files in S3...
                aws s3 ls s3://%S3_BUCKET_NAME%/
                echo ♻️ Clearing CrowdPulse cache...
                aws s3 rm s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html
                aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html --content-type text/html
                '''
            }
        }

        // -----------------------------
        // 10. Deployment Summary
        // -----------------------------
        stage('Deployment Summary') {
            steps {
                echo "--------------------------------------"
                echo "✅ TravelEase Deployment Complete!"
                echo "All backend services (Booking Email + CrowdPulse YouTube) are live and configured."
                echo "--------------------------------------"
            }
        }

        // -----------------------------
        // 11. Show Deployed Website URL
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
