pipeline {
    agent any

    environment {
        AWS_REGION = 'eu-north-1'
        ECR_REGISTRY = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME = 'TravelEaseCluster'
        
        // These will be captured later from Terraform outputs
        S3_BUCKET_NAME = ''
        ALB_DNS_NAME = ''

        // Assuming prod.tfvars is in the project root (..\\)
        TF_VAR_FILE = 'prod.tfvars'
        
        // Define ALL services and their local Docker directory paths
        SERVICE_MAP = [
            'booking-service': 'Booking_Service',
            'flight-service': 'Flight_Service',
            'payment-service': 'Payment_Service',
            'crowdpulse-service': 'CrowdPulse/backend'
        ]
        
        // Hardcoded old URL placeholder found in index.html's JS
        OLD_ALB_URL_PLACEHOLDER = 'http://travelease-project-ALB-720876672.eu-north-1.elb.amazonaws.com'
        
        // Specific placeholder used in the widget file's JS 
        OLD_WIDGET_URL_PLACEHOLDER = 'http://travelease-ALB-721125848.eu-north-1.elb.amazonaws.com'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Cloning repository..."
                git branch: 'main', url: 'https://github.com/works-praneel/TravelEase_Internship.git'
            }
        }
        
        stage('AWS & ECR Login Setup') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'BNmnx0bIy24ahJTSUi6MIEpYUVmCTV8dyMBfH6cq',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    // Use bat for cross-platform execution (Windows/Linux)
                    bat """
                    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                    aws configure set region %AWS_REGION%
                    
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    """
                }
            }
        }
        
        stage('Terraform Provisioning') {
            steps {
                dir('terraform') { 
                    echo "Running terraform init..."
                    bat 'terraform init'
                    
                    echo "Running terraform plan..."
                    // Correctly references prod.tfvars from the project root
                    bat "terraform plan -var-file=..\\%TF_VAR_FILE% -out=tfplan"
                    
                    echo "Running terraform apply..."
                    bat 'terraform apply -auto-approve tfplan'
                }
            }
        }
        
        // --- STAGE 1: CAPTURE TERRAFORM OUTPUTS (FIXED) ---
        stage('Get Terraform Outputs') {
            steps {
                dir('terraform') {
                    script {
                        // Capture outputs directly into Groovy variables using sh/bat wrapper
                        def albDns = sh(script: 'terraform output -raw alb_dns_name', returnStdout: true).trim()
                        def s3Bucket = sh(script: 'terraform output -raw frontend_bucket_name', returnStdout: true).trim()
                        def frontUrl = sh(script: 'terraform output -raw frontend_website_url', returnStdout: true).trim()

                        // Set Jenkins environment variables
                        env.ALB_DNS_NAME   = albDns
                        env.S3_BUCKET_NAME = s3Bucket
                        env.FRONTEND_URL   = frontUrl
                        
                        // Validation (this prevents the null check failure in later stages)
                        if (!env.ALB_DNS_NAME || !env.S3_BUCKET_NAME || !env.FRONTEND_URL) {
                            error("""
                            ❌ Terraform outputs missing or invalid. Check 'outputs.tf' and state file.
                            Captured: ALB_DNS_NAME=${env.ALB_DNS_NAME}
                            """.stripIndent())
                        }
                        
                        echo "Captured ALB DNS: ${env.ALB_DNS_NAME}"
                        echo "Captured S3 Bucket: ${env.S3_BUCKET_NAME}"
                    }
                }
            }
        }

        stage('Build, Tag, and Push Images') {
            steps {
                script {
                    env.SERVICE_MAP.each { serviceName, serviceDirectory ->
                        
                        echo "Building and pushing image for service: ${serviceName}"

                        dir("${serviceDirectory}") { 
                            // Build the Docker image in the specific service directory
                            bat "docker build -t ${serviceName} ."
                        }
                        
                        // Tag the image
                        bat "docker tag ${serviceName}:latest %ECR_REGISTRY%/${serviceName}:latest"
                        
                        // Push the image to ECR
                        bat "docker push %ECR_REGISTRY%/${serviceName}:latest"
                    }
                }
            }
        }
        
        // --- STAGE 2: PREPARE AND DEPLOY FRONTEND (URL INJECTION) ---
        stage('Prepare & Deploy Frontend') {
            steps {
                echo "1. Replacing API URLs in frontend files..."
                script {
                    def newAlbUrl = "http://${env.ALB_DNS_NAME}"
                    
                    // a) Update index.html: Replace the old hardcoded ALB URL placeholder in the JS block.
                    bat "powershell -Command \"(Get-Content index.html) -replace '${env.OLD_ALB_URL_PLACEHOLDER}', '${newAlbUrl}' | Set-Content index.html\""
                    
                    // b) Update CrowdPulse Widget: Replace the hardcoded API_URL inside crowdpulse_widget.html.
                    bat "powershell -Command \"(Get-Content CrowdPulse\\frontend\\crowdpulse_widget.html) -replace '${env.OLD_WIDGET_URL_PLACEHOLDER}', '${newAlbUrl}' | Set-Content CrowdPulse\\frontend\\crowdpulse_widget.html\""
                }

                echo "2. Uploading processed files to S3 bucket: ${S3_BUCKET_NAME}"
                
                // Using AWS CLI to upload the core files to the dynamic S3 bucket.
                bat """
                aws s3 cp index.html s3://%S3_BUCKET_NAME%/index.html --content-type "text/html"
                aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html --content-type "text/html"
                aws s3 cp images\\travelease_logo.png s3://%S3_BUCKET_NAME%/images/travelease_logo.png --content-type "image/png"
                """
                echo "S3 Upload Complete. Frontend changes are live."
            }
        }
        
        stage('Deploy to Fargate') {
            steps {
                script {
                    env.SERVICE_MAP.keySet().each { serviceName ->
                        echo "Deploying service: ${serviceName} to Fargate..."
                        // Force ECS to pull the latest image and restart the task
                        bat "aws ecs update-service --cluster ${CLUSTER_NAME} --service ${serviceName} --force-new-deployment"
                    }
                }
            }
        }
        
        // --- FINAL STAGE: OUTPUT FRONTEND URL ---
        stage('Display Outputs') {
            steps {
                dir('terraform') {
                    // Get the final S3 website endpoint URL (frontend_website_url output must exist)
                    // The FRONTEND_URL variable already holds this value from the Get Terraform Outputs stage.
                    bat 'echo FINAL WEBSITE URL: %FRONTEND_URL%'
                }
                
                // Display ALB DNS explicitly
                bat 'echo ALB DNS (Backend API): http://%ALB_DNS_NAME%'
            }
        }
    }
}