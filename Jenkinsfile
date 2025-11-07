pipeline {
    agent any

    // Poll GitHub every 2 minutes
    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        AWS_REGION     = 'eu-north-1'
        ECR_REGISTRY   = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME   = 'TravelEaseCluster'

        ALB_DNS        = ''
        S3_BUCKET_NAME = ''
        FRONTEND_URL   = ''
        NEW_ALB_URL    = ''
        REPO_DIR       = '.'
    }

    stages {

        // ------------------- CHECKOUT -------------------
        stage('Checkout') {
            steps {
                echo 'Cloning repository...'
                git branch: 'main', url: 'https://github.com/works-praneel/TravelEase_Project.git'
            }
        }

        // ------------------- AWS LOGIN -------------------
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

        // ------------------- TERRAFORM -------------------
        stage('Apply Infrastructure (Terraform)') {
            steps {
                script {
                    dir('D:/Minor/TravelEase/terraform') {
                        echo 'Running Terraform init, plan, and apply...'
                        bat '''
                        terraform init -no-color
                        terraform plan -no-color -out=tfplan
                        terraform apply -no-color -auto-approve tfplan
                        '''

                        // Capture Terraform outputs safely
                        def rawAlbDns      = bat(returnStdout: true, script: 'terraform output -raw load_balancer_dns 2>NUL').trim()
                        def rawS3Bucket    = bat(returnStdout: true, script: 'terraform output -raw frontend_bucket_name 2>NUL').trim()
                        def rawFrontendUrl = bat(returnStdout: true, script: 'terraform output -raw frontend_website_url 2>NUL').trim()

                        env.ALB_DNS        = rawAlbDns      ? rawAlbDns.replaceAll('"', '')      : ''
                        env.S3_BUCKET_NAME = rawS3Bucket    ? rawS3Bucket.replaceAll('"', '')    : ''
                        env.FRONTEND_URL   = rawFrontendUrl ? rawFrontendUrl.replaceAll('"', '') : ''

                        if (!env.ALB_DNS || !env.S3_BUCKET_NAME || !env.FRONTEND_URL) {
                            error("""
                            ❌ Terraform output capture failed.
                            ALB_DNS        = '${env.ALB_DNS}'
                            S3_BUCKET_NAME = '${env.S3_BUCKET_NAME}'
                            FRONTEND_URL   = '${env.FRONTEND_URL}'
                            Check:
                              1. Jenkins AWS credentials are valid.
                              2. 'terraform output' returns valid results.
                              3. Correct directory path: D:/Minor/TravelEase/terraform
                            """.stripIndent())
                        }

                        env.NEW_ALB_URL = "http://${env.ALB_DNS}"

                        echo "✅ Captured ALB DNS       : ${env.ALB_DNS}"
                        echo "✅ Captured S3 Bucket     : ${env.S3_BUCKET_NAME}"
                        echo "✅ Captured Frontend URL  : ${env.FRONTEND_URL}"
                    }
                }
            }
        }

        // ------------------- FRONTEND UPDATE -------------------
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

        // ------------------- DOCKER BUILD & PUSH -------------------
        stage('Build, Tag, and Push Images') {
            steps {
                script {
                    def services = [
                        'flight-service'     : 'Flight_Service',
                        'booking-service'    : 'Booking_Service',
                        'payment-service'    : 'Payment_Service',
                        'crowdpulse-service' : 'CrowdPulse\\backend'
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

        // ------------------- DEPLOY TO FARGATE -------------------
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

        // ------------------- DEPLOY FRONTEND -------------------
        stage('Deploy Frontend (S3)') {
            steps {
                script {
                    echo "Using S3 bucket: ${env.S3_BUCKET_NAME}"
                    if (!env.S3_BUCKET_NAME?.trim()) {
                        error("S3_BUCKET_NAME is empty! Terraform output not captured.")
                    }

                    bat """
                    echo Deploying frontend assets to s3://%S3_BUCKET_NAME% ...
                    aws s3 cp index.html s3://%S3_BUCKET_NAME%/index.html --content-type text/html --acl public-read
                    aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/crowdpulse_widget.html --content-type text/html --acl public-read
                    aws s3 cp images\\travelease_logo.png s3://%S3_BUCKET_NAME%/images/travelease_logo.png --content-type image/png --acl public-read
                    """
                }
            }
        }

        // ------------------- DISPLAY OUTPUTS -------------------
        stage('Display Outputs') {
            steps {
                script {
                    echo '--------------------------------------------'
                    echo '✅ TravelEase Deployment Complete'
                    echo "Backend ALB DNS       : ${env.ALB_DNS}"
                    echo "Frontend S3 Bucket    : ${env.S3_BUCKET_NAME}"
                    echo "Frontend Website URL  : ${env.FRONTEND_URL}"
                    echo "Frontend uses backend : ${env.NEW_ALB_URL}"
                    echo '--------------------------------------------'
                }
            }
        }
    }
}
