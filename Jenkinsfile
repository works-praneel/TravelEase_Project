pipeline {
    agent any

    environment {
        AWS_REGION      = 'eu-north-1'
        ECR_REGISTRY    = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME    = 'TravelEaseCluster'
        TERRAFORM_DIR   = 'terraform'
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
                    bat '''
                        aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                        aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                        aws configure set region %AWS_REGION%
                        aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    '''
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

        // 4. Fetch Terraform Outputs (Defensive check added in code)
        stage('4. Fetch Terraform Outputs') {
            steps {
                script {
                    echo "Reading outputs from tf_outputs.json..."

                    def outputs = readJSON file: "${TERRAFORM_DIR}/tf_outputs.json"

                    // Defensive Groovy helper function: prevents NullPointerException
                    def getOutputValue = { outputsObj, key ->
                        if (outputsObj."$key" && outputsObj."$key".value != null) {
                            return outputsObj."$key".value
                        } else {
                            error "❌ CRITICAL ERROR: Terraform output key '$key' not found in tf_outputs.json. Check 'terraform/outputs.tf' or Stage 3 failure."
                        }
                    }

                    // Assign environment variables using the safe helper
                    def albDns = getOutputValue(outputs, 'load_balancer_dns')
                    
                    env.ALB_DNS      = albDns
                    env.S3_BUCKET_NAME = getOutputValue(outputs, 'frontend_bucket_name')
                    env.FRONTEND_URL   = "http://${albDns}"
                    env.FRONTEND_SITE  = getOutputValue(outputs, 'frontend_website_url')

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
                    // Note: update_frontend_and_deploy.py must use env.ALB_DNS, etc.
                    bat '''
                        "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" update_frontend_and_deploy.py .
                    '''
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
                                // Uses BAT interpolation for EMAIL_USER/PASS and Groovy interpolation for the rest
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
        stage('7. Force ECS Redeployment (Pre-Injection)') {
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
        
        // // --- Inject Gmail Credentials (Stage 8) ---
        stage('8. Inject Gmail Credentials (Booking Service)') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'gmail-user', usernameVariable: 'USR', passwordVariable: 'PWD')
                ]) {
                    script {
                        def new_task_def_arn = ''
                        
                        // Part 1: Fetch current task ARN and download JSON
                        bat """
                            for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services booking-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A
                            aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def.json
                        """
                        
                        // Part 2: Modify JSON (PowerShell is robustly executed here)
                        powershell """
                            \$td = Get-Content 'task_def.json' | ConvertFrom-Json;
                            
                            // CRITICAL FIX: Filter out old credentials using \$\_.name
                            \$td.containerDefinitions[0].environment = @(\$td.containerDefinitions[0].environment | Where-Object { \$\_.name -ne 'EMAIL_USER' -and \$\_.name -ne 'EMAIL_PASS' });
                            
                            // Add new credentials (Jenkins variables are injected using Groovy's \${variable} syntax)
                            \$td.containerDefinitions[0].environment += @{ name='EMAIL_USER'; value='${USR}' };
                            \$td.containerDefinitions[0].environment += @{ name='EMAIL_PASS'; value='${PWD}' };
                            
                            // Reconstruct and save JSON
                            \$new_td = @{ 
                                containerDefinitions = \$td.containerDefinitions; family = \$td.family; networkMode = \$td.networkMode; requiresCompatibilities = \$td.requiresCompatibilities; cpu = \$td.cpu; memory = \$td.memory 
                            };
                            if (\$td.taskRoleArn) { \$new_td.taskRoleArn = \$td.taskRoleArn };
                            if (\$td.executionRoleArn) { \$new_td.executionRoleArn = \$td.executionRoleArn };
                            \$new_td | ConvertTo-Json -Depth 15 | Out-File 'new_task_def.json' -Encoding UTF8
                        """
                        
                        // Part 3: Register new Task Definition and check output
                        bat """
                            aws ecs register-task-definition --cli-input-json file://new_task_def.json --region %AWS_REGION% > register_output.json
                        """

                        // Part 4: Read ARN and Update Service (Groovy logic)
                        try {
                            new_task_def_arn = powershell(script: "(Get-Content 'register_output.json' | ConvertFrom-Json).taskDefinition.taskDefinitionArn", returnStdout: true, timeout: 10).trim()
                        } catch (e) {
                            echo "Warning: Could not read new Task Definition ARN. Registration likely failed."
                        }

                        if (new_task_def_arn) {
                            echo "Successfully registered new Task Definition: ${new_task_def_arn}"
                            // Update the service with the new ARN
                            bat """
                                aws ecs update-service --cluster %CLUSTER_NAME% --service booking-service --task-definition ${new_task_def_arn} --force-new-deployment --region %AWS_REGION%
                            """
                        } else {
                            error("Failed to register new Task Definition. Check 'register_output.json' for the exact reason.")
                        }
                    }
                }
            }
        }


        // // --- Inject YouTube API Key (Stage 9) ---
        stage('9. Inject YouTube API Key (CrowdPulse Service)') {
            steps {
                withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                    script {
                        def new_task_def_arn = ''
                        
                        // Part 1: Fetch current task ARN and download JSON
                        bat '''
                            for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services crowdpulse-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A
                            aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def_crowdpulse.json
                        '''
                        
                        // Part 2: Modify JSON (PowerShell is robustly executed here)
                        powershell """
                            \$td = Get-Content 'task_def_crowdpulse.json' | ConvertFrom-Json;
                            
                            // FIX: Filter out old API key using the correct PowerShell pipeline variable \$\_.name
                            \$td.containerDefinitions[0].environment = @(\$td.containerDefinitions[0].environment | Where-Object { \$\_.name -ne 'YOUTUBE_API_KEY' });
                            
                            // Add new credential using Groovy interpolation
                            \$td.containerDefinitions[0].environment += @{ name='YOUTUBE_API_KEY'; value='${YOUTUBE_API_KEY}' };
                            
                            // Reconstruct and save JSON
                            \$new_td = @{ 
                                containerDefinitions = \$td.containerDefinitions; family = \$td.family; networkMode = \$td.networkMode; requiresCompatibilities = \$td.requiresCompatibilities; cpu = \$td.cpu; memory = \$td.memory 
                            };
                            if (\$td.taskRoleArn) { \$new_td.taskRoleArn = \$td.taskRoleArn };
                            if (\$td.executionRoleArn) { \$new_td.executionRoleArn = \$td.executionRoleArn };
                            \$new_td | ConvertTo-Json -Depth 10 | Out-File 'new_task_def_crowdpulse.json' -Encoding UTF8
                        """
                        
                        // Part 3: Register new Task Definition and check output
                        bat """
                            aws ecs register-task-definition --cli-input-json file://new_task_def_crowdpulse.json --region %AWS_REGION% > register_output_crowdpulse.json
                        """

                        // Part 4: Read ARN and Update Service (Groovy logic)
                        try {
                            new_task_def_arn = powershell(script: "(Get-Content 'register_output_crowdpulse.json' | ConvertFrom-Json).taskDefinition.taskDefinitionArn", returnStdout: true, timeout: 10).trim()
                        } catch (e) {
                            echo "Warning: Could not read new Task Definition ARN for CrowdPulse. Registration likely failed."
                        }

                        if (new_task_def_arn) {
                            echo "Successfully registered new CrowdPulse Task Definition: ${new_task_def_arn}"
                            // Update the service with the new ARN
                            bat """
                                aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --task-definition ${new_task_def_arn} --force-new-deployment --region %AWS_REGION%
                            """
                        } else {
                            error("Failed to register new CrowdPulse Task Definition. Check 'register_output_crowdpulse.json' for the exact reason.")
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
                bat 'terraform destroy -auto-approve || true' // Added || true for resilience
            }
        }
        
        // Runs only if the pipeline completes all stages successfully
        success {
            echo '✅ Deployment completed successfully. Waiting 15 minutes before starting infrastructure teardown.'
            
            // Wait for 15 minutes (900 seconds)
            script {
                sleep(time: 15, unit: 'MINUTES')
            }
            
            echo '⏳ 15 minutes elapsed. Starting infrastructure teardown (terraform destroy).'
            dir("${TERRAFORM_DIR}") {
                bat 'terraform destroy -auto-approve'
            }
        }
    }
}