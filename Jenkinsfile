pipeline {
    agent any

    environment {
        // AWS configuration
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        
        // Variables to store dynamic Terraform outputs
        ALB_DNS = ''
        S3_BUCKET_NAME = ''
        
        // The base directory structure in your repository
        REPO_DIR = 'works-praneel/travelease_project/TravelEase_Project-239fa85907536e1e224456f82c849cd92624898e'
        
        // The full URL that will be injected into index.html
        NEW_ALB_URL = '' 
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
                // IMPORTANT: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY variables 
                // must be used with %VARIABLE_NAME% syntax inside bat for Windows
                withCredentials([usernamePassword(
                    credentialsId: 'BNmnx0bIy24ahJTSUi6MIEpYUVmCTV8dyMBfH6cq',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    bat """
                    echo Configuring AWS CLI and logging into ECR...
                    
                    // Configure AWS CLI
                    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                    aws configure set region %AWS_REGION%
                    
                    // ECR Login (pipes work in bat)
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    """
                }
            }
        }
        
        // --- 1. Terraform Init, Plan, Apply, and Output Capture ---
        stage('Apply Infrastructure (Terraform)') {
            steps {
                script {
                    dir("${REPO_DIR}/terraform") {
                        echo "Running Terraform init, plan, and apply..."
                        bat 'terraform init'
                        bat 'terraform plan'
                        bat 'terraform apply -auto-approve'
                        
                        // Capture the outputs (Groovy function call is the same for bat/sh)
                        env.ALB_DNS = bat(returnStdout: true, script: 'terraform output -raw load_balancer_dns').trim()
                        env.S3_BUCKET_NAME = bat(returnStdout: true, script: 'terraform output -raw frontend_bucket_name').trim()
                        
                        env.NEW_ALB_URL = "http://${ALB_DNS}"

                        echo "Captured ALB DNS: ${ALB_DNS}"
                        echo "Captured S3 Bucket: ${S3_BUCKET_NAME}"
                    }
                }
            }
        }
        
        // --- 2. Update index.html with new ALB DNS ---
        stage('Update Frontend ALB URL') {
            steps {
                script {
                    def indexPath = "${REPO_DIR}/index.html"
                    
                    echo "Reading and updating index.html with new ALB URL: ${NEW_ALB_URL}"
                    def content = readFile(indexPath)

                    // Replace the old hardcoded ALB URL with the new one dynamically in two places.
                    // Using replaceAll with regex to ensure the new URL is injected correctly.
                    content = content.replaceAll(/(const ALB_URL = ")(\S+)(")/, "\$1${NEW_ALB_URL}\$3")
                    content = content.replaceAll(/(const API_ENDPOINT = ")(\S+)(")/, "\$1${NEW_ALB_URL}\$3")

                    writeFile(file: indexPath, text: content)
                    echo "Successfully updated ALB URLs in index.html for deployment."
                }
            }
        }
        
        // --- 3. Build, Tag, and Push Images (All 4 services) ---
        stage('Build, Tag, and Push Images') {
            steps {
                script {
                    // Map service name to its Dockerfile context directory.
                    def services = [
                        'flight-service': 'Flight_Service',
                        'booking-service': 'Booking_Service',
                        'payment-service': 'Payment_Service',
                        'crowdpulse-service': 'CrowdPulse\\backend' // Use \\ for Windows path separator
                    ]
                    
                    dir("${REPO_DIR}") { 
                        services.each { serviceName, serviceDirectory ->
                            echo "Building and pushing image for service: ${serviceName} from .\\${serviceDirectory}"
                            
                            // Docker build command using bat. Use backslashes (\) for Windows paths
                            bat "docker build -t ${serviceName} .\\${serviceDirectory}"
                            bat "docker tag ${serviceName}:latest ${ECR_REGISTRY}/${serviceName}:latest"
                            bat "docker push ${ECR_REGISTRY}/${serviceName}:latest"
                        }
                    }
                }
            }
        }
        
        // --- 4. Deploy to Fargate (Force new deployment for all 4 services) ---
        stage('Deploy to Fargate') {
            steps {
                script {
                    // List all services, including the new one
                    def services = ['flight-service', 'booking-service', 'payment-service', 'crowdpulse-service']
                    
                    services.each { serviceName ->
                        echo "Force deploying service: ${serviceName} to cluster ${CLUSTER_NAME}..."
                        // AWS CLI command using bat
                        bat "aws ecs update-service --cluster ${CLUSTER_NAME} --service ${serviceName} --force-new-deployment"
                    }
                }
            }
        }
        
        // --- 5. Deploy Frontend Files to S3 ---
        stage('Deploy Frontend (S3)') {
            steps {
                // Use Groovy interpolation (${VARIABLE}) inside bat command for dynamic paths/bucket
                bat """
                echo Deploying updated index.html to s3://${S3_BUCKET_NAME}...
                aws s3 cp ${REPO_DIR}\\index.html s3://${S3_BUCKET_NAME}/index.html --content-type text/html --acl public-read
                
                echo Deploying crowdpulse_widget.html...
                aws s3 cp ${REPO_DIR}\\CrowdPulse\\frontend\\crowdpulse_widget.html s3://${S3_BUCKET_NAME}/crowdpulse_widget.html --content-type text/html --acl public-read
                
                echo Deploying travelease_logo.png...
                aws s3 cp ${REPO_DIR}\\images\\travelease_logo.png s3://${S3_BUCKET_NAME}/images/travelease_logo.png --content-type image/png --acl public-read
                """
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
                    echo "NOTE: The frontend is configured to use the new backend URL: ${NEW_ALB_URL}"
                    echo "-------------------------------------"
                }
            }
        }
    }
}