
---

### `template.yaml`
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Hospital Backend (SAM) - Cognito, HTTP API, Lambda, DynamoDB, S3 Dashboard

Parameters:
  DashboardOrigin:
    Type: String
    Default: "*"
    Description: Allowed CORS origin for HTTP API and response headers, e.g., https://your-bucket.s3-website-<region>.amazonaws.com or http://localhost:8000
  DashboardPublicRead:
    Type: String
    AllowedValues: ["true","false"]
    Default: "true"
    Description: Whether to allow public read for the S3 website bucket
  ProjectName:
    Type: String
    Default: hospital-backend-sam
  EnvironmentName:
    Type: String
    Default: dev

Globals:
  Function:
    Runtime: python3.11
    Timeout: 10
    MemorySize: 256
    Handler: app.lambda_handler
    CodeUri: src
    Environment:
      Variables:
        DYNAMODB_TABLE: !Ref PatientRecordsTable
        ALLOWED_ORIGIN: !Ref DashboardOrigin

Resources:
  PatientRecordsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub ${ProjectName}-${EnvironmentName}-PatientRecords
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: patient_id
          AttributeType: S
      KeySchema:
        - AttributeName: patient_id
          KeyType: HASH
      SSESpecification:
        SSEEnabled: true

  CognitoUserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: !Sub ${ProjectName}-${EnvironmentName}-user-pool
      AutoVerifiedAttributes: ["email"]
      UsernameAttributes: ["email"]
      Schema:
        - Name: email
          Required: true
          Mutable: true

  CognitoUserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref CognitoUserPool
      ClientName: !Sub ${ProjectName}-${EnvironmentName}-client
      GenerateSecret: false
      ExplicitAuthFlows:
        - ALLOW_USER_SRP_AUTH
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
      SupportedIdentityProviders:
        - COGNITO
      PreventUserExistenceErrors: ENABLED
      RefreshTokenValidity: 30
      AccessTokenValidity: 1
      IdTokenValidity: 1
      TokenValidityUnits:
        AccessToken: hours
        IdToken: hours
        RefreshToken: days
      CallbackURLs:
        - "http://localhost:8000"
      LogoutURLs:
        - "http://localhost:8000"

  CognitoPatientsGroup:
    Type: AWS::Cognito::UserPoolGroup
    Properties:
      GroupName: Patients
      UserPoolId: !Ref CognitoUserPool
      Description: Default patients group

  CognitoAdminGroup:
    Type: AWS::Cognito::UserPoolGroup
    Properties:
      GroupName: Admin
      UserPoolId: !Ref CognitoUserPool
      Description: Admin group with dashboard access

  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      CorsConfiguration:
        AllowHeaders: ["*"]
        AllowMethods: ["GET","OPTIONS"]
        AllowOrigins: [!Ref DashboardOrigin]
      Auth:
        Authorizers:
          CognitoJwtAuthorizer:
            JwtConfiguration:
              issuer: !Sub https://cognito-idp.${AWS::Region}.amazonaws.com/${CognitoUserPool}
              audience:
                - !Ref CognitoUserPoolClient
            IdentitySource: "$request.header.Authorization"

  HealthFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/health.lambda_handler
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /health
            Method: GET

  GetPatientMeFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/patient_me.lambda_handler
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref PatientRecordsTable
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /patient/me
            Method: GET
            Auth:
              Authorizer: CognitoJwtAuthorizer

  GetAdminMetricsOverviewFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/admin_overview.lambda_handler
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref PatientRecordsTable
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /admin/metrics/overview
            Method: GET
            Auth:
              Authorizer: CognitoJwtAuthorizer

  GetAdminMetricsDiseasesFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/admin_diseases.lambda_handler
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref PatientRecordsTable
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /admin/metrics/diseases
            Method: GET
            Auth:
              Authorizer: CognitoJwtAuthorizer

  GetAdminMetricsMedicationsFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/admin_medications.lambda_handler
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref PatientRecordsTable
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /admin/metrics/medications
            Method: GET
            Auth:
              Authorizer: CognitoJwtAuthorizer

  DashboardBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub ${ProjectName}-${EnvironmentName}-dashboard-${AWS::AccountId}-${AWS::Region}
      WebsiteConfiguration:
        IndexDocument: index.html
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete

  DashboardBucketPublicPolicy:
    Type: AWS::S3::BucketPolicy
    Condition: IsPublicDashboard
    Properties:
      Bucket: !Ref DashboardBucket
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Sid: AllowPublicRead
            Effect: Allow
            Principal: "*"
            Action: "s3:GetObject"
            Resource: !Sub ${DashboardBucket.Arn}/*

Conditions:
  IsPublicDashboard: !Equals [!Ref DashboardPublicRead, "true"]

Outputs:
  HttpApiUrl:
    Description: HTTP API endpoint base URL
    Value: !Sub https://${HttpApi}.execute-api.${AWS::Region}.amazonaws.com
  UserPoolId:
    Description: Cognito User Pool Id
    Value: !Ref CognitoUserPool
  UserPoolClientId:
    Description: Cognito User Pool Client Id
    Value: !Ref CognitoUserPoolClient
  DashboardUrl:
    Description: S3 static website URL
    Value: !GetAtt DashboardBucket.WebsiteURL
  TableName:
    Description: DynamoDB table name
    Value: !Ref PatientRecordsTable
