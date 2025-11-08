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

        stage('Fetch Terraform Outputs') {
            steps {
                script {
                    try {
                        // Try reading JSON normally (if plugin available)
                        def outputs = readJSON file: "${TERRAFORM_DIR}/tf_outputs.json"
                        env.ALB_DNS = outputs.load_balancer_dns.value
                        env.S3_BUCKET_NAME = outputs.frontend_bucket_name.value
                        env.FRONTEND_WEBSITE = outputs.frontend_website_url.value
                    } catch (Exception e) {
                        // Fallback to PowerShell (if plugin not installed)
                        env.ALB_DNS = powershell(returnStdout: true, script: "terraform -chdir=${TERRAFORM_DIR} output -raw load_balancer_dns").trim()
                        env.S3_BUCKET_NAME = powershell(returnStdout: true, script: "terraform -chdir=${TERRAFORM_DIR} output -raw frontend_bucket_name").trim()
                        env.FRONTEND_WEBSITE = powershell(returnStdout: true, script: "terraform -chdir=${TERRAFORM_DIR} output -raw frontend_website_url").trim()
                    }

                    env.FRONTEND_URL = "http://${env.ALB_DNS}"

                    echo "--------------------------------------"
                    echo "Backend ALB DNS: ${env.ALB_DNS}"
                    echo "Frontend S3 Bucket Name: ${env.S3_BUCKET_NAME}"
                    echo "Frontend Website URL: ${env.FRONTEND_WEBSITE}"
                    echo "Frontend uses backend at: ${env.FRONTEND_URL}"
                    echo "--------------------------------------"
                }
            }
        }

        // ✅ Updated for Windows: No bash/WSL; uses Python instead
        stage('Update Frontend URL') {
            steps {
                script {
                    echo "🚀 Updating frontend URLs and deploying to S3..."
                    bat """
                    "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" update_frontend_and_deploy.py ${env.FRONTEND_URL} ${env.S3_BUCKET_NAME} .
                    """
                }
            }
        }

        stage('Build & Push Docker Images') {
            steps {
                script {
                    def images = ['Booking_Service', 'Flight_Service', 'Payment_Service', 'CrowdPulse']
                    for (img in images) {
                        bat """
                        echo Building and pushing ${img}...
                        docker build -t %ECR_REGISTRY%/${img.toLowerCase()}:latest ${img}
                        docker push %ECR_REGISTRY%/${img.toLowerCase()}:latest
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

        stage('Upload Frontend Files to S3') {
            steps {
                bat '''
                echo Uploading updated frontend assets to s3://%S3_BUCKET_NAME% ...
                aws s3 cp index.html s3://%S3_BUCKET_NAME%/index.html --content-type text/html
                aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/crowdpulse_widget.html --content-type text/html
                aws s3 cp images\\travelease_logo.png s3://%S3_BUCKET_NAME%/images/travelease_logo.png --content-type image/png
                '''
            }
        }

        stage('Populate Databases') {
            steps {
                bat '''
                echo Running Python data population scripts...
                "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" populate_smart_trips_db.py
                "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" Flight_Service\\populate_flights_db.py
                '''
            }
        }

        stage('TravelEase Deployment Complete') {
            steps {
                echo "--------------------------------------"
                echo "✅ TravelEase Deployment Complete!"
                echo "Backend ALB DNS: ${env.ALB_DNS}"
                echo "Frontend S3 Bucket Name: ${env.S3_BUCKET_NAME}"
                echo "Frontend Website URL: ${env.FRONTEND_WEBSITE}"
                echo "Frontend uses backend at: ${env.FRONTEND_URL}"
                echo "--------------------------------------"
            }
        }

        stage('Open Deployed Website') {
            steps {
                echo "🌐 Opening deployed TravelEase website..."
                bat """
                echo Launching frontend in browser...
                powershell -Command "Start-Process 'chrome.exe' 'http://${env.FRONTEND_WEBSITE}'"
                powershell -Command "Start-Sleep -Seconds 3"
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