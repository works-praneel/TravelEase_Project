pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        TERRAFORM_DIR = 'terraform'
    }

    triggers {
        pollSCM('H/2 * * * *') // every 2 minutes
    }

    stages {

        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Login to AWS & ECR') {
            steps {
                withAWS(region: "${AWS_REGION}", credentials: 'aws-jenkins-creds') {
                    bat '''
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
                    '''
                }
            }
        }

        stage('Fetch Terraform Outputs') {
            steps {
                script {
                    def outputFile = "${TERRAFORM_DIR}/tf_outputs.json"
                    // If missing, regenerate automatically
                    if (!fileExists(outputFile)) {
                        echo "tf_outputs.json not found. Regenerating..."
                        bat "cd ${TERRAFORM_DIR} && terraform output -json > tf_outputs.json"
                    }

                    // Read outputs
                    def outputs = readJSON file: outputFile
                    env.S3_BUCKET_NAME = outputs.frontend_bucket_name?.value
                    env.WEBSITE_URL = outputs.frontend_website_url?.value
                    env.ALB_DNS = outputs.load_balancer_dns?.value
                    env.FRONTEND_URL = "http://${env.ALB_DNS}"

                    // Validate
                    if (!env.S3_BUCKET_NAME || !env.ALB_DNS) {
                        error("""
                        Terraform outputs missing or invalid.
                        Captured:
                          ALB_DNS = ${env.ALB_DNS}
                          S3_BUCKET_NAME = ${env.S3_BUCKET_NAME}
                          FRONTEND_URL = ${env.FRONTEND_URL}
                        Ensure outputs.tf has:
                         • load_balancer_dns
                         • frontend_bucket_name
                         • frontend_website_url
                        """)
                    }

                    echo "Terraform Outputs:"
                    echo "  S3_BUCKET_NAME: ${env.S3_BUCKET_NAME}"
                    echo "  WEBSITE_URL: ${env.WEBSITE_URL}"
                    echo "  ALB_DNS: ${env.ALB_DNS}"
                }
            }
        }

        stage('Update Frontend URLs in index.html') {
            steps {
                bat '''
                echo Updating ALB URL in index.html...
                powershell -Command "(Get-Content index.html) -replace 'http://travelease-project-ALB-[^"]+', '%FRONTEND_URL%' | Set-Content index.html"
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
                echo Uploading frontend assets to S3 bucket: %S3_BUCKET_NAME% ...
                aws s3 cp index.html s3://%S3_BUCKET_NAME%/index.html
                aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/crowdpulse_widget.html
                aws s3 cp images\\travelease_logo.png s3://%S3_BUCKET_NAME%/images/travelease_logo.png
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

        stage('Display Final URL') {
            steps {
                echo "✅ Application deployed successfully."
                echo "Frontend Bucket: ${env.S3_BUCKET_NAME}"
                echo "Website URL: ${env.WEBSITE_URL}"
                echo "Access App via: http://${env.ALB_DNS}"
            }
        }
    }

    post {
        success {
            echo 'Deployment completed successfully.'
        }
        failure {
            echo 'Deployment failed. Check logs for details.'
        }
    }
}
