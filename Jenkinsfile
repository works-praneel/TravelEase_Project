pipeline {
    agent any

    environment {
        AWS_REGION    = 'eu-north-1'
        ECR_REGISTRY  = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME  = 'TravelEaseCluster'
        TERRAFORM_DIR = 'terraform'
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {

        // 1. Checkout Code
        stage('1. Checkout SCM') {
            steps {
                checkout scm
            }
        }

        // 2. AWS & ECR Login
        stage('2. Login to AWS & ECR') {
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

        // 3. Infrastructure (Terraform)
        stage('3. Apply Infrastructure (Terraform)') {
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

        // 4. Fetch Terraform Outputs
        stage('4. Fetch Terraform Outputs') {
            steps {
                script {
                    echo "Reading outputs from tf_outputs.json..."

                    def outputs = readJSON file: "${TERRAFORM_DIR}/tf_outputs.json"

                    env.ALB_DNS      = outputs.load_balancer_dns.value
                    env.S3_BUCKET_NAME = outputs.frontend_bucket_name.value
                    env.FRONTEND_URL   = "http://${outputs.load_balancer_dns.value}"
                    env.FRONTEND_SITE  = outputs.frontend_website_url.value

                    echo "--------------------------------------"
                    echo " Backend ALB DNS: ${env.ALB_DNS}"
                    echo " Frontend S3 Bucket: ${env.S3_BUCKET_NAME}"
                    echo " Frontend Website: ${env.FRONTEND_SITE}"
                    echo "--------------------------------------"
                }
            }
        }

        // 5. Update Frontend URL and Deploy
        stage('5. Update Frontend URL and Deploy') {
            steps {
                script {
                    echo "Updating frontend URLs and deploying to S3..."
                    bat """
                        "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" update_frontend_and_deploy.py .
                    """
                }
            }
        }

        // 6. Build & Push Docker Images
        stage('6. Build & Push Docker Images') {
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
                            withCredentials([
                                usernamePassword(
                                    credentialsId: 'gmail-user',
                                    usernameVariable: 'EMAIL_USER',
                                    passwordVariable: 'EMAIL_PASS'
                                )
                            ]) {
                                bat """
                                    echo Building Booking Service with Gmail credentials...
                                    docker build --build-arg EMAIL_USER=%EMAIL_USER% --build-arg EMAIL_PASS=%EMAIL_PASS% -t %ECR_REGISTRY%/${repoName}:latest ${folder}
                                    docker push %ECR_REGISTRY%/${repoName}:latest
                                """
                            }
                        } else {
                            bat """
                                docker build -t %ECR_REGISTRY%/${repoName}:latest ${folder}
                                docker push %ECR_REGISTRY%/${repoName}:latest
                            """
                        }
                    }
                }
            }
        }

        // 7. Force ECS Redeployment
        stage('7. Force ECS Redeployment') {
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

        // 8. Inject Gmail Credentials into ECS Booking Service
        stage('8. Inject Gmail Credentials into ECS Booking Service') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'gmail-user',
                        usernameVariable: 'USR',
                        passwordVariable: 'PWD'
                    )
                ]) {
                    // FIX: PowerShell command is now on a single logical line
                    bat """
                        echo Fetching current task definition...

                        for /f "delims=" %%A in ('aws ecs describe-services ^
                            --cluster %CLUSTER_NAME% ^
                            --services booking-service ^
                            --query "services[0].taskDefinition" ^
                            --output text') do set TASK_DEF_ARN=%%A

                        echo Current Task Definition: %TASK_DEF_ARN%

                        aws ecs describe-task-definition ^
                            --task-definition %TASK_DEF_ARN% ^
                            --query "taskDefinition" > task_def.json

                        powershell -Command "\$json = Get-Content 'task_def.json' | ConvertFrom-Json; \$envList = @(); foreach (\$env in \$json.containerDefinitions[0].environment) { if (\$env.name -ne 'EMAIL_USER' -and \$env.name -ne 'EMAIL_PASS') { \$envList += \$env; } }; \$envList += @{ name='EMAIL_USER'; value='%USR%' }; \$envList += @{ name='EMAIL_PASS'; value='%PWD%' }; \$json.containerDefinitions[0].environment = \$envList; \$json | ConvertTo-Json -Depth 15 | Out-File 'new_task_def.json' -Encoding UTF8"
                        
                        aws ecs register-task-definition ^
                            --cli-input-json file://new_task_def.json ^
                            --region %AWS_REGION% > register_output.json

                        for /f "delims=" %%B in ('powershell -Command ^
                            "(Get-Content register_output.json | ConvertFrom-Json).taskDefinition.taskDefinitionArn"') do set NEW_TASK_DEF=%%B

                        aws ecs update-service ^
                            --cluster %CLUSTER_NAME% ^
                            --service booking-service ^
                            --task-definition %NEW_TASK_DEF% ^
                            --force-new-deployment ^
                            --region %AWS_REGION%
                    """
                }
            }
        }


        // 9. Inject YouTube API Key into ECS CrowdPulse Service
        stage('9. Inject YouTube API Key into ECS CrowdPulse Service') {
            steps {
                withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                    // FIX: PowerShell command is now on a single logical line
                    bat '''
                        for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services crowdpulse-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A

                        aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def_crowdpulse.json

                        powershell -Command "$json = Get-Content 'task_def_crowdpulse.json' | ConvertFrom-Json; $envList = @(); foreach ($env in $json.containerDefinitions[0].environment) { if ($env.name -ne 'YOUTUBE_API_KEY') { $envList += $env } }; $envList += @{ name='YOUTUBE_API_KEY'; value='%YOUTUBE_API_KEY%' }; $json.containerDefinitions[0].environment = $envList; $json | ConvertTo-Json -Depth 10 | Out-File new_task_def_crowdpulse.json -Encoding utf8"

                        aws ecs register-task-definition --cli-input-json file://new_task_def_crowdpulse.json > register_output_crowdpulse.json

                        for /f "delims=" %%B in ('powershell -Command ^
                            "(Get-Content register_output_crowdpulse.json | ConvertFrom-Json).taskDefinition.taskDefinitionArn"') do set NEW_TASK_DEF=%%B

                        aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --task-definition %NEW_TASK_DEF% --force-new-deployment --region %AWS_REGION%
                    '''
                }
            }
        }

        // 10. Verify Frontend Upload
        stage('10. Verify Frontend Upload') {
            steps {
                bat '''
                    echo Verifying uploaded frontend files...
                    aws s3 ls s3://%S3_BUCKET_NAME%/
                    echo Refreshing CrowdPulse widget...
                    aws s3 rm s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html
                    aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html --content-type text/html
                '''
            }
        }

        // 11. Deployment Summary
        stage('11. Deployment Summary') {
            steps {
                echo "--------------------------------------"
                echo "TravelEase Deployment Complete!"
                echo "--------------------------------------"
            }
        }

        // 12. Show Deployed Website URL
        stage('12. Show Deployed Website URL') {
            steps {
                echo "Deployed TravelEase Website: ${env.FRONTEND_SITE}"
            }
        }
    }
    
    // Conditional Cleanup Logic
    post {
        // Runs IMMEDIATELY if the pipeline fails at any stage
        failure {
            echo '🚨 Deployment failed. Starting IMMEDIATE infrastructure teardown (terraform destroy).'
            dir("${TERRAFORM_DIR}") {
                bat 'terraform destroy -auto-approve'
            }
        }
        
        // Runs only if the pipeline completes all stages successfully
        success {
            echo '✅ Deployment completed successfully. Waiting 15 minutes before starting infrastructure teardown.'
            
            // Wait for 15 minutes (900 seconds)
            sleep(time: 15, unit: 'MINUTES')
            
            echo '⏳ 15 minutes elapsed. Starting infrastructure teardown (terraform destroy).'
            dir("${TERRAFORM_DIR}") {
                bat 'terraform destroy -auto-approve'
            }
        }
    }
}