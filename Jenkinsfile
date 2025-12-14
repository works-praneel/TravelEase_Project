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

        // --------------------------------------------------
        // 1. Checkout Code
        // --------------------------------------------------
        stage('1. Checkout SCM') {
            steps {
                checkout scm
            }
        }

        // --------------------------------------------------
        // 2. AWS & ECR Login
        // --------------------------------------------------
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
                        aws ecr get-login-password --region %AWS_REGION% ^
                        | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    '''
                }
            }
        }

        // --------------------------------------------------
        // 3. Apply Infrastructure (Terraform)
        // --------------------------------------------------
        stage('3. Apply Infrastructure (Terraform)') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'gmail-user',
                        usernameVariable: 'GMAIL_USER',
                        passwordVariable: 'GMAIL_PASS'
                    ),
                    string(
                        credentialsId: 'youtube-api-key',
                        variable: 'YOUTUBE_KEY'
                    )
                ]) {
                    dir("${TERRAFORM_DIR}") {
                        bat '''
                            echo Setting Terraform variables...

                            set TF_VAR_email_user=%GMAIL_USER%
                            set TF_VAR_email_pass=%GMAIL_PASS%
                            set TF_VAR_youtube_api_key=%YOUTUBE_KEY%

                            terraform init -input=false
                            terraform apply -auto-approve -input=false

                            terraform output -json > tf_outputs.json
                        '''
                    }
                }
            }
        }

        // --------------------------------------------------
        // 4. Fetch Terraform Outputs (SAFE)
        // --------------------------------------------------
        stage('4. Fetch Terraform Outputs') {
            steps {
                dir("${TERRAFORM_DIR}") {
                    script {
                        if (!fileExists('tf_outputs.json')) {
                            error "tf_outputs.json not found. Terraform apply did not complete."
                        }

                        def outputs = readJSON file: 'tf_outputs.json'

                        if (!outputs?.load_balancer_dns?.value) {
                            error "Terraform output 'load_balancer_dns' is missing or null."
                        }

                        env.ALB_DNS        = outputs.load_balancer_dns.value
                        env.S3_BUCKET_NAME = outputs.frontend_bucket_name?.value
                        env.FRONTEND_SITE  = outputs.frontend_website_url?.value

                        echo "--------------------------------------"
                        echo " ALB DNS        : ${env.ALB_DNS}"
                        echo " S3 Bucket      : ${env.S3_BUCKET_NAME}"
                        echo " Frontend Site  : ${env.FRONTEND_SITE}"
                        echo "--------------------------------------"
                    }
                }
            }
        }

        // --------------------------------------------------
        // 5. Update Frontend & Deploy to S3
        // --------------------------------------------------
        stage('5. Update Frontend URL and Deploy') {
            steps {
                bat '''
                    "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" ^
                    update_frontend_and_deploy.py .
                '''
            }
        }

        // --------------------------------------------------
        // 6. Build & Push Docker Images
        // --------------------------------------------------
        stage('6. Build & Push Docker Images') {
            steps {
                script {
                    def services = [
                        'booking-service'   : 'Booking_Service',
                        'flight-service'    : 'Flight_Service',
                        'payment-service'   : 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse\\backend'
                    ]

                    services.each { repo, folder ->
                        echo "Building and pushing ${repo}"
                        bat """
                            docker build -t %ECR_REGISTRY%/${repo}:latest ${folder}
                            docker push %ECR_REGISTRY%/${repo}:latest
                        """
                    }
                }
            }
        }

        // --------------------------------------------------
        // 7. Force ECS Redeployment
        // --------------------------------------------------
        stage('7. Force ECS Redeployment') {
            steps {
                bat '''
                    echo Redeploying ECS services...

                    aws ecs update-service --cluster %CLUSTER_NAME% --service booking-service    --force-new-deployment --region %AWS_REGION%
                    aws ecs update-service --cluster %CLUSTER_NAME% --service flight-service     --force-new-deployment --region %AWS_REGION%
                    aws ecs update-service --cluster %CLUSTER_NAME% --service payment-service    --force-new-deployment --region %AWS_REGION%
                    aws ecs update-service --cluster %CLUSTER_NAME% --service crowdpulse-service --force-new-deployment --region %AWS_REGION%
                '''
            }
        }

        // --------------------------------------------------
        // 8. Verify Frontend Upload
        // --------------------------------------------------
        stage('8. Verify Frontend Upload') {
            steps {
                bat '''
                    aws s3 ls s3://%S3_BUCKET_NAME%/
                    aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html ^
                    s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html ^
                    --content-type text/html
                '''
            }
        }

        // --------------------------------------------------
        // 9. Deployment Summary
        // --------------------------------------------------
        stage('9. Deployment Summary') {
            steps {
                echo "--------------------------------------"
                echo " TravelEase Deployment Complete!"
                echo " Website: ${env.FRONTEND_SITE}"
                echo "--------------------------------------"
            }
        }
    }

    // --------------------------------------------------
    // Post Actions (NO DESTROY)
    // --------------------------------------------------
    post {
        failure {
            echo 'Deployment failed. Infrastructure retained for debugging.'
        }
        success {
            echo 'Deployment successful. Infrastructure retained.'
        }
    }
}
