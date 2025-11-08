pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        TERRAFORM_DIR = 'terraform'
    }

    triggers {
        pollSCM('H/2 * * * *') // Poll GitHub every 2 minutes
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('AWS Login & ECR Auth') {
            steps {
                withAWS(region: "${AWS_REGION}", credentials: 'aws-jenkins-creds') {
                    bat '''
                    aws sts get-caller-identity
                    for /f "delims=" %%a in ('aws ecr get-login-password --region %AWS_REGION%') do docker login --username AWS --password %%a %ECR_REGISTRY%
                    '''
                }
            }
        }

        stage('Terraform Init & Apply') {
            steps {
                dir("${TERRAFORM_DIR}") {
                    bat '''
                    terraform init -input=false
                    terraform plan -out=tfplan -input=false
                    terraform apply -auto-approve tfplan
                    '''
                }
            }
        }

        stage('Fetch Terraform Outputs') {
            steps {
                script {
                    def outputs = bat(script: "cd ${TERRAFORM_DIR} && terraform output -json", returnStdout: true).trim()
                    def parsed = readJSON text: outputs
                    env.S3_BUCKET_NAME = parsed.s3_bucket_name.value
                    env.ALB_DNS_NAME = parsed.alb_dns_name.value
                    env.FRONTEND_URL = "http://${parsed.alb_dns_name.value}"
                }
            }
        }

        stage('Update Frontend URL in index.html') {
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
                        docker build -t %ECR_REGISTRY%/${img.toLowerCase()}:latest ${img}
                        docker push %ECR_REGISTRY%/${img.toLowerCase()}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to ECS Fargate') {
            steps {
                bat '''
                aws ecs update-service --cluster %CLUSTER_NAME% --service TravelEaseService --force-new-deployment --region %AWS_REGION%
                '''
            }
        }

        stage('Deploy Frontend to S3') {
            steps {
                bat '''
                aws s3 sync . s3://%S3_BUCKET_NAME% --delete
                '''
            }
        }

        stage('Populate Databases') {
            steps {
                bat '''
                python populate_smart_trips_db.py
                python Flight_Service\\populate_flights_db.py
                '''
            }
        }

        stage('Display Outputs') {
            steps {
                echo "ALB URL: ${env.FRONTEND_URL}"
                echo "Frontend Bucket: ${env.S3_BUCKET_NAME}"
                echo "ECS Cluster: ${env.CLUSTER_NAME}"
            }
        }
    }

    post {
        success {
            echo 'Deployment successful.'
        }
        failure {
            echo 'Deployment failed. Check logs.'
        }
    }
}
