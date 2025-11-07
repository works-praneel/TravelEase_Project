pipeline {
    agent any

    environment {
        // AWS configuration
        AWS_REGION     = 'eu-north-1'
        ECR_REGISTRY   = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME   = 'TravelEaseCluster'

        // Terraform outputs (set dynamically)
        ALB_DNS        = ''
        S3_BUCKET_NAME = ''
        NEW_ALB_URL    = ''

        // Repo workspace root
        REPO_DIR       = '.'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Cloning repository...'
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
                    bat '''
                    echo Configuring AWS CLI and logging into ECR...
                    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                    aws configure set region %AWS_REGION%
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    '''
                }
            }
        }

        // --- Terraform Infrastructure Stage ---
        stage('Apply Infrastructure (Terraform)') {
            steps {
                script {
                    // Use absolute local Terraform directory
                    dir('D:/Minor/TravelEase/terraform') {
                        echo 'Running Terraform init, plan, and apply...'
                        bat '''
                        terraform init
                        terraform plan -out=tfplan
                        terraform apply -auto-approve tfplan
                        '''
                        env.ALB_DNS        = bat(returnStdout: true, script: 'terraform output -raw load_balancer_dns').trim()
                        env.S3_BUCKET_NAME = bat(returnStdout: true, script: 'terraform output -raw frontend_bucket_name').trim()
                        env.NEW_ALB_URL    = "http://${env.ALB_DNS}"

                        echo "Captured ALB DNS: ${env.ALB_DNS}"
                        echo "Captured S3 Bucket: ${env.S3_BUCKET_NAME}"
                    }
                }
            }
        }

        // --- Update Frontend with ALB URL ---
        stage('Update Frontend ALB URL') {
            steps {
                script {
                    def indexPath = "${REPO_DIR}/index.html"
                    echo "Updating index.html with new ALB URL: ${env.NEW_ALB_URL}"
                    def content = readFile(indexPath)
                    content = content.replaceAll(/(const ALB_URL = ")([^"]+)(")/, "\$1${env.NEW_ALB_URL}\$3")
                    content = content.replaceAll(/(const API_ENDPOINT = ")([^"]+)(")/, "\$1${env.NEW_ALB_URL}\$3")
                    writeFile(file: indexPath, text: content)
                    echo 'Frontend URLs updated successfully.'
                }
            }
        }

        // --- Docker Build, Tag, Push ---
        stage('Build, Tag, and Push Images') {
            steps {
                script {
                    def services = [
                        'flight-service'    : 'Flight_Service',
                        'booking-service'   : 'Booking_Service',
                        'payment-service'   : 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse\\backend'
                    ]
                    dir("${REPO_DIR}") {
                        services.each { name, path ->
                            echo "Building and pushing image for ${name}"
                            bat """
                            docker build -t ${name} .\\${path}
                            docker tag ${name}:latest %ECR_REGISTRY%/${name}:latest
                            docker push %ECR_REGISTRY%/${name}:latest
                            """
                        }
                    }
                }
            }
        }

        // --- Deploy Backend to ECS Fargate ---
        stage('Deploy to Fargate') {
            steps {
                script {
                    def services = ['flight-service', 'booking-service', 'payment-service', 'crowdpulse-service']
                    services.each { svc ->
                        echo "Forcing new deployment of ${svc}..."
                        bat "aws ecs update-service --cluster %CLUSTER_NAME% --service ${svc} --force-new-deployment"
                    }
                }
            }
        }

        // --- Deploy Frontend to S3 ---
        stage('Deploy Frontend (S3)') {
            steps {
                bat """
                echo Deploying frontend assets to s3://%S3_BUCKET_NAME% ...
                aws s3 cp index.html s3://%S3_BUCKET_NAME%/index.html --content-type text/html --acl public-read
                aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/crowdpulse_widget.html --content-type text/html --acl public-read
                aws s3 cp images\\travelease_logo.png s3://%S3_BUCKET_NAME%/images/travelease_logo.png --content-type image/png --acl public-read
                """
            }
        }

        // --- Display Outputs ---
        stage('Display Outputs') {
            steps {
                script {
                    def siteUrl = bat(returnStdout: true, script: 'cd D:/Minor/TravelEase/terraform && terraform output -raw frontend_website_url').trim()
                    echo '--------------------------------------------'
                    echo '✅ TravelEase Deployment Complete'
                    echo "Backend ALB DNS       : ${env.ALB_DNS}"
                    echo "Frontend S3 Bucket    : ${env.S3_BUCKET_NAME}"
                    echo "Frontend Website URL  : ${siteUrl}"
                    echo "Frontend uses backend : ${env.NEW_ALB_URL}"
                    echo '--------------------------------------------'
                }
            }
        }
    }
}
