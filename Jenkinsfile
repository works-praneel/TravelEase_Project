pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        ALB_DNS = ''
        S3_BUCKET_NAME = ''
        NEW_ALB_URL = ''
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Cloning repository..."
                git branch: 'main', url: 'https://github.com/works-praneel/TravelEase_Project.git'
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
                script {
                    dir('terraform') {
                        bat 'dir'   // Show contents
                        bat 'terraform init'
                        bat 'terraform plan'
                        bat 'terraform apply -auto-approve'

                        env.ALB_DNS = bat(returnStdout: true, script: 'terraform output -raw load_balancer_dns').trim()
                        env.S3_BUCKET_NAME = bat(returnStdout: true, script: 'terraform output -raw frontend_bucket_name').trim()
                        env.NEW_ALB_URL = "http://${env.ALB_DNS}"

                        echo "✅ Captured ALB DNS: ${env.ALB_DNS}"
                        echo "✅ Captured S3 Bucket: ${env.S3_BUCKET_NAME}"
                        echo "✅ Constructed ALB URL: ${env.NEW_ALB_URL}"
                    }
                }
            }
        }

        stage('Update Frontend & Deploy via Script') {
            steps {
                script {
                    echo "🚀 Preparing to update frontend URLs and deploy to S3..."
                    echo "🔹 ALB DNS: ${env.ALB_DNS}"
                    echo "🔹 S3 Bucket: ${env.S3_BUCKET_NAME}"
                    echo "🔹 NEW ALB URL: ${env.NEW_ALB_URL}"

                    bat """
                    echo Running Python script using full path...
                    "C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" update_frontend_and_deploy.py ${env.NEW_ALB_URL} ${env.S3_BUCKET_NAME} .
                    """
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

                    services.each { serviceName, serviceDirectory ->
                        echo "Building and pushing image for ${serviceName}..."
                        bat "docker build -t ${serviceName} .\\${serviceDirectory}"
                        bat "docker tag ${serviceName}:latest ${env.ECR_REGISTRY}/${serviceName}:latest"
                        bat "docker push ${env.ECR_REGISTRY}/${serviceName}:latest"
                    }
                }
            }
        }

        stage('Deploy to Fargate') {
            steps {
                script {
                    def services = ['flight-service', 'booking-service', 'payment-service', 'crowdpulse-service']
                    services.each { serviceName ->
                        bat "aws ecs update-service --cluster ${env.CLUSTER_NAME} --service ${serviceName} --force-new-deployment --region ${env.AWS_REGION}"
                    }
                }
            }
        }

        stage('Display Outputs') {
            steps {
                script {
                    def s3WebsiteUrl = bat(returnStdout: true, script: """
                        cd terraform
                        terraform output -raw frontend_website_url
                    """).trim()

                    echo "✅ TravelEase Deployment Complete!"
                    echo "-------------------------------------"
                    echo "Backend ALB DNS: ${env.ALB_DNS}"
                    echo "Frontend S3 Bucket Name: ${env.S3_BUCKET_NAME}"
                    echo "Frontend Website URL: ${s3WebsiteUrl}"
                    echo "Frontend uses backend at: ${env.NEW_ALB_URL}"
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