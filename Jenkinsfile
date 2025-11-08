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
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-jenkins-creds'
        ]]) {
            bat '''
            set AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID%
            set AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY%
            set AWS_DEFAULT_REGION=%AWS_REGION%
            aws sts get-caller-identity
            for /f "delims=" %%a in ('aws ecr get-login-password --region %AWS_REGION%') do docker login --username AWS --password %%a %ECR_REGISTRY%
            '''
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
                    def outputs = readJSON file: "${TERRAFORM_DIR}/tf_outputs.json"

                    env.ALB_DNS = outputs.load_balancer_dns.value
                    env.S3_BUCKET_NAME = outputs.frontend_bucket_name.value
                    env.FRONTEND_WEBSITE = outputs.frontend_website_url.value
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

        stage('Update Frontend URL') {
            steps {
                bat '''
                echo Updating ALB URL in index.html using update_frontend_url.sh...
                bash update_frontend_url.sh index.html %FRONTEND_URL%
                '''
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
                python populate_smart_trips_db.py
                python Flight_Service\\populate_flights_db.py
                '''
            }
        }

        stage('TravelEase Deployment Complete') {
            steps {
                echo "--------------------------------------"
                echo "TravelEase Deployment Complete!"
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
                powershell -Command "Start-Process 'chrome.exe' '${env.FRONTEND_URL}'"
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
