pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        REPO_DIR = 'works-praneel/travelease_project/TravelEase_Project-239fa85907536e1e224456f82c849cd92624898e'
        ALB_DNS = ''
        S3_BUCKET_NAME = ''
        NEW_ALB_URL = ''
    }

    triggers {
        pollSCM('H/5 * * * *') // check for repo changes every 5 min
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Cloning repository..."
                git branch: 'main', url: 'https://github.com/works-praneel/TravelEase_Internship.git'
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
                    echo Configuring AWS CLI and logging into ECR...
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
                script {
                    dir("${REPO_DIR}/terraform") {
                        bat 'terraform init'
                        bat 'terraform plan'
                        bat 'terraform apply -auto-approve'

                        env.ALB_DNS = bat(returnStdout: true, script: 'terraform output -raw load_balancer_dns').trim()
                        env.S3_BUCKET_NAME = bat(returnStdout: true, script: 'terraform output -raw frontend_bucket_name').trim()
                        env.NEW_ALB_URL = "http://${ALB_DNS}"

                        echo "Captured ALB DNS: ${ALB_DNS}"
                        echo "Captured S3 Bucket: ${S3_BUCKET_NAME}"
                    }
                }
            }
        }

        stage('Update Frontend & Deploy via Script') {
            steps {
                script {
                    echo "Running Python script to update frontend URLs and deploy to S3..."
                    bat "python ${REPO_DIR}\\update_frontend_and_deploy.py ${NEW_ALB_URL} ${S3_BUCKET_NAME} ${REPO_DIR}"
                }
            }
        }

        stage('Build, Tag, and Push Images') {
            steps {
                script {
                    def services = [
                        'flight-service': 'Flight_Service',
                        'booking-service': 'Booking_Service',
                        'payment-service': 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse\\backend'
                    ]

                    dir("${REPO_DIR}") {
                        services.each { serviceName, serviceDirectory ->
                            echo "Building and pushing image for ${serviceName}..."
                            bat "docker build -t ${serviceName} .\\${serviceDirectory}"
                            bat "docker tag ${serviceName}:latest ${ECR_REGISTRY}/${serviceName}:latest"
                            bat "docker push ${ECR_REGISTRY}/${serviceName}:latest"
                        }
                    }
                }
            }
        }

        stage('Deploy to Fargate') {
            steps {
                script {
                    def services = ['flight-service', 'booking-service', 'payment-service', 'crowdpulse-service']
                    services.each { serviceName ->
                        bat "aws ecs update-service --cluster ${CLUSTER_NAME} --service ${serviceName} --force-new-deployment --region ${AWS_REGION}"
                    }
                }
            }
        }

        stage('Display Outputs') {
            steps {
                script {
                    def s3WebsiteUrl = bat(returnStdout: true, script: """
                        cd ${REPO_DIR}\\terraform
                        terraform output -raw frontend_website_url
                    """).trim()

                    echo "✅ TravelEase Deployment Complete!"
                    echo "-------------------------------------"
                    echo "Backend ALB DNS: ${ALB_DNS}"
                    echo "Frontend S3 Bucket Name: ${S3_BUCKET_NAME}"
                    echo "Frontend Website URL: ${s3WebsiteUrl}"
                    echo "Frontend uses backend at: ${NEW_ALB_URL}"
                    echo "-------------------------------------"
                }
            }
        }
    }

    post {
        success {
            echo '✅ Deployment completed successfully.'
        }
        failure {
            echo '❌ Deployment failed. Check the logs for details.'
        }
    }
}