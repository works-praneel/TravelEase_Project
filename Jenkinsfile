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

        // ... (Stages 1 through 7 remain unchanged) ...

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

                            :: FIX 1: Aggressive PowerShell JSON cleanup: Only select required fields and inject secrets.
                            powershell -Command "\$td = Get-Content 'task_def.json' | ConvertFrom-Json; \$td.containerDefinitions[0].environment = @(\$td.containerDefinitions[0].environment | Where-Object {\$.name -ne 'EMAIL_USER' -and \$.name -ne 'EMAIL_PASS'}); \$td.containerDefinitions[0].environment += @{ name='EMAIL_USER'; value='%USR%' }; \$td.containerDefinitions[0].environment += @{ name='EMAIL_PASS'; value='%PWD%' }; \$new_td = @{ containerDefinitions = \$td.containerDefinitions; family = \$td.family; networkMode = \$td.networkMode; requiresCompatibilities = \$td.requiresCompatibilities; cpu = \$td.cpu; memory = \$td.memory }; if (\$td.taskRoleArn) { \$new_td.taskRoleArn = \$td.taskRoleArn }; if (\$td.executionRoleArn) { \$new_td.executionRoleArn = \$td.executionRoleArn }; \$new_td | ConvertTo-Json -Depth 15 | Out-File 'new_task_def.json' -Encoding UTF8"
                            
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
                        // This handles the environment variable capture outside of the volatile 'bat' block.
                        try {
                            new_task_def_arn = powershell(
                                script: "(Get-Content 'register_output.json' | ConvertFrom-Json).taskDefinition.taskDefinitionArn",
                                returnStdout: true,
                                // Add a timeout, sometimes AWS output file is empty
                                timeout: 10
                            ).trim()
                        } catch (e) {
                            echo "Warning: Could not read new Task Definition ARN. It's likely the registration failed."
                            // Keep the ARN empty to trigger the check below
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


        // 9. Inject YouTube API Key into ECS CrowdPulse Service
        stage('9. Inject YouTube API Key into ECS CrowdPulse Service') {
            steps {
                withCredentials([string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY')]) {
                    script {
                        def new_task_def_arn = ''
                        
                        // Part 1: Fetch, Modify, and Register Task Definition
                        bat '''
                            for /f "delims=" %%A in ('aws ecs describe-services --cluster %CLUSTER_NAME% --services crowdpulse-service --query "services[0].taskDefinition" --output text') do set TASK_DEF_ARN=%%A

                            aws ecs describe-task-definition --task-definition %TASK_DEF_ARN% --query "taskDefinition" > task_def_crowdpulse.json

                            :: FIX 1: Aggressive PowerShell JSON cleanup: Only select required fields and inject secrets.
                            powershell -Command "$td = Get-Content 'task_def_crowdpulse.json' | ConvertFrom-Json; $td.containerDefinitions[0].environment = @($td.containerDefinitions[0].environment | Where-Object {$_.name -ne 'YOUTUBE_API_KEY'}); $td.containerDefinitions[0].environment += @{ name='YOUTUBE_API_KEY'; value='%YOUTUBE_API_KEY%' }; $new_td = @{ containerDefinitions = $td.containerDefinitions; family = $td.family; networkMode = $td.networkMode; requiresCompatibilities = $td.requiresCompatibilities; cpu = $td.cpu; memory = $td.memory }; if ($td.taskRoleArn) { $new_td.taskRoleArn = $td.taskRoleArn }; if ($td.executionRoleArn) { $new_td.executionRoleArn = $td.executionRoleArn }; $new_td | ConvertTo-Json -Depth 10 | Out-File 'new_task_def_crowdpulse.json' -Encoding UTF8"

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
                                script: "(Get-Content 'register_output_crowdpulse.json' | ConvertFrom-Json).taskDefinition.taskDefinitionArn",
                                returnStdout: true,
                                timeout: 10
                            ).trim()
                        } catch (e) {
                            echo "Warning: Could not read new Task Definition ARN. It's likely the registration failed."
                            // Keep the ARN empty to trigger the check below
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