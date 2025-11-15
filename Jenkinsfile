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

        // 8. Inject Gmail Credentials into ECS Booking Service (Fixed: Removed internal comments)
        stage('8. Inject Gmail Credentials into ECS Booking Service') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'gmail-user',
                        usernameVariable: 'USR',
                        passwordVariable: 'PWD'
                    )
                ]) {
                    script {
                        def new_task_def_arn = ''
                        
                        // Part 1: Fetch, Modify, and Register Task Definition (using bat for multiple AWS calls)
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

                            powershell -Command "\$td = Get-Content 'task_def.json' | ConvertFrom-Json; \$td.containerDefinitions[0].environment = @(\$td.containerDefinitions[0].environment | Where-Object {$$.name -ne 'EMAIL_USER' -and $$.name -ne 'EMAIL_PASS'}); \$td.containerDefinitions[0].environment += @{ name='EMAIL_USER'; value='%USR%' }; \$td.containerDefinitions[0].environment += @{ name='EMAIL_PASS'; value='%PWD%' }; \$new_td = @{ containerDefinitions = \$td.containerDefinitions; family = \$td.family; networkMode = \$td.networkMode; requiresCompatibilities = \$td.requiresCompatibilities; cpu = \$td.cpu; memory = \$td.memory }; if (\$td.taskRoleArn) { \$new_td.taskRoleArn = \$td.taskRoleArn }; if (\$td.executionRoleArn) { \$new_td.executionRoleArn = \$td.executionRoleArn }; \$new_td | ConvertTo-Json -Depth 15 | Out-File 'new_task_def.json' -Encoding UTF8"
                            
                            echo DEBUG: FILE CONTENT (new_task_def.json):
                            type new_task_def.json
                            echo --------------------------------------

                            aws ecs register-task-definition ^
                                --cli-input-json file://new_task_def.json ^
                                --region %AWS_REGION% > register_output.json
                            
                            echo DEBUG: AWS ERROR OUTPUT (register_output.json):
                            type register_output.json
                            echo --------------------------------------
                        """

                        // Part 2: Read ARN using robust Groovy/PowerShell
                        try {
                            new_task_def_arn = powershell(
                                script: "(Get-Content 'register_output.json' | ConvertFrom-Json).taskDefinition.taskDefinitionArn",
                                returnStdout: true,
                                timeout: 10
                            ).trim()
                        } catch (e) {
                            echo "Warning: Could not read new Task Definition ARN. It's likely the registration failed."
                        }

                        // Part 3: Update Service
                        if (new_task_def_arn) {
                            echo "Successfully registered new Task Definition: ${new_task_def_arn}"
                            bat """
                                aws ecs update-service ^
                                    --cluster %CLUSTER_NAME% ^
                                    --service booking-service ^
                                    --task-definition ${new_task_def_arn} ^
                                    --force-new-deployment ^
                                    --region %AWS_REGION%
                            """
                        } else {
                            error("Failed to register new Task Definition. Check the 'DEBUG: AWS ERROR OUTPUT' for the exact reason.")
                        }
                    }
                }
            }
        }


        // 9. Inject YouTube API Key into ECS CrowdPulse Service (Fixed: Removed internal comments)
        stage('9. Inject YouTube API Key into ECS CrowdPulse Service') {
            steps {
                withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                    script {
                        def new_task_def_arn = ''
                        
                        // Part 1: Fetch, Modify, and Register Task Definition
                        bat '''
                            for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services crowdpulse-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A

                            aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def_crowdpulse.json

                            powershell -Command "\$td = Get-Content 'task_def_crowdpulse.json' | ConvertFrom-Json; \$td.containerDefinitions[0].environment = @(\$td.containerDefinitions[0].environment | Where-Object {$$_.name -ne 'YOUTUBE_API_KEY'}); \$td.containerDefinitions[0].environment += @{ name='YOUTUBE_API_KEY'; value='%YOUTUBE_API_KEY%' }; \$new_td = @{ containerDefinitions = \$td.containerDefinitions; family = \$td.family; networkMode = \$td.networkMode; requiresCompatibilities = \$td.requiresCompatibilities; cpu = \$td.cpu; memory = \$td.memory }; if (\$td.taskRoleArn) { \$new_td.taskRoleArn = \$td.taskRoleArn }; if (\$td.executionRoleArn) { \$new_td.executionRoleArn = \$td.executionRoleArn }; \$new_td | ConvertTo-Json -Depth 10 | Out-File 'new_task_def_crowdpulse.json' -Encoding UTF8"

                            echo DEBUG: FILE CONTENT (new_task_def_crowdpulse.json):
                            type new_task_def_crowdpulse.json
                            echo --------------------------------------

                            aws ecs register-task-definition --cli-input-json file://new_task_def_crowdpulse.json > register_output_crowdpulse.json

                            echo DEBUG: AWS ERROR OUTPUT (register_output_crowdpulse.json):
                            type register_output_crowdpulse.json
                            echo --------------------------------------
                        '''
                        
                        // Part 2: Read ARN using robust Groovy/PowerShell
                        try {
                             new_task_def_arn = powershell(
                                script: "(Get-Content 'register_output.json' | ConvertFrom-Json).taskDefinition.taskDefinitionArn",
                                returnStdout: true,
                                timeout: 10
                            ).trim()
                        } catch (e) {
                            echo "Warning: Could not read new Task Definition ARN. It's likely the registration failed."
                        }
                        
                        // Part 3: Update Service
                        if (new_task_def_arn) {
                            echo "Successfully registered new Task Definition: ${new_task_def_arn}"
                            bat """
                                aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --task-definition ${new_task_def_arn} --force-new-deployment --region %AWS_REGION%
                            """
                        } else {
                            error("Failed to register new Task Definition. Check the 'DEBUG: AWS ERROR OUTPUT' for the exact reason.")
                        }
                    }
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
    
    // Conditional Cleanup Logic: Immediate destroy on failure, 15 min delay on success.
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