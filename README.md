# generate-qr-code-api

This is a sample project that demonstrates how to build a very simple serverless application using AWS Lambda and API Gateway. The application generates a QR code image from text input and uploads it to an S3 bucket, returning a json object with a presigned URL for the uploaded image.

The project uses a github workflow to automatically build and deploy the application when changes are pushed to the main branch. The workflow is defined in the `.github/workflows/deploy.yml` file and uses the AWS SAM CLI to build and deploy the application.

The application code is located in the `generate_qr_code` directory and the handler is set to `app.lambda_handler`. The AWS SAM template is defined in the `template.yaml` file. The SAM template defines the Lambda function, its permissions, and the API Gateway endpoint.
