pipeline {
    agent any

    // Poll every 2 minutes for GitHub changes
    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        AWS_REGION       = 'eu-north-1'
        ECR_REGISTRY     = '904233121598.dkr.ecr.eu-north-1.amazonaws.com'
        CLUSTER_NAME     = 'TravelEaseCluster'

        // Terraform & output variables
        TF_VAR_FILE      = 'prod.tfvars'
        ALB_DNS_NAME     = ''
        S3_BUCKET_NAME   = ''
        FRONTEND_URL     = ''
        NEW_ALB_URL      = ''

        // Service build mapping (single-line JSON)
        SERVICE_MAP_JSON = '{"booking-service": "Booking_Service", "flight-service": "Flight_Service", "payment-service": "Payment_Service", "crowdpulse-service": "CrowdPulse/backend"}'

        // Old URL placeholders for frontend replacement
        OLD_ALB_URL_PLACEHOLDER     = 'http://travelease-project-ALB-720876672.eu-north-1.elb.amazonaws.com'
        OLD_WIDGET_URL_PLACEHOLDER  = 'http://travelease-ALB-721125848.eu-north-1.elb.amazonaws.com'
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
        stage('AWS & ECR Login Setup') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'BNmnx0bIy24ahJTSUi6MIEpYUVmCTV8dyMBfH6cq',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    bat """
                    echo Configuring AWS CLI...
                    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
                    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
                    aws configure set region %AWS_REGION%
                    echo Logging into ECR...
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                    """
                }
            }
        }

        // ------------------- TERRAFORM -------------------
        stage('Apply Infrastructure (Terraform)') {
            steps {
                script {
                    dir('D:/Minor/TravelEase/terraform') {
                        echo 'Running Terraform init, plan, and apply...'
                        bat """
                        terraform init -no-color
                        terraform plan -no-color -var-file=../%TF_VAR_FILE% -out=tfplan
                        terraform apply -no-color -auto-approve tfplan

                        echo Capturing Terraform outputs...
                        terraform output -json > tf_outputs.json
                        """
                    }

                    // Parse JSON outputs directly
                    def jsonText = readFile('D:/Minor/TravelEase/terraform/tf_outputs.json')
                    def tf = new groovy.json.JsonSlurper().parseText(jsonText)

                    env.ALB_DNS_NAME   = tf.alb_dns_name?.value ?: tf.load_balancer_dns?.value ?: ''
                    env.S3_BUCKET_NAME = tf.frontend_bucket_name?.value ?: ''
                    env.FRONTEND_URL   = tf.frontend_website_url?.value ?: ''

                    if (!env.ALB_DNS_NAME || !env.S3_BUCKET_NAME || !env.FRONTEND_URL) {
                        error("""
                        ❌ Terraform outputs missing or invalid.
                        Captured:
                          ALB_DNS_NAME   = ${env.ALB_DNS_NAME}
                          S3_BUCKET_NAME = ${env.S3_BUCKET_NAME}
                          FRONTEND_URL   = ${env.FRONTEND_URL}
                        Check:
                          • Terraform outputs in D:/Minor/TravelEase/terraform/outputs.tf
                          • State file has values for alb_dns_name, frontend_bucket_name, frontend_website_url
                        """.stripIndent())
                    }

                    env.NEW_ALB_URL = "http://${env.ALB_DNS_NAME}"

                    echo "✅ ALB DNS: ${env.ALB_DNS_NAME}"
                    echo "✅ S3 Bucket: ${env.S3_BUCKET_NAME}"
                    echo "✅ Frontend URL: ${env.FRONTEND_URL}"
                }
            }
        }

        // ------------------- DOCKER BUILD & PUSH -------------------
        stage('Build, Tag, and Push Images') {
            steps {
                script {
                    def services = new groovy.json.JsonSlurper().parseText(env.SERVICE_MAP_JSON)
                    services.each { name, dirPath ->
                        echo "Building and pushing image for ${name}"
                        dir("${dirPath}") {
                            bat "docker build -t ${name} ."
                        }
                        bat """
                        docker tag ${name}:latest %ECR_REGISTRY%/${name}:latest
                        docker push %ECR_REGISTRY%/${name}:latest
                        """
                    }
                }
            }
        }

        // ------------------- FRONTEND UPDATE & DEPLOY -------------------
        stage('Prepare & Deploy Frontend') {
            steps {
                script {
                    echo "Updating frontend files with ALB: ${env.NEW_ALB_URL}"

                    // Replace URLs in index.html and widget
                    bat "powershell -Command \"(Get-Content index.html) -replace '${env.OLD_ALB_URL_PLACEHOLDER}', '${env.NEW_ALB_URL}' | Set-Content index.html\""
                    bat "powershell -Command \"(Get-Content CrowdPulse\\frontend\\crowdpulse_widget.html) -replace '${env.OLD_WIDGET_URL_PLACEHOLDER}', '${env.NEW_ALB_URL}' | Set-Content CrowdPulse\\frontend\\crowdpulse_widget.html\""

                    echo "Uploading files to S3: ${env.S3_BUCKET_NAME}"
                    bat """
                    aws s3 cp index.html s3://%S3_BUCKET_NAME%/index.html --content-type "text/html"
                    aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://%S3_BUCKET_NAME%/CrowdPulse/frontend/crowdpulse_widget.html --content-type "text/html"
                    aws s3 cp images\\travelease_logo.png s3://%S3_BUCKET_NAME%/images/travelease_logo.png --content-type "image/png"
                    """
                }
            }
        }

        // ------------------- ECS DEPLOYMENT -------------------
        stage('Deploy to Fargate') {
            steps {
                script {
                    def services = ['flight-service', 'booking-service', 'payment-service', 'crowdpulse-service']
                    services.each { svc ->
                        echo "Forcing ECS redeployment for: ${svc}"
                        bat "aws ecs update-service --cluster %CLUSTER_NAME% --service ${svc} --force-new-deployment"
                    }
                }
            }
        }

        // ------------------- DISPLAY OUTPUTS -------------------
        stage('Display Outputs') {
            steps {
                script {
                    echo '--------------------------------------------'
                    echo '✅ TravelEase Deployment Complete'
                    echo "Backend ALB DNS       : ${env.ALB_DNS_NAME}"
                    echo "Frontend S3 Bucket    : ${env.S3_BUCKET_NAME}"
                    echo "Frontend Website URL  : ${env.FRONTEND_URL}"
                    echo "Frontend uses backend : ${env.NEW_ALB_URL}"
                    echo '--------------------------------------------'
                }
            }
        }
    }
}
